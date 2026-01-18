from ultralytics import YOLO
import cv2

class VehicleDetector:
    def __init__(self, model_path="D:\Traffic Light System\Models\yolov8n.pt", conf=0.25, imgsz=640):
        self.model = YOLO(model_path)
        self.conf = conf
        self.imgsz = imgsz

    def detect_vehicles(self, frame):
       
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = self.model.predict(rgb_frame, imgsz=self.imgsz, conf=self.conf, verbose=False)

        detections = []
        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()  
            scores = result.boxes.conf.cpu().numpy()
            classes = result.boxes.cls.cpu().numpy() 

            for bbox, score, cls_idx in zip(boxes, scores, classes):
                cls_name = self.model.names[int(cls_idx)]
                detections.append({
                    "bbox": bbox,       
                    "class": cls_name,   
                    "score": float(score)
                })

        return detections

    def draw_boxes(self, frame, detections):
       
        for det in detections:
            x1, y1, x2, y2 = map(int, det["bbox"])
            label = f"{det['class']} {det['score']:.2f}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
        return frame
