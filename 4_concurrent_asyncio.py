import asyncio
import contextlib
import time
import random

counter = 0

async def connect_to_device(
    lock: asyncio.Lock
):
    global counter
    async with contextlib.AsyncExitStack() as stack:
        # Trying to connect to multiple devices at once can cause errors, which is what the lock is for
        async with lock:
            counter = counter + 1
            print("Counter = ")
            print(counter)

        while counter < 4:
            await asyncio.sleep(0.01)

        print("Counter has finished")


# async def main():
#     lock = asyncio.Lock()

#     await asyncio.gather(
#         *(
#             connect_to_device(lock) for _ in range(4)
#         )
#     )

first_one_ready = False
second_one_ready = False
forearm_data = 0

async def callback_1(event1, event2, wait_time):
    await asyncio.sleep(wait_time)
    print("First one is ready")
    event1.set()
    await event2.wait()
    print("Forearm data is", forearm_data)
    # Perform error check here
    print("Task 1: Both are done")
    event1.clear()

async def callback_2(event1, event2, wait_time):
    await asyncio.sleep(wait_time)
    global forearm_data
    print("Second one is ready")
    forearm_data = random.randint(1, 1000)
    print("Forearm data to send", forearm_data)
    event2.set()
    await event1.wait()
    print("Task 2: Both are done")
    event2.clear()

async def callback_3(event1, event2, wait_time):
    await asyncio.sleep(wait_time)
    print("Third one is doing its own thing")

async def callback_4(event1, event2, wait_time):
    await asyncio.sleep(wait_time)
    print("Fourth one is doing its own thing")
    
async def wait_for_both(callback, task_num, wait_time, event1, event2):
    print(callback)
    for i in range(100):
        print(task_num, i)
        result = await callback(event1, event2, wait_time)

wait_times = [0.02, 0.02, 0.03, 0.03]
task_nums = [1, 2, 3, 4]
callbacks = [callback_1, callback_2, callback_3, callback_4]

async def main():
    event1 = asyncio.Event()
    event2 = asyncio.Event()
    tasks = []

    # tasks = [
    #     asyncio.create_task(wait_for_both(callback_1, 1, event1, event2)),
    #     asyncio.create_task(wait_for_both(callback_2, 2, event1, event2))
    # ]

    await asyncio.gather(
        *(
            wait_for_both(callback, task_num, wait_time, event1, event2) for callback, task_num, wait_time in zip(callbacks, task_nums, wait_times)
        )
    )
    


if __name__ == "__main__":
    asyncio.run(main())