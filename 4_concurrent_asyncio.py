import asyncio
import contextlib

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


async def main():
    lock = asyncio.Lock()

    await asyncio.gather(
        *(
            connect_to_device(lock) for _ in range(4)
        )
    )


if __name__ == "__main__":
    for i in range(4):
        print(i) 
    asyncio.run(main())