from collections import deque
from statistics import median

class SignalProcessor:
    def __init__(self, radius_m=100, reference_rssi=-40, path_loss_n=2.7):
        self.radius_m = radius_m
        self.reference_rssi = reference_rssi
        self.path_loss_n = path_loss_n
        self.access_points = {}

    def estimate_distance(self, rssi):
        if rssi is None or self.path_loss_n <= 0:
            return None
        # Indicative log-distance estimate only; requires site calibration.
        return round(10 ** ((self.reference_rssi - rssi) / (10 * self.path_loss_n)), 1)

    def add_access_point(self, bssid, ssid, rssi, timestamp):
        record = self.access_points.setdefault(bssid, {
            "ssid": ssid, "history": deque(maxlen=25),
            "first_seen": timestamp, "last_seen": timestamp
        })
        if ssid and ssid != "<hidden>":
            record["ssid"] = ssid
        record["history"].append(rssi)
        record["last_seen"] = timestamp
        record["median_rssi"] = median(record["history"])
        record["estimated_distance_m"] = self.estimate_distance(record["median_rssi"])

    def summary(self):
        result = []
        for bssid, record in self.access_points.items():
            result.append({
                "bssid": bssid,
                "ssid": record["ssid"],
                "median_rssi": record.get("median_rssi"),
                "estimated_distance_m": record.get("estimated_distance_m"),
                "last_seen": record["last_seen"]
            })
        return sorted(result, key=lambda item: item["median_rssi"] or -999, reverse=True)
