import time
import os
import cv2

SPEED_LIMIT = 60  # km/h

class ViolationChecker:
    def __init__(self, save_dir="data/images"):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        self.violation_captured = {}  # Track which vehicles already have saved images

    def check(self, frame, tracked_objects, speeds, light_state):
        """
        Returns list of violations ONLY when they occur.
        Only saves image once per vehicle.
        """
        violations = []

        for obj in tracked_objects:
            obj_id = obj["id"]
            vehicle_type = obj["class"]
            speed = speeds.get(obj_id, 0)

            violation_type = None
            
            # Check for overspeed violation
            if speed > SPEED_LIMIT:
                violation_type = "Overspeed"
            
            # Check for red light violation
            elif light_state == "RED":
                violation_type = "Red Light"

            # Only process if there's an actual violation
            if violation_type:
                # Only save image once per vehicle
                if obj_id not in self.violation_captured:
                    img_path = os.path.join(
                        self.save_dir, 
                        f"{vehicle_type}_{obj_id}_{int(time.time())}.jpg"
                    )
                    cv2.imwrite(img_path, frame)
                    self.violation_captured[obj_id] = True
                else:
                    # Use existing image path (won't be saved again to DB)
                    img_path = f"Already captured for ID {obj_id}"

                violations.append({
                    "vehicle_id": obj_id,
                    "vehicle_type": vehicle_type,
                    "speed": round(speed, 2),
                    "violation": violation_type,
                    "image": img_path,
                    "time": time.strftime("%Y-%m-%d %H:%M:%S")
                })

        return violations