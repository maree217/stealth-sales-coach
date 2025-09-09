#!/usr/bin/env python3
"""
Live display for sales coach - shows real-time activity
"""

import time
import subprocess
import re
from datetime import datetime

def get_sales_coach_logs():
    """Get recent sales coach logs"""
    try:
        # Get logs from running processes
        result = subprocess.run(
            ['ps', 'aux'], 
            capture_output=True, 
            text=True
        )
        
        coach_processes = []
        for line in result.stdout.split('\n'):
            if 'sales_coach' in line and 'python' in line:
                coach_processes.append(line.strip())
        
        return coach_processes
    except:
        return []

def monitor_activity():
    """Monitor and display sales coach activity"""
    print("🎯 SALES COACH LIVE MONITOR")
    print("=" * 50)
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    last_check = time.time()
    
    while True:
        try:
            current_time = datetime.now().strftime('%H:%M:%S')
            
            # Check for running processes
            processes = get_sales_coach_logs()
            
            print(f"\r[{current_time}] Processes: {len(processes)} | Status: {'🟢 ACTIVE' if processes else '🔴 STOPPED'} ", end="", flush=True)
            
            # Show basic status every 10 seconds
            if time.time() - last_check > 10:
                print()  # New line
                if processes:
                    print("✅ Sales coach processes detected:")
                    for i, proc in enumerate(processes[:2], 1):  # Show first 2
                        # Extract key info
                        parts = proc.split()
                        if len(parts) > 10:
                            cpu = parts[2]
                            mem = parts[3] 
                            print(f"   Process {i}: CPU {cpu}% | MEM {mem}%")
                else:
                    print("❌ No sales coach processes running")
                    print("   Start with: python -m sales_coach.cli start --config config/low_sensitivity.yaml")
                
                print(f"   Monitoring since: {datetime.now().strftime('%H:%M:%S')}")
                print()
                last_check = time.time()
            
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Monitor stopped")
            break
        except Exception as e:
            print(f"\n❌ Monitor error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_activity()