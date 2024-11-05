from itertools import tee
import re
from datetime import datetime, timedelta
from collections import defaultdict
import time
import sys
import os

# Configuration of constants for the adjusted problem statement
BURST_EVENT_TYPE = "WARNING"          
BURST_THRESHOLD = 5                    
BURST_TIME_WINDOW_MINUTES = 3         

ERROR_THRESHOLD = 5                   
ERROR_TIME_WINDOW_MINUTES = 60         

# Instructions for usage:
#1. Run the script
#2. Enter the path to the log file when prompted. If not, a new file will be created.
#3. Use the menu to filter, count, extract, and display events
#4. The log file should follow the specified format:
#        [YYYY-MM-DD HH:MM:SS] EVENT_TYPE: EVENT_DETAILS

def parse_log_file(log_file_path):
    log_entries = []
    log_pattern = re.compile(r'\[(.*?)\]\s+(\w+):\s+(.*)')
    try:
        with open(log_file_path, 'r') as file:
            for line in file:
                match = log_pattern.match(line.strip())
                if match:
                    timestamp_str, event_type, event_details = match.groups()
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    log_entries.append({
                        'timestamp': timestamp,
                        'event_type': event_type,
                        'event_details': event_details
                    })
    except FileNotFoundError:
        print(f"File '{log_file_path}' not found. Creating a new log file.")
        # Create an empty log file
        with open(log_file_path, 'w') as file:
            pass
    return log_entries

def filter_events_by_type(entries, event_type):
    filtered = [entry for entry in entries if entry['event_type'] == event_type]
    filtered_sorted = sorted(filtered, key=lambda x: x['timestamp'])
    return filtered_sorted

def count_events_by_type(entries):
    counts = defaultdict(int)
    for entry in entries:
        counts[entry['event_type']] += 1
    return dict(counts)

def extract_events_by_date_range(entries, start_date_str, end_date_str):
    datetime_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d']
    def parse_date(date_str):
        for fmt in datetime_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"Date '{date_str}' is not in a recognized format.")

    try:
        start_datetime = parse_date(start_date_str)
        end_datetime = parse_date(end_date_str)

        # If time is not provided, set start time to 00:00:00 and end time to 23:59:59
        if len(start_date_str) == 10:
            start_datetime = start_datetime.replace(hour=0, minute=0, second=0)
        if len(end_date_str) == 10:
            end_datetime = end_datetime.replace(hour=23, minute=59, second=59)

        extracted = [
            entry for entry in entries
            if start_datetime <= entry['timestamp'] <= end_datetime
        ]
        extracted_sorted = sorted(extracted, key=lambda x: x['timestamp'])
        return extracted_sorted

    except ValueError as ve:
        print(f"Error parsing dates: {ve}")
        return None

def display_summary_report(entries):
    counts = count_events_by_type(entries)
    unique_dates = sorted({entry['timestamp'].date().isoformat() for entry in entries})
    if entries:
        most_recent_event = max(entries, key=lambda x: x['timestamp'])
    else:
        most_recent_event = None
    summary = {
        'counts': counts,
        'unique_dates': unique_dates,
        'most_recent_event': most_recent_event
    }
    return summary

def display_events(events):
    for entry in events:
        timestamp_str = entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp_str}] {entry['event_type']}: {entry['event_details']}")

def print_with_aura(text, pause_end_sentence=0.5, pause_between_letters=0.05):
    for line in text.split('\n'):
        for char in line:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(pause_between_letters)
        sys.stdout.write('\n')
        sys.stdout.flush()
        if line.endswith(('.', '!', ',')):
            time.sleep(pause_end_sentence)

def add_log_entry(log_file_path):
    event_type = input("Enter the event type (ERROR, WARNING, INFO, MAINTENANCE): ").upper()
    event_details = input("Enter the event details: ")
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_entry = f"[{timestamp}] {event_type}: {event_details}"
    
    with open(log_file_path, 'a') as file:
        file.write(log_entry + '\n')
        print(f"Log entry written to '{log_file_path}'.")

def detect_log_bursts(entries, event_type=BURST_EVENT_TYPE, n=BURST_THRESHOLD, m=BURST_TIME_WINDOW_MINUTES):
    bursts = []
    event_timestamps = sorted([entry['timestamp'] for entry in entries if entry['event_type'] == event_type])

    left = 0
    for right in range(len(event_timestamps)):
        while event_timestamps[right] - event_timestamps[left] > timedelta(minutes=m):
            left += 1
        window_size = right - left + 1
        if window_size >= n:
            burst_start = event_timestamps[left]
            burst_end = event_timestamps[right]
            bursts.append((burst_start, burst_end))
            # Move left to avoid overlapping bursts
            left += 1

    if bursts:
        print(f"\n*** Detected {len(bursts)} burst(s) for event type '{event_type}': ***")
        for idx, (start, end) in enumerate(bursts, 1):
            print(f" Burst {idx}: {start} to {end} ({n} events within {m} minutes)")

def generate_error_alerts(entries, threshold=ERROR_THRESHOLD, window_minutes=ERROR_TIME_WINDOW_MINUTES):
    error_events = sorted([entry['timestamp'] for entry in entries if entry['event_type'] == 'ERROR'])

    alerts = []
    left = 0
    for right in range(len(error_events)):
        while error_events[right] - error_events[left] > timedelta(minutes=window_minutes):
            left += 1
        window_size = right - left + 1
        if window_size >= threshold:
            alert_time = error_events[left]
            alerts.append(alert_time)
            left += 1

    if alerts:
        print(f"\n*** ALERT: Detected {len(alerts)} high-error period(s): ***")
        for idx, alert_time in enumerate(alerts, 1):
            print(f" Alert {idx}: Starting at {alert_time}")

def run_parser(log_file_path):
    entries = parse_log_file(log_file_path)

    # I had a manual detection function but made it automatic now
    detect_log_bursts(entries)

    # Automatically generate error alerts, should work now, didnt test with extreme use-cases
    generate_error_alerts(entries)

    while True:
        print("\nSpace Logbook Parser")
        print("1. Filter Events by Type")
        print("2. Count Events by Type")
        print("3. Extract Events by Date Range")
        print("4. Display Summary Report")
        print("5. Add Log Entry")
        print("6. Exit")
        choice = input("Select an option (1-6): ")

        if choice == '1':
            event_type = input("Enter the event type (ERROR, WARNING, INFO, MAINTENANCE): ").upper()
            filtered_events = filter_events_by_type(entries, event_type)
            print(f"\n{event_type} Events:")
            display_events(filtered_events)

        elif choice == '2':
            counts = count_events_by_type(entries)
            print("\nEvent Count:")
            for event, count in counts.items():
                print(f"{event}: {count}")

        elif choice == '3':
            print("You can enter dates in 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS' format.")
            start_date = input("Enter the start date: ")
            end_date = input("Enter the end date: ")
            extracted_events = extract_events_by_date_range(entries, start_date, end_date)
            if extracted_events is not None:
                print(f"\nEvents from {start_date} to {end_date}:")
                if extracted_events:
                    display_events(extracted_events)
                else:
                    print("No events found in the specified range.")

        elif choice == '4':
            summary = display_summary_report(entries)
            print("\nSummary Report:")
            print("Total Events:")
            for event, count in summary['counts'].items():
                print(f"{event}: {count}")

            print("\nUnique Dates in Log:")
            for date in summary['unique_dates']:
                print(date)

            print("\nMost Recent Event:")
            if summary['most_recent_event']:
                entry = summary['most_recent_event']
                timestamp_str = entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp_str}] {entry['event_type']}: {entry['event_details']}")
            else:
                print("No events found.")

        elif choice == '5':  
            add_log_entry(log_file_path)
            entries = parse_log_file(log_file_path) 
            detect_log_bursts(entries)
            generate_error_alerts(entries)

        elif choice == '6': 
            poem = """Do not go gentle into that good night,
Old age should burn and rave at close of day;
Rage, rage against the dying of the light.

Though wise men at their end know dark is right,
Because their words had forked no lightning they
Do not go gentle into that good night.

Good men, the last wave by, crying how bright
Their frail deeds might have danced in a green bay,
Rage, rage against the dying of the light.

Wild men who caught and sang the sun in flight,
And learn, too late, they grieved it on its way,
Do not go gentle into that good night.

Grave men, near death, who see with blinding sight
Blind eyes could blaze like meteors and be gay,
Rage, rage against the dying of the light.

And you, my father, there on the sad height,
Curse, bless, me now with your fierce tears, I pray.
Do not go gentle into that good night.
Rage, rage against the dying of the light."""
    
            print_with_aura(poem)
            break
            # I hope you see this, this took a lot of effort :)

        else:
            print("Invalid option. Please select a number between 1 and 6.")

if __name__ == "__main__":
    run_parser('space_log.txt')
