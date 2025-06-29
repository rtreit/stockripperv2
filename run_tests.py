#!/usr/bin/env python3
"""
StockRipper v2 - Test Runner
Runs all end-to-end tests for the multi-agent trading system.
"""

import sys
import os
import asyncio
import subprocess
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def run_all_tests():
    """Run all end-to-end tests in sequence."""
    print("🚀 StockRipper v2 - Complete Test Suite")
    print("=" * 50)
    print("Running all end-to-end tests...")
    print()
    
    test_files = [
        "tests/utils/verify_system.py",
        "tests/e2e/test_agent_workflow.py", 
        "tests/e2e/test_complete_workflow.py",
        "tests/e2e/test_real_stock_analysis.py"
    ]
    
    results = {}
    
    for test_file in test_files:
        test_name = Path(test_file).stem
        print(f"📋 Running {test_name}...")
        
        try:
            result = subprocess.run(
                [sys.executable, test_file], 
                capture_output=True, 
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print(f"  ✅ {test_name}: PASSED")
                results[test_name] = "PASSED"
            else:
                print(f"  ❌ {test_name}: FAILED")
                print(f"     Error: {result.stderr}")
                results[test_name] = "FAILED"
                
        except subprocess.TimeoutExpired:
            print(f"  ⏰ {test_name}: TIMEOUT")
            results[test_name] = "TIMEOUT"
        except Exception as e:
            print(f"  💥 {test_name}: ERROR - {e}")
            results[test_name] = "ERROR"
        
        print()
    
    # Summary
    print("=" * 50)
    print("📊 TEST SUITE RESULTS")
    print("=" * 50)
    
    passed = sum(1 for v in results.values() if v == "PASSED")
    total = len(results)
    
    for test_name, status in results.items():
        status_icon = {"PASSED": "✅", "FAILED": "❌", "TIMEOUT": "⏰", "ERROR": "💥"}
        print(f"{status_icon.get(status, '❓')} {test_name}: {status}")
    
    print()
    print(f"📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! StockRipper v2 is fully functional.")
        return True
    else:
        print("⚠️  Some tests failed. Check logs above.")
        return False

if __name__ == "__main__":
    print("🔬 StockRipper v2 Test Suite")
    print("Running comprehensive end-to-end tests...")
    print()
    
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
