import json
import traceback
from fastapi import APIRouter, HTTPException, Form, Depends, UploadFile, Request
from app.utils.jwt_token import verify_jwt

router = APIRouter(
    tags=["metadata"],
    responses={404: {"description": "Not found"}},
)


@router.put('/metadata')
async def update_metadata(request: Request, payload=Depends(verify_jwt)):
    try:
        address = payload['sub']
        ...  # validate operation permission
        ...  # update database

        r = request.app.redis
        # Update redis data
        # await r.update(key, value)
        # Publish to make all instances refresh metadata from redis
        # await r.publish('channel2', "")

        return "Update successfully."
    except HTTPException as e:
        raise e
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500)


@router.post('/metadata/logo')
async def update_logo(request: Request, file: UploadFile, id: str = Form(...), payload=Depends(verify_jwt)):
    try:
        address = payload['sub']
        ...  # validate operation permission
        ...  # upload file to cloud service like s3
        ...  # update database

        r = request.app.redis
        # Update redis data
        # await r.update(key, value)
        # Publish to make all instances refresh metadata from redis
        # await r.publish('channel2', "")

        return {"image_url": "https://url.com"}
    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        print(str(e))
        raise HTTPException(status_code=500)



