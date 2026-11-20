import sqlite3
from pathlib import Path
from threading import Lock

class WiFiDatabase:
    def __init__(self, db_path):
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.lock = Lock()
        with self.lock:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS access_points (
                    bssid TEXT PRIMARY KEY,
                    ssid TEXT NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    rssi_avg REAL NOT NULL,
                    signal_count INTEGER NOT NULL
                )
            """)
            self.conn.commit()

    def save_access_point(self, bssid, ssid, rssi, timestamp):
        with self.lock:
            row = self.conn.execute(
                "SELECT rssi_avg, signal_count FROM access_points WHERE bssid=?", (bssid,)
            ).fetchone()
            if row:
                avg, count = row
                count += 1
                avg = ((avg * (count - 1)) + rssi) / count
                self.conn.execute("""
                    UPDATE access_points SET ssid=?, last_seen=?, rssi_avg=?, signal_count=?
                    WHERE bssid=?
                """, (ssid, timestamp, avg, count, bssid))
            else:
                self.conn.execute("""
                    INSERT INTO access_points
                    (bssid, ssid, first_seen, last_seen, rssi_avg, signal_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (bssid, ssid, timestamp, timestamp, float(rssi), 1))
            self.conn.commit()

    def close(self):
        with self.lock:
            self.conn.close()
