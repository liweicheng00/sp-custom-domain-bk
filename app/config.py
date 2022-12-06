import os
from typing import Optional, Union
from pydantic import BaseSettings, HttpUrl


class Settings(BaseSettings):
    runtime_env: str = os.getenv('RUNTIME_ENV')
    docs_url: Optional[str] = None

    project_name: str = "sp-custom-domain"
    s3_bucket_domain_name: str = os.getenv('S3_BUCKET_DOMAIN_NAME')
    default_project_domain_name: str = os.getenv('DEFAULT_PROJECT_DOMAIN_NAME')
    hosted_zone_id: str = os.getenv('HOSTED_ZONE_ID')


class StagingSettings(Settings):
    docs_url: Optional[str] = '/docs'


class DemoSettings(StagingSettings):
    ...


class HotfixStagings(StagingSettings):
    ...


class TestSettings(StagingSettings):
    from dotenv import load_dotenv
    load_dotenv()
    docs_url: Optional[str] = None
    trusted_hosts: list = None


class ProdSettings(Settings):
    origins: list = []
    trusted_hosts: list = []


class RcSettings(ProdSettings):
    ...


RUNTIME_ENV = os.getenv('RUNTIME_ENV')
if RUNTIME_ENV == 'production':
    settings = ProdSettings()
elif RUNTIME_ENV == 'rc':
    settings = RcSettings()
elif RUNTIME_ENV == 'staging':
    settings = StagingSettings()
elif RUNTIME_ENV == 'demo':
    settings = DemoSettings()
elif RUNTIME_ENV == 'hotfix':
    settings = HotfixStagings()
elif RUNTIME_ENV == 'test':
    settings = TestSettings()
    settings.mongodb_db = 'test'
else:
    settings = StagingSettings()
