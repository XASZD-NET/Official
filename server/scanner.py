from datetime import datetime, timezone
from scapy.all import AsyncSniffer
from scapy.layers.dot11 import Dot11, Dot11Beacon, Dot11Elt, RadioTap

class WiFiScanner:
    """Beacon-only receiver. Does not inspect Probe Requests or client station addresses."""
    def __init__(self, interface, processor, database):
        self.interface = interface
        self.processor = processor
        self.database = database
        self.running = False
        self._sniffer = None

    @staticmethod
    def _ssid(packet):
        element = packet.getlayer(Dot11Elt)
        while element is not None:
            if getattr(element, "ID", None) == 0:
                value = bytes(getattr(element, "info", b"")).decode("utf-8", errors="replace")
                return value or "<hidden>"
            element = element.payload.getlayer(Dot11Elt)
        return "<hidden>"

    def _handle(self, packet):
        if not self.running or not packet.haslayer(Dot11Beacon) or not packet.haslayer(Dot11):
            return
        bssid = packet[Dot11].addr2
        if not bssid:
            return
        rssi = getattr(packet[RadioTap], "dBm_AntSignal", None) if packet.haslayer(RadioTap) else None
        if not isinstance(rssi, (int, float)):
            return
        ssid = self._ssid(packet)
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.processor.add_access_point(bssid, ssid, int(rssi), timestamp)
        self.database.save_access_point(bssid, ssid, int(rssi), timestamp)

    def start_scanning(self, duration=0):
        self.running = True
        self._sniffer = AsyncSniffer(
            iface=self.interface, prn=self._handle, store=False,
            timeout=None if duration == 0 else duration
        )
        self._sniffer.start()
        self._sniffer.join()
        self.running = False

def stop(self):
    sniffer = getattr(self, "sniffer", None)

    if sniffer is not None:
        try:
            sniffer.stop(join=False)

            thread = getattr(sniffer, "thread", None)
            if thread is not None and thread.is_alive():
                thread.join(timeout=1)

        except Exception as exc:
            print(f"Scanner stop error: {exc}")
