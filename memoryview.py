#!/usr/bin/env python3

import io
import timeit
import gc
import sys

def benchmark():
    # 50MB of data
    size = 50 * 1024 * 1024
    data = b'x' * size
    ms = io.BytesIO(data)
    
    print(f"Python Version: {sys.version}")
    print(f"Implementation: {getattr(sys, 'implementation', 'unknown')}")
    print(f"Buffer Size: {size / (1024*1024):.1f} MB\n")

    # 1. Performance: Length Checks
    # In CPython, getvalue() is usually a CoW reference.
    # In PyPy, getvalue() often forces a full copy, making getbuffer() faster.
    gv_timer = timeit.Timer(lambda: len(ms.getvalue()))
    gb_timer = timeit.Timer(lambda: ms.getbuffer().nbytes)
    
    gv_time = gv_timer.timeit(number=10000)
    gb_time = gb_timer.timeit(number=10000)
    
    print(f"--- Performance (10,000 iterations) ---")
    print(f"len(ms.getvalue()):     {gv_time:.5f}s")
    print(f"ms.getbuffer().nbytes:  {gb_time:.5f}s")
    
    if gv_time < gb_time:
        print(f"Speed Factor: {gb_time/gv_time:.2f}x (getvalue is faster)")
    else:
        print(f"Speed Factor: {gv_time/gb_time:.2f}x (getbuffer is faster)")

    # 2. Pitfalls: Memory Locking
    print(f"\n--- Pitfalls ---")
    view = ms.getbuffer()
    print("Memoryview acquired. Attempting truncate(0)...")
    try:
        ms.truncate(0)
        print("RESULT: truncate(0) SUCCEEDED (No BufferError).")
    except BufferError as e:
        print(f"RESULT: Caught expected BufferError: {e}")
    finally:
        view.release()
        print("Memoryview released.")

    # 3. Allocation / GC Check
    gc.collect()
    
    # Cross-interpreter GC tracking
    def get_gc_state():
        if hasattr(gc, 'get_count'):
            return gc.get_count()
        return "N/A (PyPy/Other GC uses generational/non-refcount logic)"

    before = get_gc_state()
    # If getvalue() is slow, this loop will be the bottleneck
    for _ in range(1000):
        _ = len(ms.getvalue())
    after = get_gc_state()
    
    print("\n--- GC Activity (1,000 getvalue calls) ---")
    print(f"GC state before: {before}")
    print(f"GC state after:  {after}")

if __name__ == '__main__':
    benchmark()
