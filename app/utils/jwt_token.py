import traceback
from datetime import datetime, timedelta
from app.config import settings
from fastapi.security import HTTPBearer
from fastapi import Depends, HTTPException, status
import jwt
from jwt import exceptions as jwt_except

ALGORITHM = "HS256"

bearer_scheme = HTTPBearer()


def create_access_token(identity: str):
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.utcnow() + access_token_expires

    payload = {'sub': identity,
               "exp": expire,
               "iat": datetime.utcnow(),
               "aud": settings.audience,
               "iss": settings.issuer}

    return jwt.encode(payload, settings.access_token_secret_key, algorithm=ALGORITHM)


def verify_jwt(token=Depends(bearer_scheme)):
    try:
        token = token.credentials
        payload = jwt.decode(token, settings.access_token_secret_key,
                             algorithms=ALGORITHM,
                             audience=settings.audience,
                             issuer=settings.issuer)
    except jwt_except.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired Token.")

    except jwt_except.DecodeError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token.")

    except jwt_except.InvalidAudienceError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid audience.")

    except jwt_except.InvalidIssuerError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid issuer.")

    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return payload
