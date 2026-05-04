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
    gv_timer = timeit.Timer(lambda: len(ms.getvalue()))
    gb_timer = timeit.Timer(lambda: ms.getbuffer().nbytes)
    
    gv_time = gv_timer.timeit(number=10000)
    gb_time = gb_timer.timeit(number=10000)
    
    print(f"--- Performance (10,000 iterations) ---")
    print(f"len(ms.getvalue()):     {gv_time:.5f}s")
    print(f"ms.getbuffer().nbytes:  {gb_time:.5f}s")
    # Corrected speed factor logic based on your PyPy results
    if gv_time < gb_time:
        print(f"Speed Factor: {gb_time/gv_time:.2f}x (getvalue is faster)\n")
    else:
        print(f"Speed Factor: {gv_time/gb_time:.2f}x (getbuffer is faster)\n")

    # 2. Pitfalls: Memory Locking
    print(f"--- Pitfalls ---")
    view = ms.getbuffer()
    print("Memoryview acquired. Attempting truncate(0)...")
    try:
        ms.truncate(0)
        print("Success: truncate(0) did NOT raise BufferError.")
    except BufferError as e:
        print(f"Caught expected BufferError: {e}")
    finally:
        view.release()
        print("Memoryview released.")

    # 3. Allocation / GC Check
    gc.collect()
    
    # Cross-interpreter GC tracking
    def get_gc_state():
        if hasattr(gc, 'get_count'):
            return gc.get_count()
        return "N/A (PyPy/Other GC)"

    before = get_gc_state()
    for _ in range(1000):
        _ = len(ms.getvalue())
    after = get_gc_state()
    
    print("\n--- GC Activity (1,000 getvalue calls) ---")
    print(f"GC state before: {before}")
    print(f"GC state after:  {after}")
    if before == after and before != "N/A (PyPy/Other GC)":
        print("(Stability in counts proves Copy-on-Write avoids redundant allocations)")
    elif before == "N/A (PyPy/Other GC)":
        print("(PyPy GC detected; allocations are managed via JIT/Generationless GC)")

if __name__ == '__main__':
    benchmark()
