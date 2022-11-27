import pymongo
from app.config import settings

connection = pymongo.MongoClient(settings.mongodb_host,
                                 username=settings.mongodb_user,
                                 password=settings.mongodb_password,
                                 tls=True,
                                 tlsAllowInvalidCertificates=True,
                                 tlsCAFile=settings.mongodb_ca_cert,
                                 retryWrites=False)
db = connection[settings.mongodb_db]
