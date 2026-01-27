#!/usr/bin/env python3
"""
Simple manual test for memory collection
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from aiops.memory.collectors import SystemMemoryCollector, ProcessMemoryCollector
from aiops.cli.formatters.table import TableFormatter
import os

def test_system_memory():
    """Test system memory collection"""
    print("Testing System Memory Collection...")
    print("=" * 60)

    try:
        collector = SystemMemoryCollector()
        collector.initialize()

        metrics = collector.collect()

        if metrics:
            formatter = TableFormatter()
            output = formatter.format(metrics)
            print(output)
            print(f"\n✓ Successfully collected {len(metrics)} system memory metrics")
        else:
            print("✗ No metrics collected")

        collector.cleanup()
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_process_memory():
    """Test process memory collection"""
    print("\nTesting Process Memory Collection...")
    print("=" * 60)

    try:
        collector = ProcessMemoryCollector(max_processes=5)
        collector.initialize()

        # Test with current process
        pid = os.getpid()
        metrics = collector.collect(pid=pid)

        if metrics:
            formatter = TableFormatter()
            output = formatter.format(metrics)
            print(output)
            print(f"\n✓ Successfully collected memory for process {pid}")
        else:
            print("✗ No metrics collected")

        # Test top processes
        print("\nTop 5 processes by memory:")
        print("-" * 60)
        metrics = collector.collect()
        if metrics:
            output = formatter.format(metrics)
            print(output)
            print(f"\n✓ Successfully collected {len(metrics)} process metrics")

        collector.cleanup()
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("AIOps Memory Collection Manual Test")
    print("=" * 60)
    print()

    system_ok = test_system_memory()
    process_ok = test_process_memory()

    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"  System Memory: {'✓ PASS' if system_ok else '✗ FAIL'}")
    print(f"  Process Memory: {'✓ PASS' if process_ok else '✗ FAIL'}")
    print("=" * 60)

    sys.exit(0 if (system_ok and process_ok) else 1)
