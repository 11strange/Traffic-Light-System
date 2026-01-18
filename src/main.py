
import cv2
from src.detector import VehicleDetector
from src.tracker import VehicleTracker
from src.traffic_light import TrafficLight
from src.violation import ViolationChecker
from src.database import Database
from src.speed_estimator import SpeedEstimator
import os
import shutil
from datetime import datetime

CLEAR_OLD_DATA = True  
BASE_DIR = r"D:\Traffic Light System"

if CLEAR_OLD_DATA:
    print("🗑️  Clearing old violation data...")
    
    # Remove old images - use the exact paths
    images_path = r"D:\Traffic Light System\outputs\images"
    if os.path.exists(images_path):
        shutil.rmtree(images_path)
        print(f"   ✓ Deleted old images from: {images_path}")
    else:
        print(f"   ℹ No images folder found at: {images_path}")
    
    # Remove old database - use the exact path
    db_path = r"D:\Traffic Light System\database\violations.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"   ✓ Deleted old database from: {db_path}")
    else:
        print(f"   ℹ No database found at: {db_path}")
    
    print("✅ Cleanup complete\n")
else:
    print("📁 Keeping existing violation data")
    print("   (Set CLEAR_OLD_DATA=True to delete old records)\n")

# Always ensure directories exist
os.makedirs(r"D:\Traffic Light System\outputs\images", exist_ok=True)
os.makedirs(r"D:\Traffic Light System\database", exist_ok=True)

# Optional: Archive old data instead of deleting
def archive_old_data():
    """Move old data to archive folder with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = os.path.join(BASE_DIR, "archives", f"run_{timestamp}")
    
    images_path = os.path.join(BASE_DIR, "outputs", "images")
    if os.path.exists(images_path):
        os.makedirs(archive_dir, exist_ok=True)
        shutil.move(images_path, os.path.join(archive_dir, "images"))
        print(f"📦 Archived images to {archive_dir}/images")
    
    db_path = os.path.join(BASE_DIR, "database", "violations.db")
    if os.path.exists(db_path):
        os.makedirs(archive_dir, exist_ok=True)
        shutil.copy(db_path, os.path.join(archive_dir, "violations.db"))
        print(f"📦 Archived database to {archive_dir}/violations.db")


# Path to input video
VIDEO_PATH = os.path.join(BASE_DIR, "data", "Cars_Moving_On_Road_Stock_Footage_-_Free_Download_1080P.mp4")

# Initialize modules
detector = VehicleDetector(os.path.join(BASE_DIR, "models", "yolov8n.pt"))
tracker = VehicleTracker()
light = TrafficLight()
speed_estimator = None
violation_checker = ViolationChecker(save_dir=os.path.join(BASE_DIR, "outputs", "images"))
db = Database(db_path=os.path.join(BASE_DIR, "database", "violations.db"))

# Open video
cap = cv2.VideoCapture(VIDEO_PATH)
fps = cap.get(cv2.CAP_PROP_FPS)
speed_estimator = SpeedEstimator(
    fps=fps,
    pixel_to_meter=0.024423  # ← YOUR CALIBRATED VALUE HERE (example)
)
# Track which vehicles have already been recorded for violations
recorded_violations = set()

DISPLAY_WIDTH = 1200
DISPLAY_HEIGHT=800

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT))


    # 1. Detect vehicles
    detections = detector.detect_vehicles(frame)

    # 2. Track vehicles
    tracked_objects = tracker.update(detections)

    # 3. Estimate speed
    speeds = speed_estimator.estimate(tracked_objects)

    # 4. Check for violations (only returns actual violations)
    violations = violation_checker.check(frame, tracked_objects, speeds, light.get_state())

    # 5. Save violations ONCE per vehicle in DB
    for violation in violations:
        obj_id = violation["vehicle_id"]
        
        # Only save if this vehicle hasn't been recorded yet
        if obj_id not in recorded_violations:
            db.insert_violation(
                vehicle_id=obj_id,
                vehicle_type=violation["vehicle_type"],
                speed=violation["speed"],
                violation_type=violation["violation"],
                image_path=violation["image"]
            )
            recorded_violations.add(obj_id)
            print(f"⚠️  VIOLATION RECORDED: ID {obj_id} - {violation['violation']} ({violation['speed']} km/h)")

    # 6. Draw bounding boxes for all tracked vehicles
    for obj in tracked_objects:
        x1, y1, x2, y2 = map(int, obj["bbox"])
        obj_id = obj["id"]
        speed = speeds.get(obj_id, 0)
        
        # Check if this vehicle is currently violating
        is_violating = any(v["vehicle_id"] == obj_id for v in violations)
        
        # RED box for violations, WHITE box for normal
        box_color = (0, 0, 255) if is_violating else (255, 255, 255)
        text_color = (0, 0, 255) if is_violating else (255, 255, 255)
        
        # Draw box
        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
        
        # Draw speed label
        label = f"ID:{obj_id} {speed:.1f}km/h"
        if is_violating:
            label += " VIOLATION!"
        
        cv2.putText(frame, label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    text_color,
                    2)

    # 7. Display violation summary on screen
    violation_count = len(recorded_violations)
    cv2.putText(frame, f"Total Violations: {violation_count}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255),
                2)

    # 8. Show the live video
    cv2.imshow("Traffic Violation System", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print(f"\n✅ Processing complete. Total violations recorded: {violation_count}")