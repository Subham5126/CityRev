# =========================
# 🔹 Step 1: Install & Import
# =========================
#! pip install ultralytics opencv-python matplotlib

from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt

# =========================
# 🔹 Step 2: Load Pothole Model
# =========================
pothole_model = YOLO("pothole_best.pt")   # trained pothole model
garbage_model = YOLO("garbage_best.pt") # trained garbage model


# =========================
# 🔹 Step 2: Upload Image
# =========================
abs_path = "C:/Users/User/Desktop/Kartikeya/Kartikeya_Engg_Study_NOTES/Hackathons/Outputs/Test_images/"
image = input("Enter image name with extension (e.g., test1.jpg): ")
image_path = abs_path+image   # upload your test image
results_pothole = pothole_model(image_path)
results_garbage = garbage_model(image_path)

# =========================
# 🔹 Step 4: Parameters
# =========================
pothole_threshold = 5500   # px²
garbage_threshold = 40000  # px²
pixel_to_cm = 0.2          # 1 pixel = 0.5 cm
depth_cm = 3               # pothole assumed depth

# =========================
# 🔹 Step 5: Initialize totals
# =========================
total_area_px = 0
total_volume_cm3 = 0
cement_needed_kg = 0
total_garbage_area = 0
pothole_count = 0
garbage_alert_triggered = False

# =========================
# 🔹 Step 6A: Process Potholes
# =========================
for r in results_pothole:
    for box in r.boxes:
        cls = int(box.cls[0])
        label = pothole_model.names[cls].lower()

        if label == "pothole":
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            w = x2 - x1
            h = y2 - y1
            area_px = w * h

            pothole_count += 1
            total_area_px += area_px

            # Convert to real-world area
            real_area_cm2 = area_px * (pixel_to_cm ** 2)
            volume_cm3 = real_area_cm2 * depth_cm
            cement_kg = volume_cm3 / 1000

            total_volume_cm3 += volume_cm3
            cement_needed_kg += cement_kg

            print(f"🕳️ Pothole {pothole_count}:")
            print(f"   Area = {area_px:.2f} px² ({real_area_cm2:.2f} cm²)")
            print(f"   Volume = {volume_cm3:.2f} cm³")
            print(f"   Cement Needed ≈ {cement_kg:.2f} kg")

            if area_px > pothole_threshold:
                print("   ⚠️ Serious pothole – fill immediately!")

# =========================
# 🔹 Step 6B: Process Garbage
# =========================
for r in results_garbage:
    for box in r.boxes:
        cls = int(box.cls[0])
        label = garbage_model.names[cls].lower()

        if "garbage" in label:  # in case labels are "low", "medium", "high"
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            w = x2 - x1
            h = y2 - y1
            area_px = w * h

            total_garbage_area += area_px

            if area_px > garbage_threshold:
                garbage_alert_triggered = True
                print(f"🚮 Garbage detected: {label} with area {area_px:.2f} px²")

# =========================
# 🔹 Step 7: Final Reports
# =========================
print("\n===== Final Report =====")
print(f"🕳️ Total potholes: {pothole_count}")
print(f"   Combined Pothole Area = {total_area_px:.2f} px²")
print(f"   Total Volume = {total_volume_cm3:.2f} cm³")
print(f"   Cement Required ≈ {cement_needed_kg:.2f} kg")

print(f"\n🚮 Garbage Report:")
print(f"   Total Garbage Area = {total_garbage_area:.2f} px²")
if garbage_alert_triggered:
    print("   ⚠️ Garbage Alert! Area exceeds threshold.")

# =========================
# 🔹 Step 8: Show Image with Detections
# =========================
# Draw detections from both models on image
img_pothole = results_pothole[0].plot()
img_garbage = results_garbage[0].plot()

# Combine outputs (side by side)
combined = cv2.hconcat([img_pothole, img_garbage])

plt.imshow(cv2.cvtColor(combined, cv2.COLOR_BGR2RGB))
plt.axis("off")
plt.show()
