from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import os
import cv2
from werkzeug.utils import secure_filename
import threading
import time
from datetime import datetime

# Import your existing modules
from src.detector import VehicleDetector
from src.tracker import VehicleTracker
from src.speed_estimator import SpeedEstimator
from src.violation import ViolationChecker
from src.database import Database

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'mkv'}

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('outputs/images', exist_ok=True)

# Global variables for processing status
processing_status = {
    'is_processing': False,
    'progress': 0,
    'current_video': None,
    'total_frames': 0,
    'processed_frames': 0,
    'violations_found': 0
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_video_background(video_path, video_id):
    """Process video in background thread"""
    global processing_status
    
    try:
        processing_status['is_processing'] = True
        processing_status['progress'] = 0
        
        # Initialize components
        detector = VehicleDetector(r"D:\Traffic Light System\models\yolov8n.pt")
        tracker = VehicleTracker()
        violation_checker = ViolationChecker(save_dir="outputs/images")
        db = Database(db_path="database/violations.db")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        processing_status['total_frames'] = total_frames
        
        # Initialize speed estimator with calibration
        speed_estimator = SpeedEstimator(
            fps=fps,
            pixel_to_meter=0.024420  # Use your calibrated value
        )
        
        # Create traffic light (you can modify this logic)
        from src.traffic_light import TrafficLight
        light = TrafficLight()
        
        recorded_violations = set()
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            processing_status['processed_frames'] = frame_count
            processing_status['progress'] = int((frame_count / total_frames) * 100)
            
            # Process frame
            detections = detector.detect_vehicles(frame)
            tracked_objects = tracker.update(detections)
            speeds = speed_estimator.estimate(tracked_objects)
            violations = violation_checker.check(frame, tracked_objects, speeds, light.get_state())
            
            # Save violations
            for violation in violations:
                obj_id = violation["vehicle_id"]
                if obj_id not in recorded_violations:
                    db.insert_violation(
                        vehicle_id=obj_id,
                        vehicle_type=violation["vehicle_type"],
                        speed=violation["speed"],
                        violation_type=violation["violation"],
                        image_path=violation["image"],
                        video_id=video_id  # Track which video
                    )
                    recorded_violations.add(obj_id)
                    processing_status['violations_found'] += 1
        
        cap.release()
        processing_status['progress'] = 100
        
    except Exception as e:
        print(f"Error processing video: {e}")
        processing_status['progress'] = -1  # Error state
    
    finally:
        processing_status['is_processing'] = False

@app.route('/')
def index():
    """Home page with upload form"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    """Handle video upload"""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file'}), 400
    
    file = request.files['video']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Create unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(f"{timestamp}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Start processing in background
        video_id = timestamp
        processing_status['current_video'] = filename
        processing_status['violations_found'] = 0
        
        thread = threading.Thread(target=process_video_background, args=(filepath, video_id))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'filename': filename
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/status')
def get_status():
    """Get current processing status"""
    return jsonify(processing_status)

@app.route('/results')
def results():
    """View all violations"""
    db = Database(db_path="database/violations.db")
    violations = db.get_all_violations()  # You'll need to add this method
    return render_template('results.html', violations=violations)

@app.route('/dashboard')
def dashboard():
    """Statistics dashboard"""
    db = Database(db_path="database/violations.db")
    stats = db.get_statistics()  # You'll need to add this method
    return render_template('dashboard.html', stats=stats)

@app.route('/download_report')
def download_report():
    """Download violations as CSV"""
    db = Database(db_path="database/violations.db")
    csv_path = db.export_to_csv()  # You'll need to add this method
    return send_file(csv_path, as_attachment=True)

@app.route('/violation/<int:violation_id>')
def view_violation(violation_id):
    """View single violation details"""
    db = Database(db_path="database/violations.db")
    violation = db.get_violation_by_id(violation_id)
    return render_template('violation_detail.html', violation=violation)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)