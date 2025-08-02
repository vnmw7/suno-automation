import os
import sys
from datetime import datetime

def view_ai_logs(date=None):
    """View AI generation logs for a specific date or today"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    log_file = os.path.join(log_dir, f'ai_generations_{date}.log')
    
    if not os.path.exists(log_file):
        print(f"No log file found for date: {date}")
        print(f"Looking for: {log_file}")
        return
    
    print(f"=== AI Generations Log for {date} ===\n")
    
    with open(log_file, 'r') as f:
        for line in f:
            print(line.strip())

if __name__ == "__main__":
    # Usage: python log_viewer.py [YYYYMMDD]
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    view_ai_logs(date_arg)
