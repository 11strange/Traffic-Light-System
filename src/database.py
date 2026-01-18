import sqlite3
import csv
from datetime import datetime

class Database:
    def __init__(self, db_path="database/violations.db"):
        self.db_path = db_path
        self.create_table()
    
    def create_table(self):
        """Create violations table if not exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER,
                vehicle_type TEXT,
                speed REAL,
                violation_type TEXT,
                image_path TEXT,
                video_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def insert_violation(self, vehicle_id, vehicle_type, speed, violation_type, image_path, video_id=None):
        """Insert a new violation record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO violations (vehicle_id, vehicle_type, speed, violation_type, image_path, video_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (vehicle_id, vehicle_type, speed, violation_type, image_path, video_id))
        conn.commit()
        conn.close()
    
    def get_all_violations(self, limit=None):
        """Get all violations, optionally limited"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()
        
        if limit:
            cursor.execute('SELECT * FROM violations ORDER BY timestamp DESC LIMIT ?', (limit,))
        else:
            cursor.execute('SELECT * FROM violations ORDER BY timestamp DESC')
        
        violations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return violations
    
    def get_violation_by_id(self, violation_id):
        """Get a single violation by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM violations WHERE id = ?', (violation_id,))
        violation = dict(cursor.fetchone()) if cursor.fetchone() else None
        conn.close()
        return violation
    
    def get_violations_by_video(self, video_id):
        """Get all violations from a specific video"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM violations WHERE video_id = ? ORDER BY timestamp DESC', (video_id,))
        violations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return violations
    
    def get_statistics(self):
        """Get overall statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total violations
        cursor.execute('SELECT COUNT(*) FROM violations')
        stats['total_violations'] = cursor.fetchone()[0]
        
        # Violations by type
        cursor.execute('SELECT violation_type, COUNT(*) as count FROM violations GROUP BY violation_type')
        stats['by_type'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Violations by vehicle type
        cursor.execute('SELECT vehicle_type, COUNT(*) as count FROM violations GROUP BY vehicle_type')
        stats['by_vehicle'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Average speed
        cursor.execute('SELECT AVG(speed) FROM violations')
        stats['avg_speed'] = round(cursor.fetchone()[0] or 0, 2)
        
        # Max speed
        cursor.execute('SELECT MAX(speed) FROM violations')
        stats['max_speed'] = round(cursor.fetchone()[0] or 0, 2)
        
        # Recent violations (last 10)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM violations ORDER BY timestamp DESC LIMIT 10')
        stats['recent'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return stats
    
    def export_to_csv(self, output_path="violations_report.csv"):
        """Export all violations to CSV"""
        violations = self.get_all_violations()
        
        if not violations:
            return None
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = violations[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(violations)
        
        return output_path
    
    def delete_violation(self, violation_id):
        """Delete a violation by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM violations WHERE id = ?', (violation_id,))
        conn.commit()
        conn.close()
    
    def clear_all_violations(self):
        """Clear all violations (use with caution!)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM violations')
        conn.commit()
        conn.close()