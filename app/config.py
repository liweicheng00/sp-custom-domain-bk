import os
from typing import Optional, Union
from pydantic import BaseSettings, HttpUrl


class Settings(BaseSettings):
    runtime_env: str = os.getenv('RUNTIME_ENV')
    docs_url: Optional[str] = None

    mongodb_db: str = os.getenv('MONGODB_DB')
    mongodb_host: str = os.getenv('MONGODB_HOST')
    mongodb_user: str = os.getenv('MONGODB_USER')
    mongodb_password: str = os.getenv('MONGODB_PASSWORD')
    mongodb_ca_cert: str = os.getenv('MONGODB_CA_CERT')

    access_token_secret_key: str = os.getenv("ACCESS_TOKEN_SECRET_KEY")
    access_token_expire_minutes: int = 60
    audience: str = "http://localhost"
    issuer: str = "http://localhost"

    frontend_domain: HttpUrl = "https://o2meta.io"

    slack_notification_webhook: str = ""

    o2_redis_host: str = os.getenv('O2_REDIS_HOST')
    o2_redis_port: Union[int, str] = os.getenv('O2_REDIS_PORT') or ""

    db_index: int = 0


class StagingSettings(Settings):
    docs_url: Optional[str] = '/docs'
    trusted_hosts: list = None
    origins: list = []

    contract_address: str = ""
    web3_url: str = "https://eth-rinkeby.alchemyapi.io/v2/"
    alchemy_token_key: str = ""
    graph_url: str = ""


class DemoSettings(StagingSettings):
    db_index: int = 3
    ...


class HotfixStagings(StagingSettings):
    db_index: int = 6


class TestSettings(StagingSettings):
    from dotenv import load_dotenv
    load_dotenv()
    docs_url: Optional[str] = None
    trusted_hosts: list = None


class ProdSettings(Settings):
    origins: list = []
    trusted_hosts: list = []
    contract_address: str = ""
    web3_url: str = "https://eth-mainnet.alchemyapi.io/v2/"
    alchemy_token_key: str = ""
    graph_url: str = ""


class RcSettings(ProdSettings):
    db_index: int = 3


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
