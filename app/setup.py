from app.models.database import db


def create_account_collection():
    db.create_collection('account')


def init_db():
    if len(db.list_collection_names()) == 0:
        print('init db')
        create_account_collection()
        print('init db done')
    else:
        print('Not init db')


