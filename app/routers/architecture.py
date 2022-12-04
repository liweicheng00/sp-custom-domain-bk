import sys
import json
import glob
import pulumi
import mimetypes
from pulumi import automation as auto
from pulumi_aws import s3, cloudfront, acm
from fastapi import APIRouter, HTTPException, Response, status, Depends, Form

router = APIRouter(
    tags=["architecture"],
    responses={404: {"description": "Not found"}},
)
project_name = "sp-custom-domain"
project_settings = auto.ProjectSettings(name=project_name, runtime="python")
ws = auto.LocalWorkspace(project_settings=project_settings)


@router.post("/architecture")
def create_project_default_architecture():
    pulumi_update(pulumi_program, stack_name="s3_static_website")
    return "success"


@router.delete('/architecture')
def delete_project_default_architecture():
    pulumi_update(lambda _: None, stack_name="s3_static_website", destroy=True)
    return "success"


def pulumi_update(program, /, *, stack_name, destroy=False, refresh=False):
    stack = auto.create_or_select_stack(stack_name=stack_name,
                                        project_name=project_name,
                                        program=program)
    stack.set_config("aws:region", auto.ConfigValue(value="us-west-2"))

    if destroy:
        stack.destroy(on_output=print)
        return
    if refresh:
        stack.refresh(on_output=print)
        return

    stack.up(on_output=print)
    return stack.outputs()


def pulumi_program():
    s3_bucket_domain_name = upload_web_files()
    create_cloudfront_distribution("sp-custom-domain-bucket", s3_bucket_domain_name)


def upload_web_files():
    site_bucket = s3.Bucket("s3-website-bucket", website=s3.BucketWebsiteArgs(index_document="index.html"))

    for path in glob.glob('static/**/*.*', recursive=True):
        s3.BucketObject("/".join(path.split('/')[1:]),
                        bucket=site_bucket.id,  # reference to the s3.Bucket object
                        source=path,
                        content_type=mimetypes.guess_type(path)[0])  # set the MIME type of the file

    s3.BucketPolicy("bucket-policy", bucket=site_bucket.id, policy=site_bucket.id.apply(lambda id: json.dumps({
        "Version": "2012-10-17",
        "Statement": {
            "Effect": "Allow",
            "Principal": "*",
            "Action": ["s3:GetObject"],
            # Policy refers to bucket explicitly
            "Resource": [f"arn:aws:s3:::{id}/*"]
        },
    })))
    pulumi.export("website_url", site_bucket.website_endpoint)
    return site_bucket.bucket_domain_name


def create_cloudfront_distribution(s3_origin_id, s3_bucket_domain_name):
    s3_distribution = cloudfront.Distribution("sp-custom-domain-distribution",
                                              origins=[cloudfront.DistributionOriginArgs(
                                                  domain_name=s3_bucket_domain_name,
                                                  origin_id=s3_origin_id,
                                              )],
                                              enabled=True,
                                              is_ipv6_enabled=True,
                                              default_root_object="index.html",
                                              restrictions=cloudfront.DistributionRestrictionsArgs(
                                                  geo_restriction=cloudfront.DistributionRestrictionsGeoRestrictionArgs(
                                                      restriction_type="blacklist",
                                                      locations=['CN']
                                                  ),
                                              ),
                                              default_cache_behavior=cloudfront.DistributionDefaultCacheBehaviorArgs(
                                                  allowed_methods=[
                                                      "GET",
                                                      "HEAD",
                                                  ],
                                                  cached_methods=[
                                                      "GET",
                                                      "HEAD",
                                                  ],
                                                  target_origin_id=s3_origin_id,
                                                  viewer_protocol_policy="allow-all",
                                                  compress=True,
                                                  cache_policy_id="658327ea-f89d-4fab-a63d-7e88639e58f6"
                                              ),

                                              viewer_certificate=cloudfront.DistributionViewerCertificateArgs(
                                                  cloudfront_default_certificate=True,
                                              ))
    pulumi.export('cloudfront', s3_distribution.domain_name)
