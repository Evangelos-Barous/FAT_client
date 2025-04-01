import asyncio
import logging
import time
import threading
import contextlib
from flask import Flask
from flask_socketio import SocketIO
from bleak import BleakClient, BleakScanner
from typing import Iterable
import eventlet
import os

eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Notification handlers
async def notification_handler_1(sender, data: bytearray):
    global back_error
    msg = data.decode("utf-8", "ignore").strip()
    error_code = msg[-1] if msg[-1].isdigit() else None
    timestamp = f"{msg} at {time.time() * 1000}"
    print(f"BackDevice: {timestamp}")
    with open("backData.txt", "a") as file:
        file.write(msg + "\n")
    socketio.emit("ble_data", {"device": "BackDevice", "errorCode": error_code})
    back_error = 1

async def notification_handler_2(sender, data: bytearray):
    global wrist_error
    msg = data.decode("utf-8", "ignore").strip()
    error_code = msg[-1] if msg[-1].isdigit() else None
    timestamp = f"{msg} at {time.time() * 1000}"
    print(f"WristDevice: {timestamp}")
    with open("wristData.txt", "a") as file:
        file.write(msg + "\n")
    socketio.emit("ble_data", {"device": "WristDevice", "errorCode": error_code})
    wrist_error = 1

async def notification_handler_3(sender, data: bytearray):
    global bicep_error
    msg = data.decode("utf-8", "ignore").strip()
    error_code = msg[-1] if msg[-1].isdigit() else None
    timestamp = f"At {time.time() * 1000} {msg}"
    print(f"BicepDevice: {timestamp}")
    with open("bicepData.txt", "a") as file:
        file.write(msg + "\n")
    socketio.emit("ble_data", {"device": "BicepDevice", "errorCode": error_code})
    bicep_error = 1

# Device config
DEVICE_CONFIGS = [
    {"name": "BackDevice", "handler": notification_handler_1},
    {"name": "WristDevice", "handler": notification_handler_2},
    {"name": "BicepDevice", "handler": notification_handler_3},
]


async def connect_to_device(
        lock: asyncio.Lock,
        name_or_address: str,
        callback,
):
    global devices_connected
    print("starting %s task", name_or_address)

    try:
        async with contextlib.AsyncExitStack() as stack:
            async with lock:
                print("scanning for %s", name_or_address)

                device = await BleakScanner.find_device_by_name(name_or_address)

                print("stopped scanning for %s", name_or_address)

                if device is None:
                    logging.error("%s not found", name_or_address)
                    return
                else:
                    print("Found %s", name_or_address)

                async with BleakClient(device) as client:
                    for service in client.services:
                        print("[Service] %s", service)
            
                        for char in service.characteristics:
                            print(char.properties)
                            if "read" in char.properties:
                                try:
                                    value = await client.read_gatt_char(char.uuid)
                                    extra = f", Value: {value}"
                                except Exception as e:
                                    extra = f", Error: {e}"
                            else:
                                extra = ""
            
                            if "write-without-response" in char.properties:
                                extra += f", Max write w/o rsp size: {char.max_write_without_response_size}"
            
                            print(
                                "  [Characteristic] %s (%s)%s",
                                char,
                                ",".join(char.properties),
                                extra,
                            )

                print("connecting to %s", name_or_address)

                await stack.enter_async_context(client)

                print("connected to %s", name_or_address)

                stack.callback(logging.info, "disconnecting from %s", name_or_address)

            if await client.is_connected():
                devices_connected += 1
                while devices_connected < 3:
                    print("Sleeping")
                    await asyncio.sleep(0.01)
                print("Telling server to start")
                await client.write_gatt_char('55aa3bf2-6768-4c6e-97d9-fa443755401f', b"\x01", response=True)
                print("We are trying to notify")
                await client.start_notify('beb5483e-36e1-4688-b7f5-ea07361b26a8', callback)
                while True:
                    await asyncio.sleep(0.01)
                print("Notify should have ran")
            await asyncio.sleep(10.0)

        logging.info("disconnected from %s", name_or_address)

    except Exception:
        logging.exception("error with %s", name_or_address)


devices_connected = 0
names = ["BackDevice", "WristDevice", "BicepDevice"]
uuids = []
callbacks = [notification_handler_1, notification_handler_2, notification_handler_3]

async def main_ble_loop(
    names: Iterable[str],
    callbacks,
):
    lock = asyncio.Lock()
    await asyncio.gather(
        *(
        connect_to_device(lock, name, callback)
        for name, callback in zip(names, callbacks)
    )
    )

def start_ble_thread():
    loop = asyncio.new_event_loop()
    threading.Thread(target=lambda: loop.run_until_complete(main_ble_loop(names, callbacks)), daemon=True).start()

@app.route("/")
def index():
    return "BLE Flask WebSocket server is running."

@socketio.on("connect")
def on_connect():
    print("Client connected")

if __name__ == "__main__":
    file_path = 'bicepData.txt'
    if os.path.exists(file_path):
        os.remove(file_path)

    file_path = 'wristData.txt'
    if os.path.exists(file_path):
        os.remove(file_path)

    file_path = 'backData.txt'
    if os.path.exists(file_path):
        os.remove(file_path)
    start_ble_thread()
    socketio.run(app, host="127.0.0.1", port=5000)
