from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import subprocess
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000"], async_mode="threading")

print("Flask backend is running...")
DEVICE_FILE_MAP = {
    "WristDevice": "wristData.txt", #wrisDataGood.txt for demo
    "BackDevice": "backData.txt", #backDataGood.txt for demo
    "BicepDevice": "bicepData.txt" #bicepDataErrors.txt for demo
}

GOOD_DEVICE_FILE_MAP = {
    "WristDevice": "wristDataGood.txt",
    "BackDevice": "backDataGood.txt",
    "BicepDevice": "bicepDataGood.txt"
}

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route("/")
def index():
    return "Flask backend is running!"

@socketio.on("ble_data")
def handle_ble_data(data):
    print("Received BLE data:", data)
    # Forward to React frontend
    socketio.emit("ble_data", data)
    print("Data sent to React frontend:", data)

@socketio.on("get_device_data")
def handle_get_device_data(data):
    device = data.get("device")
    use_good_data = data.get("good", False)
    filename = (GOOD_DEVICE_FILE_MAP if use_good_data else DEVICE_FILE_MAP).get(device)
    print(f"Request for {'good ' if use_good_data else ''}device data: {device}")

    if not filename or not os.path.exists(filename):
        socketio.emit("device_data", {"device": device, "data": [], "error": "File not found", "good": use_good_data})
        return

    try:
        parsed_data = []

        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    if device == "WristDevice":
                        x = float(line[0:5])
                        y = float(line[5:10])
                        z = float(line[10:16])
                        code = line[-2:]
                    else: # For BackDevice and BicepDevice
                        x = float(line[0:5])
                        y = float(line[5:10])
                        z = float(line[10:15])
                        code = line[-1]

                    zero_count = code.count('0')
                    code_length = len(code)
                    performance_score = zero_count / code_length if code_length > 0 else 0

                    parsed_data.append({
                        "xData": x,
                        "yData": y,
                        "zData": z,
                        "code": code,
                        "score": performance_score
                    })
                except ValueError as e:
                    print(f"Skipping malformed line: {line} ({e})")

        socketio.emit("device_data", {"device": device, "data": parsed_data, "good": use_good_data})
        print(f"Sent {len(parsed_data)} parsed values for {device}{' (good)' if use_good_data else ''}")
    except Exception as e:
        socketio.emit("device_data", {"device": device, "data": [], "error": str(e), "good": use_good_data})
        print(f"Error reading file for {device}: {e}")

@app.route("/run-script", methods=["GET", "POST"])
def run_script():
    try:    
        print("Trying to run script")
        result = subprocess.Popen(
            ["python", "ble.py", "--run"],
        )
        print("Script output:", result.stdout)

        return jsonify({
            "message": "Script executed successfully!",
            "output": result.stdout
        }), 200

    except subprocess.CalledProcessError as e:
        print("Script failed:", e.stderr)
        return jsonify({
            "error": "Script failed",
            "details": e.stderr
        }), 500

    except Exception as e:
        print("Unexpected error:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5050, debug=True)