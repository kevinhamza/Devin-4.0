import json
import os
import time
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Analytics:
    def __init__(self, data_file="analytics_data.json"):
        self.data_file = data_file
        self.load_data()

    def load_data(self):
        """Load analytics data from a JSON file."""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as file:
                self.data = json.load(file)
        else:
            self.data = {}

    def save_data(self):
        """Save the analytics data to the JSON file."""
        with open(self.data_file, 'w') as file:
            json.dump(self.data, file, indent=4)

    def log_event(self, event_type, details):
        """Log an event with its details."""
        event_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        event_data = {
            "time": event_time,
            "type": event_type,
            "details": details
        }

        if event_type not in self.data:
            self.data[event_type] = []

        self.data[event_type].append(event_data)
        self.save_data()

        logging.info(f"Event logged: {event_type} - {event_time}")

    def get_event_count(self, event_type):
        """Get the count of a specific event type."""
        if event_type in self.data:
            return len(self.data[event_type])
        return 0

    def get_events_by_type(self, event_type):
        """Retrieve events of a specific type."""
        return self.data.get(event_type, [])

    def generate_report(self):
        """Generate a simple analytics report."""
        report = {
            "total_events": sum(len(events) for events in self.data.values()),
            "event_types": {event_type: len(events) for event_type, events in self.data.items()},
        }
        return report

    def display_report(self):
        """Display a summary report."""
        report = self.generate_report()
        logging.info("Analytics Report:")
        logging.info(f"Total Events: {report['total_events']}")
        for event_type, count in report['event_types'].items():
            logging.info(f"{event_type}: {count} events")

    def reset_data(self):
        """Reset the analytics data."""
        self.data = {}
        self.save_data()
        logging.info("Analytics data reset.")

# Example usage
if __name__ == "__main__":
    analytics = Analytics()

    # Log some events for demonstration
    analytics.log_event("user_login", {"user_id": "12345"})
    analytics.log_event("error", {"message": "Something went wrong."})
    analytics.log_event("user_logout", {"user_id": "12345"})

    # Display the analytics report
    analytics.display_report()
