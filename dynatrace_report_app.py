import base64
from pathlib import Path
import requests
import urllib3
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow requests from frontend


def capture_screenshot(
        url: str,
        out_file: Path,
        viewport_width: int = 1550,
        viewport_height: int = 850,
        device_scale_factor: float = 1.0,
        extra_wait_sec: float = 10.0,
        user_agent: str | None = None,
        timeout_ms: int = 60_000,
) -> Path:
    from playwright.sync_api import sync_playwright

    out_file.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context_args = {
            "viewport": {"width": viewport_width, "height": viewport_height},
            "device_scale_factor": device_scale_factor,
            "timezone_id": "UTC",
        }

        if user_agent:
            context_args["user_agent"] = user_agent

        context = browser.new_context(**context_args)
        page = context.new_page()

        page.goto(url, wait_until="load", timeout=timeout_ms)

        # Give dynamic dashboards/charts a moment to render
        page.wait_for_timeout(int(extra_wait_sec * 1000))
        page.screenshot(path=str(out_file), full_page=True)
        context.close()
        browser.close()

    return out_file

def file_to_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")

def https_post(url: str, json_payload: dict, timeout_sec: int = 60):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    resp = requests.post(url, json=json_payload, timeout=timeout_sec, verify=False)
    resp.raise_for_status()
    return resp

def capture_upload_snapshot(report_type, dashboard_url, flow_url):
    # 1) Capture screenshot
    out_path = Path(f"dt_dashboard_{report_type}.png")
    print(f"[1/3] Capturing full-page screenshot from Dynatrace Dashboard - {report_type}")
    capture_screenshot(
        url=dashboard_url,
        out_file=out_path
    )
    print(f"Saved screenshot -> {out_path.resolve()}")

    # 2) Convert to Base64 (or Data URL)
    print("[2/3] Converting image to Base64…")
    b64 = file_to_base64(out_path)

    # 3) Build payload and POST to Power Automate
    payload = {
        "data": b64,
    }

    print(f"[3/3] POSTing to Flow URL…")
    try:
        resp = https_post(flow_url, payload)
    except Exception as e:
        raise Exception(f"ERROR: POST failed with error: {e}")

    print("Flow response status:", resp.status_code)


@app.route('/v1/screengrab/dynatrace/dashboard', methods=['POST'])
def main():
    data = request.get_json()
    dashboard_type = data.get('type') or "status_report"
    dashboard_url = data.get('dashboard_url')
    flow_url = data.get('flow_url')
    if dashboard_url is None or len(dashboard_url) < 10:
        return jsonify({'result': 'Missing or invalid dashboard URL in the request to capture the snapshot!'}), 400
    if flow_url is None or len(flow_url) < 10:
        return jsonify({'result': 'Missing or invalid flow URL in the request to upload the snapshot!'}), 400

    try:
        capture_upload_snapshot(
            report_type=dashboard_type,
            dashboard_url=dashboard_url, flow_url=flow_url)
    except Exception as e:
        return jsonify({'result': f'Error while generating the snapshot - {e}!'}), 500

    return jsonify({'result': f'Successfully generated snapshot of "{dashboard_type}" dashboard!'}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
