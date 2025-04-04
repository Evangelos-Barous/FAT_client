from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import subprocess

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000"], async_mode="threading")

print("Flask backend is running...")

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

@app.route("/run-script", methods=["GET", "POST"])
def run_script():
    # if request.method == "GET":
    #     return jsonify({"message": "Send a POST to run the script."})
    
    # if request.method == 'POST':
    #     return '', 204
    try:    
        print("Trying to run script")
        result = subprocess.Popen(
            ["python", "ble.py", "--run"],
            # capture_output=True,
            # text=True,
            # check=True
            # stdout=open("script_output.txt", "w"),
            # stderr=subprocess.STDOUT
        )
        print("Script output:", result.stdout)

        with open("script_output.txt", "w") as f:
            f.write(result.stdout)

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
