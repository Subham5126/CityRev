from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from supabase import create_client
from ultralytics import YOLO
import cv2, numpy as np

# Supabase setup
SUPABASE_URL = "https://kxyejwmhqqqdkjwbxeiv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt4eWVqd21ocXFxZGtqd2J4ZWl2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODA3ODcxMCwiZXhwIjoyMDczNjU0NzEwfQ.q059iunjpq0CpuMwY9eacPxh6bDrw1fB_uDOdpKxcUU"  # Keep this safe!
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

# Load YOLO models
pothole_model = YOLO("pothole_best.pt")
garbage_model = YOLO("garbage_best.pt")

@app.post("/analyze/")
async def analyze(
    file: UploadFile = File(...),
    report_id: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    location: str = Form(...)
):
    # Read image bytes
    contents = await file.read()
    np_arr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Detection flags
    pothole_detected, garbage_detected = False, False

    # Pothole detection
    results_pothole = pothole_model(img)
    for r in results_pothole:
        for box in r.boxes:
            label = pothole_model.names[int(box.cls[0])].lower()
            if label == "pothole":
                pothole_detected = True

    # Garbage detection
    results_garbage = garbage_model(img)
    for r in results_garbage:
        for box in r.boxes:
            label = garbage_model.names[int(box.cls[0])].lower()
            if "garbage" in label:
                garbage_detected = True

    detected = pothole_detected or garbage_detected

    if detected:
        # Upload image to Supabase Storage
        img_path = f"reports/{report_id}.jpg"
        supabase.storage.from_("reports").upload(img_path, contents)

        # Get public URL
        image_url = supabase.storage.from_("reports").get_public_url(img_path)

        # Insert record into Supabase DB
        supabase.table("reports").insert({
            "report_id": report_id,
            "description": description,
            "category": category,
            "location": location,
            "image_url": image_url,
            "pothole_detected": pothole_detected,
            "garbage_detected": garbage_detected
        }).execute()

    return JSONResponse(content={
        "detected": detected,
        "pothole": pothole_detected,
        "garbage": garbage_detected,
        "image_url": image_url if detected else None
    })
