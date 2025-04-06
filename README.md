# Build the package

cd Detection_Bill
 1. python setup.py sdist bdist_wheel
 2. pip install dist/image_processor-0.1.0-py3-none-any.whl
 3. uvicorn app.main:app --reload

# Docker

1. docker build --platform linux/amd64 -t yolo-ocr-api .
2. docker run --platform linux/amd64 -p 8000:8000 --env-file .env yolo-ocr-api