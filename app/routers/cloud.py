import datetime
import asyncio
from fastapi import APIRouter, Form, HTTPException, BackgroundTasks
from boto3 import client
from app.config import settings

cloudfront = client('cloudfront')
acm = client('acm')
route53 = client('route53')

router = APIRouter(
    tags=["cloud"],
    responses={404: {"description": "Not found"}},
)


def get_distribution_config(caller_id: str, origin_name_id: str, s3_bucket_domain_name: str,
                            custom_domain: str) -> dict:
    return {
        'CallerReference': caller_id,
        'Comment': custom_domain,
        'DefaultRootObject': "index.html",
        'Origins': {
            'Quantity': 1,
            'Items': [
                {
                    'Id': origin_name_id,
                    'DomainName': s3_bucket_domain_name,
                    "S3OriginConfig": {"OriginAccessIdentity": ''}
                },
            ]
        },
        'DefaultCacheBehavior': {
            'TargetOriginId': origin_name_id,
            'ViewerProtocolPolicy': 'redirect-to-https',
            'Compress': True,
            'AllowedMethods': {
                'Quantity': 2,
                'Items': ['GET', 'HEAD'],
                'CachedMethods': {
                    'Quantity': 2,
                    'Items': ['GET', 'HEAD'],
                }
            },
            "ForwardedValues": {
                "Cookies": {'Forward': 'all'},
                "Headers": {"Quantity": 0},
                "QueryString": False,
                "QueryStringCacheKeys": {"Quantity": 0},
            },
            "MinTTL": 1000
        },
        'CustomErrorResponses': {
            'Quantity': 1,
            'Items': [
                {
                    'ErrorCode': 404,
                    'ResponsePagePath': '/index.html',
                    'ResponseCode': '200',
                },
            ]
        },
        'PriceClass': 'PriceClass_All',
        'Enabled': True,
        'Restrictions': {
            'GeoRestriction': {
                'RestrictionType': 'none',
                'Quantity': 0,
            }
        },
        'IsIPV6Enabled': True
    }


def update_cloudfront_aliases(cloudfront_id, custom_domain, ssl_certification_arn):
    distribution_config = cloudfront.get_distribution_config(Id=cloudfront_id)
    e_tag = distribution_config.get("ETag")
    distribution_config = distribution_config.get('DistributionConfig')
    if not distribution_config:
        raise
    distribution_config['Aliases'] = {
        'Quantity': 1,
        'Items': [
            custom_domain,
        ]
    }
    distribution_config['ViewerCertificate'] = {
        'CloudFrontDefaultCertificate': False,
        'ACMCertificateArn': ssl_certification_arn,
        'SSLSupportMethod': 'sni-only',
        'MinimumProtocolVersion': 'TLSv1.2_2021',
    }
    return cloudfront.update_distribution(
        Id=cloudfront_id,
        DistributionConfig=distribution_config,
        IfMatch=e_tag
    )


async def wait_for_update_cloudfront_aliases(cloudfront_id, domain_name, ssl_certification_arn):
    while True:
        cert = acm.describe_certificate(CertificateArn=ssl_certification_arn)
        status = cert.get('Certificate', {}).get('Status')

        if status == "ISSUED":
            break
        await asyncio.sleep(10)
    update_cloudfront_aliases(cloudfront_id, domain_name, ssl_certification_arn)


async def wait_for_delete_cloudfront_aliases(cloudfront_id, domain_name):
    while True:
        distribution = cloudfront.get_distribution(Id=cloudfront_id)
        dist = distribution.get('Distribution')
        status = dist.get("Status")
        if status == "Deployed":
            break
        await asyncio.sleep(10)
    cloudfront_domain_name = dist.get("DomainName")
    distribution_config = cloudfront.get_distribution_config(Id=cloudfront_id)
    e_tag = distribution_config.get("ETag")
    cloudfront.delete_distribution(Id=cloudfront_id, IfMatch=e_tag)

    cert_list = acm.list_certificates(
        CertificateStatuses=['ISSUED', 'PENDING_VALIDATION']).get('CertificateSummaryList')

    cert = list(filter(lambda x: x.get('DomainName') == domain_name, cert_list))
    if cert:
        if 'sp1.liweicheng00.link' in domain_name:
            cert_value = acm.describe_certificate(CertificateArn=cert[0]["CertificateArn"])
            resource_record = cert_value.get('Certificate', {}).get('DomainValidationOptions', [{}])[0].get(
                'ResourceRecord', {})
            delete_cname_record({"Name": domain_name, "Value": cloudfront_domain_name}, resource_record)
        acm.delete_certificate(CertificateArn=cert[0]["CertificateArn"])


def delete_cname_record(domain_name, resource_record):
    route53.change_resource_record_sets(
        HostedZoneId=settings.hosted_zone_id,
        ChangeBatch=dict(
            Changes=[
                dict(
                    Action="DELETE",
                    ResourceRecordSet=dict(
                        Name=resource_record['Name'],
                        Type="CNAME",
                        TTL=60,
                        ResourceRecords=[{"Value": resource_record["Value"]}]
                    )
                ),
                dict(
                    Action="CREATE",
                    ResourceRecordSet=dict(
                        Name=domain_name['Name'],
                        Type="CNAME",
                        TTL=60,
                        ResourceRecords=[{"Value": domain_name['Value']}]
                    )
                )
            ]
        )
    )


@router.get('/custom_domains')
def get_custom_domains():
    distribution_list = cloudfront.list_distributions().get('DistributionList', {}).get("Items")
    cert_list = acm.list_certificates(CertificateStatuses=['ISSUED', 'PENDING_VALIDATION']).get(
        'CertificateSummaryList')
    result = []
    for dist in distribution_list:
        domain_name = dist.get("Comment")
        if domain_name == "sp1.liweicheng00.link":
            continue

        if not dist.get('Aliases', {}).get('Quantity'):
            cert = list(filter(lambda x: x.get('DomainName') == domain_name, cert_list))
            if cert:
                certificate = acm.describe_certificate(CertificateArn=cert[0]["CertificateArn"]).get('Certificate', {})
                certificate_validation = certificate.get('DomainValidationOptions', [{}])[0].get('ResourceRecord', {})
                result.append(dict(domain_name=domain_name,
                                   cloudfront_domain=dist.get('DomainName'),
                                   status=certificate.get('Status', "Unknown"),
                                   cname_name=certificate_validation['Name'],
                                   cname_value=certificate_validation["Value"]
                                   ))
            else:
                result.extend(
                    [{"domain_name": domain_name, 'status': 'Unknown'}])
        else:
            result.extend(
                [{"domain_name": domain, 'status': dist.get("Status")} for domain in
                 dist.get('Aliases', {}).get("Items")])
    return result


@router.get('/custom_domain/{domain_name}')
def get_custom_domain_status(domain_name: str):
    cert_list = acm.list_certificates(
        CertificateStatuses=['ISSUED']).get('CertificateSummaryList')

    cert = list(filter(lambda x: x.get('DomainName') == domain_name, cert_list))
    if cert:
        try:
            distribution_list = cloudfront.list_distributions().get('DistributionList', {}).get("Items")
            for dist in distribution_list:
                if dist.get('Status') == "InProgress":
                    return {'is_issued': True, 'message': "Distribution in progress"}

                if not dist.get('Aliases', {}).get('Quantity') and dist.get("Comment") == domain_name:
                    update_cloudfront_aliases(dist.get("Id"), domain_name, cert[0]["CertificateArn"])
            return {'is_issued': True, 'is_updated_distribution_aliases': True}
        except Exception as e:
            return {'is_issued': True, 'is_updated_distribution_aliases': False, "message": str(e)}
    else:
        return {"is_issued": False, 'is_updated_distribution_aliases': False}


@router.post('/custom_domain')
async def add_custom_domain(domain_name=Form(...)):
    # Create ssl certification
    try:
        custom_domain_acm = acm.request_certificate(
            DomainName=domain_name,
            ValidationMethod="DNS",
        )
    except:
        raise HTTPException(400, 'Invalid URL.')

    # Create CloudFront distribution
    distribution_config = get_distribution_config(
        str(datetime.datetime.now()), "sp-custom-domain-bucket", settings.s3_bucket_domain_name, domain_name)
    new_cloudfront = cloudfront.create_distribution(DistributionConfig=distribution_config)

    # Get CNAME record value
    cert_value = acm.describe_certificate(CertificateArn=custom_domain_acm["CertificateArn"])
    resource_record = cert_value.get('Certificate', {}).get('DomainValidationOptions', [{}])[0].get('ResourceRecord')
    # Need to wait
    while not resource_record:
        cert_value = acm.describe_certificate(CertificateArn=custom_domain_acm["CertificateArn"])
        resource_record = cert_value.get('Certificate', {}).get('DomainValidationOptions', [{}])[0].get(
            'ResourceRecord', {})
        await asyncio.sleep(1)

    # Automatically add CNAME record if domain on liweicheng00.link
    if "sp1.liweicheng00.link" in domain_name:
        route53.change_resource_record_sets(
            HostedZoneId=settings.hosted_zone_id,
            ChangeBatch=dict(
                Changes=[
                    dict(
                        Action="CREATE",
                        ResourceRecordSet=dict(
                            Name=resource_record['Name'],
                            Type="CNAME",
                            TTL=60,
                            ResourceRecords=[{"Value": resource_record["Value"]}]
                        )
                    ),
                    dict(
                        Action="CREATE",
                        ResourceRecordSet=dict(
                            Name=domain_name,
                            Type="CNAME",
                            TTL=60,
                            ResourceRecords=[{"Value": new_cloudfront.get("Distribution", {}).get("DomainName")}]
                        )
                    )
                ]
            )
        )
        # Automatically set cloudfront aliases for *.sp1.liweicheng00.link
        await wait_for_update_cloudfront_aliases(new_cloudfront.get("Distribution", {}).get("Id"), domain_name,
                                                 custom_domain_acm["CertificateArn"])
    return resource_record


@router.delete('/custom_domain/{custom_domain}')
def delete_custom_domain(background_task: BackgroundTasks, custom_domain: str):
    distribution_list = cloudfront.list_distributions().get('DistributionList', {}).get("Items")

    for dist in distribution_list:
        domain_name = dist.get("Comment")
        if domain_name == custom_domain:
            status = dist.get("Status")
            if status == "InProgress":
                return "wait"
            cloudfront_id = dist.get('Id')
            distribution_config = cloudfront.get_distribution_config(Id=cloudfront_id)
            e_tag = distribution_config.get("ETag")
            distribution_config = distribution_config.get('DistributionConfig')
            if not distribution_config:
                raise
            if distribution_config["Enabled"]:
                distribution_config["Enabled"] = False
                cloudfront.update_distribution(
                    Id=cloudfront_id,
                    DistributionConfig=distribution_config,
                    IfMatch=e_tag
                )
            background_task.add_task(wait_for_delete_cloudfront_aliases,
                                     cloudfront_id=cloudfront_id,
                                     domain_name=domain_name)

    return "success"
