from fastapi import FastAPI
from app.api import router

app = FastAPI(title="YOLO + OCR API", version="1.0")
app.include_router(router)
