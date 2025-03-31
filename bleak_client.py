# import asyncio
# from bleak import BleakScanner
# from bleak import BleakClient
# from functools import partial

# address_list = []

# # This can be where the parsing of the data is done to send to the frontend or to
# # calculate the user performance score and append to the list of all the data points for
# # the post workout data stuff (like velocity graphs)
# async def notification_handler(sender, data: bytearray):
#     print(f"Notification from {data}: {sender}: {data.decode('utf-8', 'ignore')}")

# async def main():
#     devices = await BleakScanner.discover()
#     for device in devices:
#         print(device)

#     # Start receiving notifications once
#     # Notification handler is the notification callback that will be written that takes in the data
#     # and parses it/sends it to the UI
#         # await client.start_notify('beb5483e-36e1-4688-b7f5-ea07361b26a8', notification_handler)
#         # await client.start_notify(
#             # char_specifier, partial(my_notification_callback_with_client_input, client)
#         # )
#         # print("Started notifications...")

#     try:
#         async with BleakClient("C8:2E:18:DE:51:F2") as client:
#             if await client.is_connected():
#                 try:
#                     # Pair with the device (distinct from just connecting)
#                     await client.pair()
#                     await client.start_notify('beb5483e-36e1-4688-b7f5-ea07361b26a8', notification_handler)
#                     for i in range(5):
#                         print("We are still connected")
#                 except Exception as e:
#                     print(e)
#             else:
#                 print("Failed to connect to device")
#     except Exception as e:
#         print(e) 
# asyncio.run(main())

import argparse
import asyncio
import contextlib
import logging
from typing import Iterable
import time
import os

from bleak import BleakClient, BleakScanner

async def notification_handler_1(sender, data: bytearray):
    global wrist_error
    #await asyncio.sleep(0)
    #data1 = int.from_bytes(data, "little")
    print(f"Notification from callback 1: {sender}: {data.decode('utf-8', 'ignore')} at {time.time() * 1000}")
    with open("backData.txt", "a") as file:
        file.write(data.decode('utf-8', 'ignore') + "\n")
    wrist_error = 1

async def notification_handler_2(sender, data: bytearray):
    global wrist_error
    #await asyncio.sleep(0)
    #data2 = int.from_bytes(data, "little")
    print(f"Notification from callback 2: {sender}: {data.decode('utf-8', 'ignore')} at {time.time() * 1000}")
    with open("wristData.txt", "a") as file:
        file.write(data.decode('utf-8', 'ignore') + "\n")
    wrist_error = 1

async def notification_handler_3(sender, data: bytearray):
    global wrist_error
    #await asyncio.sleep(0)
    #data2 = int.from_bytes(data, "little")
    print(f"Notification from callback 3: {sender}: {data.decode('utf-8', 'ignore')} at {time.time() * 1000}")
    with open("bicepData.txt", "a") as file:
        file.write(data.decode('utf-8', 'ignore') + "\n")
    wrist_error = 1

async def connect_to_device(
    lock: asyncio.Lock,
    #by_address: bool,
    #macos_use_bdaddr: bool,
    name_or_address: str,
    callback, 
    #notify_uuid: str,
):
    """
    Scan and connect to a device then print notifications for 10 seconds before
    disconnecting.

    Args:
        lock:
            The same lock must be passed to all calls to this function.
        by_address:
            If true, treat *name_or_address* as an address, otherwise treat
            it as a name.
        macos_use_bdaddr:
            If true, enable hack to allow use of Bluetooth address instead of
            UUID on macOS.
        name_or_address:
            The Bluetooth address/UUID of the device to connect to.
        notify_uuid:
            The UUID of a characteristic that supports notifications.
    """
    global devices_connected
    print("starting %s task", name_or_address)

    try:
        async with contextlib.AsyncExitStack() as stack:

            # Trying to establish a connection to two devices at the same time
            # can cause errors, so use a lock to avoid this.
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

                # This will be called immediately before client.__aexit__ when
                # the stack context manager exits.
                stack.callback(logging.info, "disconnecting from %s", name_or_address)

            # The lock is released here. The device is still connected and the
            # Bluetooth adapter is now free to scan and connect another device
            # without disconnecting this one.

            if await client.is_connected():
                devices_connected += 1
                while devices_connected < 1:
                    print("Sleeping")
                    await asyncio.sleep(0.01)
                print("Telling server to start")
                await client.write_gatt_char('55aa3bf2-6768-4c6e-97d9-fa443755401f', b"\x01", response=False)
                print("We are trying to notify")
                await client.start_notify('beb5483e-36e1-4688-b7f5-ea07361b26a8', callback)
                while True:
                    await asyncio.sleep(0.01)
                    #print("Hello")
                    #await client.start_notify('beb5483e-36e1-4688-b7f5-ea07361b26a8', callback)
                    # if (name_or_address == "WristDevice"): 
                    #     await client.write_gatt_char('2e2e3152-975f-46b4-83bd-d1311a25b1c9', b"\x01", response=False)
                print("Notify should have ran")
            # while rep_count < 12:
            #    do nothing, keeping the start notify running
            await asyncio.sleep(10.0)
            # await client.stop_notify(notify_uuid)

        # The stack context manager exits here, triggering disconnection.

        logging.info("disconnected from %s", name_or_address)

    except Exception:
        logging.exception("error with %s", name_or_address)

wrist_error = 0
devices_connected = 0
names = ["BackDevice"]
#names = ["BackDevice", "WristDevice"]
#names = ["BackDevice", "WristDevice", "BicepDevice"]
uuids = []
callbacks = [notification_handler_1]
#callbacks = [notification_handler_1, notification_handler_2, notification_handler_3]

async def main(
    #by_address: bool,
    #macos_use_bdaddr: bool,
    names: Iterable[str],
    callbacks,
    #uuids: Iterable[str],
):
    lock = asyncio.Lock()

    await asyncio.gather(
        *(
            connect_to_device(lock, name, callback)#by_address, macos_use_bdaddr, address)#, uuid)
            for name, callback in zip(names, callbacks)
            #for address, uuid in zip(device_addresses, uuids)
        )
    )


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()

    # parser.add_argument(
    #     "device1",
    #     metavar="<device>",
    #     help="Bluetooth name or address of first device connect to",
    # )
    # parser.add_argument(
    #     "uuid1",
    #     metavar="<uuid>",
    #     help="notification characteristic UUID on first device",
    # )
    # parser.add_argument(
    #     "device2",
    #     metavar="<device>",
    #     help="Bluetooth name or address of second device to connect to",
    # )
    # parser.add_argument(
    #     "uuid2",
    #     metavar="<uuid>",
    #     help="notification characteristic UUID on second device",
    # )

    # parser.add_argument(
    #     "--by-address",
    #     action="store_true",
    #     help="when true treat <device> args as Bluetooth address instead of name",
    # )

    # parser.add_argument(
    #     "--macos-use-bdaddr",
    #     action="store_true",
    #     help="when true use Bluetooth address instead of UUID on macOS",
    # )

    # parser.add_argument(
    #     "-d",
    #     "--debug",
    #     action="store_true",
    #     help="sets the log level to debug",
    # )

    # args = parser.parse_args()

    # log_level = logging.DEBUG if args.debug else logging.INFO
    # logging.basicConfig(
    #     level=log_level,
    #     format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s",
    # )

    file_path = 'bicepData.txt'
    if os.path.exists(file_path):
        os.remove(file_path)

    file_path = 'wristData.txt'
    if os.path.exists(file_path):
        os.remove(file_path)

    file_path = 'backData.txt'
    if os.path.exists(file_path):
        os.remove(file_path)

    asyncio.run(
        main(
            # args.by_address,
            # args.macos_use_bdaddr,
            names,
            callbacks,
            #(args.uuid1, args.uuid2),
        )
    )