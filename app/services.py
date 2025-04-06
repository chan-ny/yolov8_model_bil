
import sys
import os

# Dynamically add root directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from image_processor.core import process_base64_image

def process_image_base64(base64_string: str) -> dict:
    return process_base64_image(base64_string)
