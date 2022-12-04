import datetime
import asyncio
from fastapi import APIRouter, Form, BackgroundTasks
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
    distribution_config = cloudfront.get_distribution_config(Id=cloudfront_id).get('DistributionConfig')
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

        print(f"check ssl status... {status}")
        if status == "ISSUED":
            break
        await asyncio.sleep(10)
    update_cloudfront_aliases(cloudfront_id, domain_name, ssl_certification_arn)


@router.get('/custom_domains')
def get_custom_domains():
    distribution_list = cloudfront.list_distributions().get('DistributionList', {}).get("Items")
    cert_list = acm.list_certificates(CertificateStatuses=['PENDING_VALIDATION']).get('CertificateSummaryList')
    result = []
    for dist in distribution_list:
        if not dist.get('Aliases', {}).get('Quantity'):
            domain_name = dist.get("Comment")
            cert = list(filter(lambda x: x.get('DomainName') == domain_name, cert_list))
            if cert:
                certificate = \
                    acm.describe_certificate(CertificateArn=cert[0]["CertificateArn"]).get('Certificate', {}).get(
                        'DomainValidationOptions', [{}])[0].get(
                        'ResourceRecord', {})
                print(certificate)
                result.append(dict(domain_name=domain_name,
                                   cname_name=certificate['Name'],
                                   cname_value=certificate["Value"]
                                   ))
        else:
            result.extend([{"domain_name": domain} for domain in dist.get('Aliases', {}).get("Items")])
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
                if not dist.get('Aliases', {}).get('Quantity') and dist.get("Comment") == domain_name:
                    update_cloudfront_aliases(dist.get("Id"), domain_name, cert[0]["CertificateArn"])
            return {'is_issued': True, 'is_update_distribution_aliases': True}
        except Exception as e:
            return {'is_issued': True, 'is_update_distribution_aliases': False, "message": str(e)}
    else:
        return {"is_issued": False, 'is_update_distribution_aliases': False}


@router.post('/custom_domain')
async def add_custom_domain(background_tasks: BackgroundTasks, domain_name=Form(...)):
    # Create CloudFront distribution
    distribution_config = get_distribution_config(
        str(datetime.datetime.now()), "sp-custom-domain-bucket", settings.s3_bucket_domain_name, domain_name)
    new_cloudfront = cloudfront.create_distribution(DistributionConfig=distribution_config)
    cloudfront_id = new_cloudfront.get("Distribution", {}).get('Id')

    # Create ssl certification
    custom_domain_acm = acm.request_certificate(
        DomainName=domain_name,
        ValidationMethod="DNS",
    )



    # Get CNAME record value
    cert_value = acm.describe_certificate(CertificateArn=custom_domain_acm["CertificateArn"])
    resource_record = cert_value.get('Certificate', {}).get('DomainValidationOptions', [{}])[0].get('ResourceRecord')
    # Need to wait
    while not resource_record:
        cert_value = acm.describe_certificate(CertificateArn=custom_domain_acm["CertificateArn"])
        resource_record = cert_value.get('Certificate', {}).get('DomainValidationOptions', [{}])[0].get(
            'ResourceRecord', {})
        print('in loop')
        await asyncio.sleep(1)

    # Automatically add CNAME record if domain on liweicheng00.link
    if "liweicheng00.link" in domain_name:
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
    return resource_record
