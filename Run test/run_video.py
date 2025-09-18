# =========================
# 🔹 Step 1: Install & Import
# =========================
#! pip install ultralytics opencv-python matplotlib

from ultralytics import YOLO
import cv2

# =========================
# 🔹 Step 2: Load Pothole Model
# =========================
pothole_model = YOLO("pothole_best.pt")   # trained pothole model

# =========================
# 🔹 Step 3: Parameters
# =========================
pothole_threshold = 50000   # px² for pothole seriousness
pixel_to_cm = 0.1          # 1 pixel = 0.5 cm
depth_cm = 3               # assumed pothole depth

# =========================
# 🔹 Step 4: Open Video
# =========================
video_path = "videoplayback.mp4"   # input video
cap = cv2.VideoCapture(video_path)

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter("processed_output.mp4", fourcc, 
                      cap.get(cv2.CAP_PROP_FPS), 
                      (int(cap.get(3)), int(cap.get(4))))

# =========================
# 🔹 Step 5: Initialize Totals
# =========================
total_pothole_area = 0
total_volume_cm3 = 0
total_cement_kg = 0
pothole_count = 0
frame_count = 0

# total_garbage_area = 0              # (for garbage, keep commented)
# garbage_alert_triggered = False
# high_garbage_detected = False

# =========================
# 🔹 Step 6: Process Frames
# =========================
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Run pothole detection
    results_pothole = pothole_model(frame, verbose=False)

    # =========================
    # 🔹 Process Pothole Detections
    # =========================
    for r in results_pothole:
        for box in r.boxes:
            cls = int(box.cls[0])
            label = pothole_model.names[cls].lower()

            if label == "pothole":
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                w, h = x2 - x1, y2 - y1
                area_px = w * h

                pothole_count += 1
                total_pothole_area += area_px

                # Convert to real-world units
                real_area_cm2 = area_px * (pixel_to_cm ** 2)
                volume_cm3 = real_area_cm2 * depth_cm
                cement_kg = volume_cm3 / 1000

                total_volume_cm3 += volume_cm3
                total_cement_kg += cement_kg

                # Optional: draw box
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0,255,0), 2)
                cv2.putText(frame, f"Pothole",
                            (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0,255,0), 2)

        frame_count += 1
    # =========================
    # 🔹 Garbage Detection (commented)
    # =========================
    # results_garbage = garbage_model(frame, verbose=False)
    # for r in results_garbage:
    #     for box in r.boxes:
    #         cls = int(box.cls[0])
    #         label = garbage_model.names[cls].lower()
    #         if "garbage" in label or label in ["low", "medium", "high"]:
    #             x1, y1, x2, y2 = box.xyxy[0].tolist()
    #             w, h = x2 - x1, y2 - y1
    #             area_px = w * h
    #             total_garbage_area += area_px
    #             if area_px > garbage_threshold:
    #                 garbage_alert_triggered = True
    #             if label == "high":
    #                 high_garbage_detected = True

    out.write(frame)

cap.release()
out.release()

# =========================
# 🔹 Step 7: Final Report
# =========================
print("\n===== FINAL VIDEO REPORT =====")
print(f"🕳️ Total potholes detected: {int(pothole_count/frame_count*10)}")
print(f"   Total pothole area = {total_pothole_area:.2f} px²")
print(f"   Total pothole volume = {total_volume_cm3:.2f} cm³")
print(f"   Cement required ≈ {total_cement_kg:.2f} kg")

# print(f"\n🚮 Garbage Report:")   # (commented)
# print(f"   Total garbage area = {total_garbage_area:.2f} px²")
# if garbage_alert_triggered:
#     print("   ⚠ Garbage Alert! Some garbage exceeds threshold area.")
# if high_garbage_detected:
#     print("   🚨 HIGH Garbage Level detected!")
