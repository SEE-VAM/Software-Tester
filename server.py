import os
import sys
import json
import time
import queue
import threading
import asyncio
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, Response, send_from_directory

from crawler_engine import AutoCrawlerEngine

app = Flask(__name__, static_folder="web", static_url_path="")

BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Global event queue for Server-Sent Events (SSE)
event_queue = queue.Queue()
active_crawler = None
crawler_thread = None

test_state = {
    "is_running": False,
    "is_paused": False,
    "target_url": "http://localhost:8080",
    "metrics": {"total": 0, "passed": 0, "failed": 0},
    "logs": [],
    "bugs": [],
    "screens": {},
    "scenarios": {}
}

def broadcast_event(event):
    event_queue.put(event)
    
    # Update local state cache
    ev_type = event.get("type")
    if ev_type == "log":
        test_state["logs"].append(event)
        if len(test_state["logs"]) > 200:
            test_state["logs"].pop(0)
    elif ev_type == "metrics":
        test_state["metrics"]["total"] = event.get("total", 0)
        test_state["metrics"]["passed"] = event.get("passed", 0)
        test_state["metrics"]["failed"] = event.get("failed", 0)
    elif ev_type == "bug_found":
        test_state["bugs"].append(event.get("bug"))
    elif ev_type == "screen_changed":
        screen_name = event.get("screen")
        test_state["screens"][screen_name] = event.get("status")
    elif ev_type == "scenario_updated":
        s_name = event.get("name")
        test_state["scenarios"][s_name] = {
            "status": event.get("status"),
            "details": event.get("details")
        }

@app.route("/")
def index():
    return send_from_directory("web", "index.html")

@app.route("/screenshots/<filename>")
def get_screenshot(filename):
    return send_from_directory(str(SCREENSHOTS_DIR), filename)

@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify({
        "status": "running" if test_state["is_running"] else "idle",
        "state": test_state
    })

def run_crawler_worker(target_url, headless=False):
    global active_crawler
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    active_crawler = AutoCrawlerEngine(
        target_url=target_url,
        headless=headless,
        event_callback=broadcast_event
    )
    test_state["is_running"] = True
    broadcast_event({"type": "status_changed", "status": "running"})
    
    try:
        loop.run_until_complete(active_crawler.run_crawler())
    except Exception as e:
        broadcast_event({"type": "log", "timestamp": datetime.now().strftime("%H:%M:%S"), "message": f"Fatal Crawler Error: {e}", "status": "error"})
    finally:
        test_state["is_running"] = False
        broadcast_event({"type": "status_changed", "status": "completed"})
        loop.close()

@app.route("/api/start", methods=["POST"])
def start_test():
    global crawler_thread
    if test_state["is_running"]:
        return jsonify({"error": "Test is already running"}), 400

    data = request.json or {}
    target_url = data.get("target_url", "http://localhost:8080").strip()
    headless = data.get("headless", False)

    test_state["target_url"] = target_url
    test_state["metrics"] = {"total": 0, "passed": 0, "failed": 0}
    test_state["logs"] = []
    test_state["bugs"] = []
    test_state["screens"] = {}
    test_state["scenarios"] = {}

    crawler_thread = threading.Thread(target=run_crawler_worker, args=(target_url, headless), daemon=True)
    crawler_thread.start()

    return jsonify({"message": f"AutoQA Suite started on {target_url}", "status": "started"})

@app.route("/api/stop", methods=["POST"])
def stop_test():
    global active_crawler
    if active_crawler:
        active_crawler.is_running = False
        test_state["is_running"] = False
        broadcast_event({"type": "log", "timestamp": datetime.now().strftime("%H:%M:%S"), "message": "Test execution stopped by user.", "status": "error"})
        broadcast_event({"type": "status_changed", "status": "stopped"})
        return jsonify({"message": "Test stopped."})
    return jsonify({"message": "No active test found."})

@app.route("/api/pause", methods=["POST"])
def pause_test():
    global active_crawler
    if active_crawler:
        active_crawler.is_paused = not active_crawler.is_paused
        test_state["is_paused"] = active_crawler.is_paused
        msg = "Test paused by user." if active_crawler.is_paused else "Test resumed."
        broadcast_event({"type": "log", "timestamp": datetime.now().strftime("%H:%M:%S"), "message": msg, "status": "info"})
        return jsonify({"is_paused": active_crawler.is_paused, "message": msg})
    return jsonify({"message": "No active test found."})

@app.route("/api/events")
def sse_events():
    def event_stream():
        # First push current state snapshot
        yield f"data: {json.dumps({'type': 'init', 'state': test_state})}\n\n"
        while True:
            try:
                event = event_queue.get(timeout=20)
                yield f"data: {json.dumps(event)}\n\n"
            except queue.Empty:
                # Keep alive ping
                yield f": keep-alive\n\n"
    
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/api/export-report", methods=["GET"])
def export_report():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = REPORTS_DIR / f"test_report_{timestamp}.html"
    
    bugs_html = ""
    for bug in test_state["bugs"]:
        shot_html = f'<img src="/screenshots/{bug["screenshot"]}" style="max-width:300px;border-radius:6px;margin-top:8px;border:1px solid #dc2626;" />' if bug.get("screenshot") else ""
        bugs_html += f"""
        <div style="background:#fee2e2;border:1px solid #ef4444;padding:12px;border-radius:8px;margin-bottom:12px;">
            <strong style="color:#b91c1c;">[{bug['id']}] {bug['title']}</strong>
            <p style="font-size:12px;color:#7f1d1d;margin:4px 0;"><strong>Selector:</strong> <code>{bug['selector']}</code></p>
            <p style="font-size:12px;color:#991b1b;background:#fecaca;padding:8px;border-radius:4px;font-family:monospace;">{bug['error']}</p>
            {shot_html}
        </div>
        """

        scenarios_html = ""
        for s_name, s_data in test_state.get("scenarios", {}).items():
            sc_color = "#059669" if s_data.get("status") == "Passed" else ("#d97706" if s_data.get("status") == "Testing" else "#dc2626")
            sc_bg = "#ecfdf5" if s_data.get("status") == "Passed" else "#fef2f2"
            scenarios_html += f"""
            <div style="background:{sc_bg};border:1px solid {sc_color};padding:10px 14px;border-radius:8px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <strong>{s_name}</strong>
                    <p style="font-size:12px;color:#475569;margin-top:2px;">{s_data.get('details', '')}</p>
                </div>
                <span style="font-weight:bold;color:{sc_color};padding:4px 8px;border-radius:4px;font-size:12px;text-transform:uppercase;">{s_data.get('status')}</span>
            </div>
            """

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AutoQA POS Test Audit Report - {timestamp}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #1e293b; padding: 40px; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 32px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); }}
        .header {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 16px; margin-bottom: 24px; }}
        .stats {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
        .card {{ padding: 16px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center; }}
        .card-val {{ font-size: 28px; font-weight: bold; }}
        .card-lbl {{ font-size: 12px; color: #64748b; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🛒 AutoQA POS Test Audit Report</h2>
            <p>Target Application: <strong>{test_state['target_url']}</strong></p>
            <p style="color:#64748b;font-size:12px;">Generated at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        <div class="stats">
            <div class="card"><div class="card-val">{test_state['metrics']['total']}</div><div class="card-lbl">Total Tested Elements</div></div>
            <div class="card" style="border-color:#10b981;"><div class="card-val" style="color:#059669;">{test_state['metrics']['passed']}</div><div class="card-lbl">Passed (Verified OK)</div></div>
            <div class="card" style="border-color:#ef4444;"><div class="card-val" style="color:#dc2626;">{test_state['metrics']['failed']}</div><div class="card-lbl">Issues / Bugs Found</div></div>
        </div>

        <h3>🎯 Business Transaction Flow Tests:</h3>
        <div style="margin-bottom:24px;">
            {scenarios_html or '<p style="color:#64748b;">No scenario transactions recorded.</p>'}
        </div>

        <h3>🐛 Captured Issues & Errors:</h3>
        {bugs_html or '<p style="color:#059669;font-weight:bold;">🎉 No errors encountered! All tested elements passed.</p>'}
    </div>
</body>
</html>"""

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    return send_from_directory(str(REPORTS_DIR), report_file.name)

if __name__ == "__main__":
    print("==================================================================")
    print(" 🤖 AutoQA Robot - Automated POS Testing Engine")
    print(" 🚀 Dashboard running at: http://localhost:9090")
    print("==================================================================")
    app.run(host="0.0.0.0", port=9090, debug=False)
