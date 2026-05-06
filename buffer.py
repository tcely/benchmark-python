#!/usr/bin/env python3

import io
import threading
import asyncio

class SynchronizedBytesIO(io.BytesIO):
    """
    A fully synchronized BytesIO implementation ensuring thread safety and 
    async compatibility across multiple event loops.
    """
    # Class-level lock to ensure thread-safe initialization of instance-level locks
    _init_lock = threading.Lock()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thread_lock = None
        self._async_locks = {}

    def _get_thread_lock(self):
        if self._thread_lock is None:
            with self._init_lock:
                if self._thread_lock is None:
                    # RLock is used to allow nested 'with' calls on the same thread
                    self._thread_lock = threading.RLock()
        return self._thread_lock

    def _get_async_lock(self):
        loop = asyncio.get_running_loop()
        with self._get_thread_lock():
            if loop not in self._async_locks:
                self._async_locks[loop] = asyncio.Lock()
            return self._async_locks[loop]

    # --- Sync Context Manager ---
    def __enter__(self):
        self._get_thread_lock().acquire()
        return self

    def __exit__(self, *args):
        self._get_thread_lock().release()

    # --- Async Context Manager ---
    async def __aenter__(self):
        await self._get_async_lock().acquire()
        return self

    async def __aexit__(self, *args):
        self._get_async_lock().release()

    # --- Length Operations ---

    def __len__(self):
        with self._get_thread_lock():
            pos = self.tell()
            try:
                return self.seek(0, 2)
            finally:
                self.seek(pos)

    async def alen(self):
        # Inlined pointer logic avoids async deadlocks caused by non-reentrant asyncio locks
        async with self._get_async_lock():
            pos = self.tell()
            try:
                return self.seek(0, 2)
            finally:
                self.seek(pos)

    # --- Read Operations ---

    def read(self, size=-1):
        with self._get_thread_lock():
            return super().read(size)

    async def aread(self, size=-1):
        async with self._get_async_lock():
            return super().read(size)

    def readline(self, size=-1):
        with self._get_thread_lock():
            return super().readline(size)

    async def areadline(self, size=-1):
        async with self._get_async_lock():
            return super().readline(size)

    def readlines(self, hint=-1):
        with self._get_thread_lock():
            return super().readlines(hint)

    async def areadlines(self, hint=-1):
        async with self._get_async_lock():
            return super().readlines(hint)

    # --- Write Operations ---

    def write(self, b):
        with self._get_thread_lock():
            return super().write(b)

    async def awrite(self, b):
        async with self._get_async_lock():
            return super().write(b)

    def writelines(self, lines):
        with self._get_thread_lock():
            return super().writelines(lines)

    async def awritelines(self, lines):
        async with self._get_async_lock():
            return super().writelines(lines)

    # --- Pointer & Buffer Operations ---

    def seek(self, offset, whence=0):
        with self._get_thread_lock():
            return super().seek(offset, whence)

    def tell(self):
        with self._get_thread_lock():
            return super().tell()

    def truncate(self, size=None):
        with self._get_thread_lock():
            return super().truncate(size)

    def getvalue(self):
        with self._get_thread_lock():
            return super().getvalue()

    def getbuffer(self):
        with self._get_thread_lock():
            return super().getbuffer()

    # --- Lifecycle Operations ---

    def flush(self):
        with self._get_thread_lock():
            return super().flush()

    def close(self):
        try:
            if self._thread_lock:
                with self._thread_lock:
                    super().close()
            else:
                super().close()
        finally:
            self._thread_lock = None
            self._async_locks.clear()
