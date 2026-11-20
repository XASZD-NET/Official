#!/usr/bin/env python3
"""Flask API + web dashboard for authorized, passive Wi-Fi AP inventory."""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory

from processor import SignalProcessor
from storage import WiFiDatabase
from scanner import WiFiScanner

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"
DB_PATH = BASE_DIR / "database" / "wifi_data.db"
ALLOWED_RADII = {50, 100, 150}

app = Flask(__name__, static_folder=None)
db = WiFiDatabase(DB_PATH)
processor = SignalProcessor(radius_m=100)

scanner_lock = threading.RLock()
scanner: WiFiScanner | None = None
scanner_thread: threading.Thread | None = None
scanner_error: str | None = None
is_scanning = False
current_radius = 100


def scanner_worker() -> None:
    """Run the authorized Beacon-only scanner in a background thread."""
    global is_scanning, scanner_error
    try:
        active_scanner = scanner
        if active_scanner is None:
            raise RuntimeError("Scanner was not initialized")
        active_scanner.start_scanning(duration=0)
    except Exception as exc:  # surfaced through /api/status for diagnosis
        scanner_error = f"Scanner error: {exc}"
    finally:
        with scanner_lock:
            is_scanning = False


def valid_radius(value: Any) -> bool:
    # bool is a subclass of int, so reject it explicitly.
    return isinstance(value, int) and not isinstance(value, bool) and value in ALLOWED_RADII


@app.get("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.get("/<path:filename>")
def web_assets(filename: str):
    if filename not in {"style.css", "script.js"}:
        return jsonify({"error": "Not found"}), 404
    return send_from_directory(WEB_DIR, filename)


@app.get("/api/status")
def status():
    with scanner_lock:
        return jsonify({
            "is_scanning": is_scanning,
            "radius_m": current_radius,
            "scanner_error": scanner_error,
        })


@app.get("/api/devices")
def devices():
    radius = request.args.get("radius", default=current_radius, type=int)
    if radius not in ALLOWED_RADII:
        return jsonify({"error": "radius must be 50, 100, or 150"}), 400

    rows = processor.summary()
    visible = [
        row for row in rows
        if row["estimated_distance_m"] is None or row["estimated_distance_m"] <= radius
    ]
    return jsonify({
        "total_aps": len(rows),
        "within_estimated_radius": sum(
            1 for row in rows
            if row["estimated_distance_m"] is not None
            and row["estimated_distance_m"] <= radius
        ),
        "radius_m": radius,
        "is_scanning": is_scanning,
        "scanner_error": scanner_error,
        "devices": [{
            "bssid": row["bssid"],
            "ssid": row["ssid"],
            "rssi": row["median_rssi"],
            "distance_m": row["estimated_distance_m"],
            "last_seen": row["last_seen"],
        } for row in visible],
    })


@app.post("/api/config")
def configure():
    global current_radius
    payload = request.get_json(silent=True) or {}
    radius = payload.get("radius")
    if not valid_radius(radius):
        return jsonify({"error": "radius must be 50, 100, or 150"}), 400

    with scanner_lock:
        current_radius = radius
        processor.radius_m = radius
    return jsonify({"status": "updated", "radius_m": current_radius})


@app.post("/api/start")
def start():
    global scanner, scanner_thread, is_scanning, scanner_error, current_radius
    payload = request.get_json(silent=True) or {}
    radius = payload.get("radius", current_radius)
    if not valid_radius(radius):
        return jsonify({"error": "radius must be 50, 100, or 150"}), 400

    interface = os.environ.get("WIFI_MONITOR_INTERFACE", "").strip()
    if not interface:
        return jsonify({
            "error": (
                "ยังไม่ได้กำหนด WIFI_MONITOR_INTERFACE เป็นชื่อ Monitor Mode "
                "interface ที่ระบบเตรียมไว้แล้ว"
            )
        }), 400

    with scanner_lock:
        if is_scanning:
            return jsonify({"status": "already_running", "is_scanning": True})

        current_radius = radius
        processor.radius_m = radius
        scanner_error = None
        scanner = WiFiScanner(interface, processor, db)
        is_scanning = True
        scanner_thread = threading.Thread(target=scanner_worker, daemon=True)
        scanner_thread.start()

    return jsonify({
        "status": "started",
        "is_scanning": True,
        "message": "เริ่มรับ Beacon frames แล้ว",
    })


@app.post("/api/stop")
def stop():
    global is_scanning
    with scanner_lock:
        if scanner is not None:
            scanner.stop()
        is_scanning = False
    return jsonify({"status": "stopped", "is_scanning": False})


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "absolute-darkgpt-6767"})


if __name__ == "__main__":
    # Render supplies PORT. Bind to 0.0.0.0 so its router can reach the service.
    host = os.environ.get("WEB_HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", os.environ.get("WEB_PORT", "5000")))
    app.run(host=host, port=port, debug=False, threaded=True)
    
