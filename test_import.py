#!/usr/bin/env python3
"""Test script to check if job_hunter.py can be imported"""
import sys
sys.path.insert(0, 'C:\\Users\\carin\\Desktop\\job-2.0--main')

try:
    import job_hunter
    print("✅ SUCCESS: job_hunter.py imported successfully!")
    print(f"Functions available: {[f for f in dir(job_hunter) if not f.startswith('_')][:10]}...")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
