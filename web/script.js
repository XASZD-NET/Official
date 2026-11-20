const $ = (id) => document.getElementById(id);
const state = { scanning: false, timer: null, busy: false };

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
  return payload;
}

function setMessage(message, isError = false) {
  $("message").textContent = message;
  $("message").classList.toggle("error", isError);
}

function setScanning(active) {
  state.scanning = active;
  $("startBtn").disabled = active;
  $("stopBtn").disabled = !active;
  $("statusValue").textContent = active ? "ON" : "OFF";
  $("statusValue").classList.toggle("on", active);
  $("scanState").textContent = active ? "กำลังสแกนแบบ Passive" : "ยังไม่เริ่มสแกน";
  $("scanPulse").parentElement.classList.toggle("active", active);
  if (state.timer) clearInterval(state.timer);
  state.timer = active ? setInterval(refresh, 2000) : null;
}

function safeText(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  })[c]);
}

function renderDevices(devices) {
  $("tableCount").textContent = `${devices.length} รายการ`;
  if (!devices.length) {
    $("deviceRows").innerHTML = '<tr><td colspan="5" class="empty">ยังไม่พบ Access Point หรือยังไม่มีข้อมูล RSSI</td></tr>';
    return;
  }
  $("deviceRows").innerHTML = devices.map(d => `
    <tr>
      <td><span class="ssid">${safeText(d.ssid || "Hidden network")}</span><span class="subtle">802.11 Beacon</span></td>
      <td class="mac">${safeText(d.bssid)}</td>
      <td class="rssi">${d.rssi == null ? "—" : `${Number(d.rssi).toFixed(0)} dBm`}</td>
      <td class="distance">${d.distance_m == null ? "ไม่สามารถประเมิน" : `~${Number(d.distance_m).toFixed(1)} m`}</td>
      <td>${safeText(d.last_seen || "—")}</td>
    </tr>`).join("");
}

async function refresh() {
  if (state.busy) return;
  state.busy = true;
  try {
    const radius = Number($("radiusSelect").value);
    const data = await api(`/api/devices?radius=${radius}`);
    $("apCount").textContent = data.total_aps;
    $("withinCount").textContent = data.within_estimated_radius;
    $("radiusValue").textContent = data.radius_m;
    $("lastUpdated").textContent = `อัปเดต ${new Date().toLocaleTimeString("th-TH")}`;
    renderDevices(data.devices);
    if (data.scanner_error) setMessage(data.scanner_error, true);
    else setMessage("เชื่อมต่อเซิร์ฟเวอร์แล้ว");
  } catch (error) {
    setMessage(`เชื่อมต่อ API ไม่สำเร็จ: ${error.message}`, true);
  } finally {
    state.busy = false;
  }
}

$("startBtn").addEventListener("click", async () => {
  try {
    const data = await api("/api/start", { method: "POST", body: JSON.stringify({ radius: Number($("radiusSelect").value) }) });
    setScanning(Boolean(data.is_scanning));
    setMessage(data.message || "ส่งคำสั่งเริ่มสแกนแล้ว");
    await refresh();
  } catch (error) { setMessage(error.message, true); }
});

$("stopBtn").addEventListener("click", async () => {
  try {
    await api("/api/stop", { method: "POST", body: "{}" });
    setScanning(false);
    setMessage("หยุดการสแกนแล้ว");
    await refresh();
  } catch (error) { setMessage(error.message, true); }
});

$("radiusSelect").addEventListener("change", async () => {
  $("radiusValue").textContent = $("radiusSelect").value;
  try {
    await api("/api/config", { method: "POST", body: JSON.stringify({ radius: Number($("radiusSelect").value) }) });
    await refresh();
  } catch (error) { setMessage(error.message, true); }
});

(async function init() {
  try {
    const status = await api("/api/status");
    $("connectionDot").parentElement.classList.add("online");
    $("connectionText").textContent = "เซิร์ฟเวอร์ออนไลน์";
    $("radiusSelect").value = String(status.radius_m);
    $("radiusValue").textContent = status.radius_m;
    setScanning(status.is_scanning);
    await refresh();
  } catch (error) {
    $("connectionText").textContent = "เซิร์ฟเวอร์ออฟไลน์";
    setMessage(`เริ่มต้นไม่สำเร็จ: ${error.message}`, true);
  }
})();
