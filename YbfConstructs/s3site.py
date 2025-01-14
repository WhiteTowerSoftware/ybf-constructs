from aws_cdk import aws_s3_deployment as s3deploy
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_route53 as rt53
from aws_cdk import aws_route53_targets as rt53_targets
from constructs import Construct
import typing


class SiteDeploy(Construct):
    '''Represents a construct to deploy a static site to S3

    This construct will additionally add a domain name to the site
    and will redirect all HTTP to HTTPS
    '''

    def __init__(
            self, scope: Construct, id: str, *,
            sources: typing.Sequence[s3deploy.ISource],
            certificate: acm.ICertificate,
            domain_name: str,
            route53_zone: rt53.IHostedZone,
            bucket_name: typing.Optional[str] = None,
            prune_bucket: typing.Optional[bool] = False,
            root_object: typing.Optional[str] = 'index.html') -> None:
        super().__init__(scope, id)

        if bucket_name is None:
            pkgBucket = s3.Bucket(self, "SiteBucket")
        else:
            pkgBucket = s3.Bucket.from_bucket_name(
                self, "SiteBucket", bucket_name)

        distribution = cloudfront.Distribution(
            self, "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(pkgBucket),
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS  # noqa: E501
            ),
            default_root_object=root_object,
            domain_names=[domain_name],
            certificate=certificate
        )

        rt53.ARecord(
            self, "DnsRecord",
            record_name=domain_name,
            zone=route53_zone,
            target=rt53.RecordTarget.from_alias(
                rt53_targets.CloudFrontTarget(distribution))
        )

        s3deploy.BucketDeployment(
            self, "WebsiteFiles",
            sources=sources,
            destination_bucket=pkgBucket,
            distribution=distribution,
            prune=prune_bucket
        )
