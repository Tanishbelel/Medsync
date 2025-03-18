import cv2
import pytesseract
import numpy as np
from django.conf import settings
import os
from .models import Medicine

# Configure Tesseract Path (Windows Only)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Update this if needed

def preprocess_image(image_path):
    """Improve OCR accuracy with better preprocessing"""
    image = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Resize for better OCR
    scale_percent = 150  # Resize by 150%
    width = int(gray.shape[1] * scale_percent / 100)
    height = int(gray.shape[0] * scale_percent / 100)
    gray = cv2.resize(gray, (width, height), interpolation=cv2.INTER_LINEAR)
    
    # Apply adaptive thresholding
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
    
    return gray

def extract_text(image_path):
    """Extract text from a prescription image"""
    processed_image = preprocess_image(image_path)
    text = pytesseract.image_to_string(processed_image)
    return text.strip()

from .models import Medicine

import re

def get_medicine_info(text):
    """Extract medicine names and dosages using regex"""
    medicine_pattern = r"([A-Za-z]+(?:\s[A-Za-z]+))\s(\d+mg|\d+ml)?"
    matches = re.findall(medicine_pattern, text)

    medicines = []
    for match in matches:
        name = match[0].strip()
        dosage = match[1].strip() if match[1] else ""
        medicines.append(Medicine(name=name, dosage=dosage))
    
    # Save extracted medicines
    Medicine.objects.bulk_create(medicines)

    return Medicine.objects.all()


def process_prescription(image):
    """Main function to process prescription image"""
    upload_dir = os.path.join(settings.MEDIA_ROOT, "prescriptions")
    os.makedirs(upload_dir, exist_ok=True)

    image_path = os.path.join(upload_dir, image.name)

    with open(image_path, "wb+") as destination:
        for chunk in image.chunks():
            destination.write(chunk)

    extracted_text = extract_text(image_path)
    medicine_data = get_medicine_info(extracted_text)

    return medicine_data