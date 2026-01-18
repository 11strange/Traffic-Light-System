import math
from collections import deque

class SpeedEstimator:
    def __init__(self, fps, pixel_to_meter=0.05, window_size=10, min_dist_thresh=2.0):
        self.fps = fps
        self.pixel_to_meter = pixel_to_meter
        self.prev_positions = {}
        self.speed_buffer = {}  # last 'n' speeds for smoothing
        self.window_size = window_size
        self.min_dist_thresh = min_dist_thresh

    def estimate(self, tracked_objects):
        current_speeds = {}

        for obj in tracked_objects:
            obj_id = obj["id"]
            x1, y1, x2, y2 = obj["bbox"]
            
            # Calculate center point
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

            if obj_id in self.prev_positions:
                px, py = self.prev_positions[obj_id]
                
                # 1. Euclidean distance
                dist_px = math.dist((cx, cy), (px, py))
                
                # 2. Threshold micro-movements
                if dist_px < self.min_dist_thresh:
                    dist_px = 0

                # 3. Speed in m/s and km/h
                dist_m = dist_px * self.pixel_to_meter
                speed_mps = dist_m * self.fps
                speed_kmph = speed_mps * 3.6
                
                # 4. Moving average smoothing
                if obj_id not in self.speed_buffer:
                    self.speed_buffer[obj_id] = deque(maxlen=self.window_size)
                self.speed_buffer[obj_id].append(speed_kmph)
                avg_speed = sum(self.speed_buffer[obj_id]) / len(self.speed_buffer[obj_id])
                current_speeds[obj_id] = round(avg_speed, 2)
            else:
                current_speeds[obj_id] = 0
                self.speed_buffer[obj_id] = deque(maxlen=self.window_size)

            # Update previous position
            self.prev_positions[obj_id] = (cx, cy)

        # Cleanup old objects
        active_ids = {obj["id"] for obj in tracked_objects}
        self.prev_positions = {k: v for k, v in self.prev_positions.items() if k in active_ids}
        self.speed_buffer = {k: v for k, v in self.speed_buffer.items() if k in active_ids}

        return current_speeds
