import asyncio
from bleak import BleakScanner
from bleak import BleakClient
from functools import partial

address_list = []

# This can be where the parsing of the data is done to send to the frontend or to
# calculate the user performance score and append to the list of all the data points for
# the post workout data stuff (like velocity graphs)
async def notification_handler(sender, data: bytearray):
    print(f"Notification from {sender.address}: {data.decode('utf-8')}") 

async def main():
    devices = await BleakScanner.discover()
    for device in devices:
        print(device)

    # Start receiving notifications once
    # Notification handler is the notification callback that will be written that takes in the data
    # and parses it/sends it to the UI
        # await client.start_notify(CHAR_ACC_UUID, notification_handler)
        # await client.start_notify(
            # char_specifier, partial(my_notification_callback_with_client_input, client)
        # )
        # print("Started notifications...")

    try:
        async with BleakClient("C8:2E:18:DE:51:F2") as client:
            if await client.is_connected():
                try:
                    # Pair with the device (distinct from just connecting)
                    await client.pair()
                    for i in range(10000):
                        print("We are still connected")
                except Exception as e:
                    print(e)
            else:
                print("Failed to connect to device")
    except Exception as e:
        print(e) 


asyncio.run(main())