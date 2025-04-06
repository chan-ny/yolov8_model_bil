from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from app.security import verify_api_key
from app.services import process_image_base64
import logging

router = APIRouter()

class ImageRequest(BaseModel):
    base64_image: str

@router.post("/process", dependencies=[Depends(verify_api_key)])
def process_image(request: ImageRequest):
    try:
        result = process_image_base64(request.base64_image)
        return {"success": True, "data": result}
    except ValueError as e:
        logging.exception("Processing failed")
        raise HTTPException(status_code=400, detail=str(e))
