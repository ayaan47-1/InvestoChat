#!/usr/bin/env python3
"""Test caching implementation"""

import time
from main import retrieve

print("Testing caching implementation...")
print("\n=== First query ===")
start1 = time.time()
result1 = retrieve("payment plan", k=3)
elapsed1 = time.time() - start1
print(f"First query took {elapsed1:.2f}s")
print(f"Mode: {result1['mode']}, Answers: {len(result1.get('answers', []))}")

print("\n=== Second query (same) - should hit cache ===")
start2 = time.time()
result2 = retrieve("payment plan", k=3)
elapsed2 = time.time() - start2
print(f"Second query took {elapsed2:.2f}s")
print(f"Mode: {result2['mode']}, Answers: {len(result2.get('answers', []))}")

print(f"\n=== Speed improvement ===")
if elapsed2 < elapsed1:
    speedup = elapsed1 / elapsed2
    print(f"Second query was {speedup:.1f}x faster!")
else:
    print(f"No speedup detected (might be due to API caching)")

print("\n=== Third query (different) - should NOT hit cache ===")
start3 = time.time()
result3 = retrieve("amenities", k=3)
elapsed3 = time.time() - start3
print(f"Third query took {elapsed3:.2f}s")
print(f"Mode: {result3['mode']}, Answers: {len(result3.get('answers', []))}")

print("\n✅ Cache test complete!")
