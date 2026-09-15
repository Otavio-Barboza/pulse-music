# import geral
import asyncio, threading


class AsyncManager:

    loop = asyncio.new_event_loop()
    _started = threading.Event()

    @classmethod
    def start(cls):
        threading.Thread(
            target = cls._run,
            daemon = True
        ).start()

        cls._started.wait()

    @classmethod
    def _run(cls):
        asyncio.set_event_loop(cls.loop)
        cls._started.set()
        cls.loop.run_forever()
        
    @classmethod
    def create_task(cls, coroutine):
        asyncio.run_coroutine_threadsafe(
            coroutine,
            cls.loop
        )