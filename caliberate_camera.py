"""
Camera Calibration Tool for Speed Estimation
Run this BEFORE your main traffic system to get accurate pixel_to_meter value
"""

import cv2
import math

class CalibrationTool:
    def __init__(self, video_path):
        self.video_path = video_path
        self.points = []
        self.frame = None
        
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse clicks to mark points"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.points.append((x, y))
            print(f"✓ Point {len(self.points)}: ({x}, {y})")
            
            # Draw the point
            cv2.circle(self.frame, (x, y), 5, (0, 0, 255), -1)
            
            # Draw line if we have 2 points
            if len(self.points) == 2:
                cv2.line(self.frame, self.points[0], self.points[1], (0, 255, 0), 2)
                pixel_dist = math.dist(self.points[0], self.points[1])
                
                # Show distance on frame
                mid_x = (self.points[0][0] + self.points[1][0]) // 2
                mid_y = (self.points[0][1] + self.points[1][1]) // 2
                cv2.putText(self.frame, f"{pixel_dist:.1f}px", 
                           (mid_x, mid_y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow("Calibration", self.frame)
    
    def run(self):
        """Run the calibration tool"""
        print("\n" + "="*60)
        print("CAMERA CALIBRATION TOOL")
        print("="*60)
        print("\nSTEPS:")
        print("1. Video will pause on first frame")
        print("2. IMPORTANT: Measure distance ALONG traffic direction (not across):")
        print("   - Distance between dashed lines: 12m (dash + gap)")
        print("   - Two consecutive dashes: 12-15m")
        print("   - Known road feature in direction of travel")
        print("   ⚠️  DON'T use lane width - causes perspective errors!")
        print("3. Click TWO points marking this distance")
        print("4. Enter the real-world distance in meters")
        print("5. Copy the calibrated value to your code")
        print("\nPress any key to start...")
        print("="*60 + "\n")
        
        # Open video
        cap = cv2.VideoCapture(self.video_path)
        ret, self.frame = cap.read()
        
        if not ret:
            print("❌ Error: Could not read video")
            return
        
        # Create window
        cv2.namedWindow("Calibration")
        cv2.setMouseCallback("Calibration", self.mouse_callback)
        
        # Show instructions on frame
        h, w = self.frame.shape[:2]
        overlay = self.frame.copy()
        cv2.rectangle(overlay, (10, 10), (w-10, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, self.frame, 0.3, 0, self.frame)
        
        cv2.putText(self.frame, "CALIBRATION MODE", (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.putText(self.frame, "1. Click START point of known distance", (20, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(self.frame, "2. Click END point of known distance", (20, 95),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        cv2.imshow("Calibration", self.frame)
        
        # Wait for user to mark 2 points
        while len(self.points) < 2:
            key = cv2.waitKey(1)
            if key == 27:  # ESC
                print("❌ Calibration cancelled")
                cap.release()
                cv2.destroyAllWindows()
                return
        
        # Calculate pixel distance
        pixel_distance = math.dist(self.points[0], self.points[1])
        
        # Get real distance from user
        print(f"\n📏 Pixel distance: {pixel_distance:.2f} pixels")
        print(f"📍 Point 1: {self.points[0]}")
        print(f"📍 Point 2: {self.points[1]}")
        
        try:
            real_distance = float(input("\n✏️  Enter REAL distance in meters: "))
            
            # Calculate calibration
            pixel_to_meter = real_distance / pixel_distance
            
            print("\n" + "="*60)
            print("✅ CALIBRATION COMPLETE!")
            print("="*60)
            print(f"Pixel distance: {pixel_distance:.2f} pixels")
            print(f"Real distance: {real_distance:.2f} meters")
            print(f"Calibrated ratio: {pixel_to_meter:.6f} meters/pixel")
            print("\n📋 ADD THIS TO YOUR CODE:")
            print("="*60)
            print(f"speed_estimator = SpeedEstimator(")
            print(f"    fps={cap.get(cv2.CAP_PROP_FPS):.0f},")
            print(f"    pixel_to_meter={pixel_to_meter:.6f}")
            print(f")")
            print("="*60 + "\n")
            
            # Show final result
            result_frame = self.frame.copy()
            cv2.putText(result_frame, f"Calibrated: {pixel_to_meter:.6f} m/px", 
                       (20, h - 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Calibration", result_frame)
            cv2.waitKey(0)
            
        except ValueError:
            print("❌ Invalid input")
        
        cap.release()
        cv2.destroyAllWindows()


# Run the calibration tool
if __name__ == "__main__":
    VIDEO_PATH = r"D:\Traffic Light System\data\Cars_Moving_On_Road_Stock_Footage_-_Free_Download_1080P.mp4"
    
    calibrator = CalibrationTool(VIDEO_PATH)
    calibrator.run()