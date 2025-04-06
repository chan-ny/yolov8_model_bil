import cv2
import numpy as np
from ultralytics import YOLO
import pytesseract
import re
from datetime import datetime
import base64
import binascii

# --- Load YOLO Model Once ---
model = YOLO('models/dataset_model.pt')
class_names = model.names

# --- Image Processing Functions ---
def threshold_image_GAUSSIAN(img: np.ndarray) -> str:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.fastNlMeansDenoising(gray, None, 21, 5, 20)
    gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 11, 2)
    kernel = np.ones((1, 1), np.uint8)
    gray = cv2.dilate(gray, kernel, iterations=1)
    gray = cv2.erode(gray, kernel, iterations=1)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    # return gray
    return pytesseract.image_to_string(gray, config="--oem 3 --psm 6 -l eng")

def grayscale_image(img: np.ndarray) -> str:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    # return gray
    return pytesseract.image_to_string(gray, config="--oem 3 --psm 6 -l eng+lao")

def clean_text(data: dict) -> dict:
    cleaned = {}
    for key, value in data.items():
        cleaned_value = re.sub(r'[\n\r]', ' ', value)
        if key not in ['Description', 'BILL']:
            cleaned_value = re.sub(r'[^\w\s,.-]', '', cleaned_value).strip().replace(" ", "").replace(",", "")
        cleaned[key] = cleaned_value
    return cleaned

def extract_details(account_str):
    pattern = r"([A-Z]+)(MS|MR)([\d\w+-]+)(LAK|THB|USD)$"
    match = re.match(pattern, account_str)
    if match:
        name = f'{match.group(1)} {match.group(2)}'
        return name, match.group(3), match.group(4)
    return None, None, None

# --- Main Processing Function ---
def process_base64_image(base64_string: str):
    # --- Clean and Validate Base64 ---
    if ',' in base64_string:
        base64_string = base64_string.split(",")[1]

    missing_padding = len(base64_string) % 4
    if missing_padding:
        base64_string += '=' * (4 - missing_padding)

    try:
        image_bytes = base64.b64decode(base64_string)
    except binascii.Error as e:
        raise ValueError("Invalid base64 input.") from e

    image_array = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Failed to decode image from base64.")

    # --- YOLO Detection ---
    results = model.predict(source=img, conf=0.1, imgsz=640)
    boxes = results[0].boxes.data

    # --- OCR Extraction ---
    extracted_text = {}
    for i, box in enumerate(boxes):
        x1, y1, x2, y2, conf, cls = map(int, box.tolist())
        class_name = class_names.get(cls, f"class_{cls}")
        cropped_img = img[y1:y2, x1:x2]

        if class_name == "QR_CODE":
            continue
        elif class_name in ["Description", "BILL"]:
            # cv2.imwrite(f"imgs/{class_name}.jpg", grayscale_image(cropped_img))
            extracted_text[class_name] = grayscale_image(cropped_img)
        else:
            # cv2.imwrite(f"imgs/{class_name}.jpg", threshold_image_GAUSSIAN(cropped_img))
            extracted_text[class_name] = threshold_image_GAUSSIAN(cropped_img)

    # --- Clean OCR Results ---
    cleaned_data = clean_text(extracted_text)

    # --- Extract Fields ---
    raw_data = {}
    for key, value in cleaned_data.items():
        if key == 'Created_Date':
            raw_data[key] = datetime.strptime(re.sub(r"[^\d]", "", value), "%d%m%y%H%M%S")
        elif key == 'Reference_No':
            raw_data[key] = re.sub(r"[^\d]", "", value)
        elif key == 'Amount':
            raw_data[key] = re.sub(r"[^\d]", "", value)
        elif key == 'Fee':
            raw_data[key] = re.sub(r"[^\d]", "", value)
        elif key == 'Tricket_NO':
            match = re.match(r"([A-Za-z0-9]+)", value)
            raw_data[key] = match.group(1) if match else value
        elif key == 'Source_Account':
            name, account, currency = extract_details(value)
            raw_data.update({
                "source_name": name,
                "source_account": account,
                "source_currency": currency
            })
        elif key == 'Destination_Account':
            name, account, currency = extract_details(value)
            raw_data.update({
                "destination_name": name,
                "destination_account": account,
                "destination_currency": currency,
                "currency_used": currency
            })
        elif key == 'Description':
            raw_data[key] = value

    return raw_data

