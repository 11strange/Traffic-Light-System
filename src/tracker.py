
import numpy as np

class VehicleTracker:
    def __init__(self, iou_threshold=0.3):
        self.next_id = 0
        self.tracks = {}  
        self.iou_threshold = iou_threshold

    def _iou(self, boxA, boxB):
        """
        Calculate Intersection over Union (IoU)
        box format: [x1, y1, x2, y2]
        """
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        inter_area = max(0, xB - xA) * max(0, yB - yA)
        if inter_area == 0:
            return 0.0

        boxA_area = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxB_area = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

        return inter_area / float(boxA_area + boxB_area - inter_area)

    def update(self, detections):
       

        updated_tracks = {}
        assigned_tracks = set()

        for det in detections:
            bbox = det["bbox"]
            best_iou = 0
            best_id = None

            for track_id, track_bbox in self.tracks.items():
                iou = self._iou(bbox, track_bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_id = track_id

            if best_iou > self.iou_threshold:
                updated_tracks[best_id] = bbox
                assigned_tracks.add(best_id)
                det["id"] = best_id
            else:
           
                det["id"] = self.next_id
                updated_tracks[self.next_id] = bbox
                self.next_id += 1

        self.tracks = updated_tracks
        return detections
