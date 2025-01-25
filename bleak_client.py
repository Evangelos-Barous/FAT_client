# import asyncio
# from bleak import BleakScanner
# from bleak import BleakClient
# from functools import partial

# address_list = []

# # This can be where the parsing of the data is done to send to the frontend or to
# # calculate the user performance score and append to the list of all the data points for
# # the post workout data stuff (like velocity graphs)
# async def notification_handler(sender, data: bytearray):
#     print(f"Notification from {sender.address}: {data.decode('utf-8')}") 

# async def main():
#     devices = await BleakScanner.discover()
#     for device in devices:
#         print(device)

#     # Start receiving notifications once
#     # Notification handler is the notification callback that will be written that takes in the data
#     # and parses it/sends it to the UI
#         # await client.start_notify(CHAR_ACC_UUID, notification_handler)
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
#                     for i in range(10000):
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

from bleak import BleakClient, BleakScanner

device_connected_count = 0
addresses = ["C8:2E:18:DE:51:F2"]
uuids = []

async def connect_to_device(
    lock: asyncio.Lock,
    #by_address: bool,
    #macos_use_bdaddr: bool,
    name_or_address: str,
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
    global device_connected_count
    print("starting %s task", name_or_address)

    try:
        async with contextlib.AsyncExitStack() as stack:

            # Trying to establish a connection to two devices at the same time
            # can cause errors, so use a lock to avoid this.
            async with lock:
                print("scanning for %s", name_or_address)

                device = await BleakScanner.find_device_by_address(
                        name_or_address, macos=dict(use_bdaddr=True)
                )

                # if by_address:
                #     device = await BleakScanner.find_device_by_address(
                #         name_or_address, macos=dict(use_bdaddr=macos_use_bdaddr)
                #     )
                # else:
                #     device = await BleakScanner.find_device_by_name(name_or_address)

                print("stopped scanning for %s", name_or_address)

                if device is None:
                    logging.error("%s not found", name_or_address)
                    return

                client = BleakClient(device)

                print("connecting to %s", name_or_address)

                await stack.enter_async_context(client)

                print("connected to %s", name_or_address)
                device_connected_count += 1

                # This will be called immediately before client.__aexit__ when
                # the stack context manager exits.
                stack.callback(logging.info, "disconnecting from %s", name_or_address)

            # The lock is released here. The device is still connected and the
            # Bluetooth adapter is now free to scan and connect another device
            # without disconnecting this one.

            def callback(_, data):
                logging.info("%s received %r", name_or_address, data)

            while device_connected_count < 1:
                await asyncio.sleep(0.001)
            
            print("All devices connected")
            # await client.start_notify(notify_uuid, callback)
            # while rep_count < 12:
            #    do nothing, keeping the start notify running
            await asyncio.sleep(10.0)
            # await client.stop_notify(notify_uuid)

        # The stack context manager exits here, triggering disconnection.

        logging.info("disconnected from %s", name_or_address)

    except Exception:
        logging.exception("error with %s", name_or_address)


async def main(
    #by_address: bool,
    #macos_use_bdaddr: bool,
    device_addresses: Iterable[str],
    #uuids: Iterable[str],
):
    lock = asyncio.Lock()

    await asyncio.gather(
        *(
            connect_to_device(lock, address)#by_address, macos_use_bdaddr, address)#, uuid)
            for address in device_addresses
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

    asyncio.run(
        main(
            # args.by_address,
            # args.macos_use_bdaddr,
            addresses,
            #(args.uuid1, args.uuid2),
        )
    )