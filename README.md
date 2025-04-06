
# Docker

1. docker build --platform linux/amd64 -t yolo-ocr-api .
2. docker run --platform linux/amd64 -p 8000:8000 --env-file .env yolo-ocr-api