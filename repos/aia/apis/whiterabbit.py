# apis/whiterabbit.py
import requests
import json
import time
from datetime import datetime
import threading
import logging

class WhiteRabbitAI:
    """
    A class that integrates with White Rabbit AI APIs and provides various functionalities.
    This class can perform data retrieval, analysis, task management, and more.
    """
    
    def __init__(self, api_key, api_endpoint="https://api.whiterabbitneo.com/v1/"):
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.tasks = []
        self.lock = threading.Lock()
        self._setup_logging()

    def _setup_logging(self):
        """Set up logging for API interactions."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler("whiterabbit.log"), logging.StreamHandler()]
        )

    def log_request(self, method, url, status_code, response_time):
        """Log the details of each API request."""
        logging.info(f"API Request: {method} {url} | Status: {status_code} | Time: {response_time}s")

    def _request(self, endpoint, method="GET", data=None):
        """
        Helper function to make an HTTP request to the White Rabbit API.
        """
        url = f"{self.api_endpoint}{endpoint}"
        start_time = time.time()
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response_time = time.time() - start_time
            self.log_request(method, url, response.status_code, response_time)
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Error {response.status_code}: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Request Exception: {e}")
            return None

    def fetch_task_data(self, task_id):
        """
        Fetch data for a specific task from the White Rabbit API.
        """
        endpoint = f"tasks/{task_id}"
        return self._request(endpoint)

    def create_task(self, task_name, task_params):
        """
        Create a new task with the given parameters.
        """
        endpoint = "tasks"
        data = {
            "name": task_name,
            "params": task_params
        }
        return self._request(endpoint, method="POST", data=data)

    def get_all_tasks(self):
        """
        Fetch all tasks from the White Rabbit API.
        """
        endpoint = "tasks"
        return self._request(endpoint)

    def update_task(self, task_id, task_params):
        """
        Update an existing task with new parameters.
        """
        endpoint = f"tasks/{task_id}"
        data = {
            "params": task_params
        }
        return self._request(endpoint, method="POST", data=data)

    def delete_task(self, task_id):
        """
        Delete a task from the White Rabbit API.
        """
        endpoint = f"tasks/{task_id}"
        return self._request(endpoint, method="DELETE")

    def handle_task_failure(self, task_id):
        """
        Handle a task failure by retrying or notifying admins.
        """
        logging.error(f"Task {task_id} failed. Retrying...")
        self.retry_task(task_id)

    def retry_task(self, task_id):
        """
        Retry a failed task.
        """
        logging.info(f"Retrying task {task_id}...")
        task_data = self.fetch_task_data(task_id)
        if task_data:
            task_name = task_data.get("name")
            task_params = task_data.get("params")
            self.create_task(task_name, task_params)

    def perform_batch_operations(self, task_list):
        """
        Perform a series of operations on multiple tasks concurrently.
        """
        threads = []
        for task in task_list:
            task_id = task.get("id")
            thread = threading.Thread(target=self.process_task, args=(task_id,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    def process_task(self, task_id):
        """
        Process an individual task.
        """
        task_data = self.fetch_task_data(task_id)
        if task_data:
            logging.info(f"Processing task {task_id}...")
            # Placeholder for task processing logic
            time.sleep(2)  # Simulate task processing time
            logging.info(f"Task {task_id} processed successfully.")
        else:
            self.handle_task_failure(task_id)

    def schedule_periodic_tasks(self, interval_seconds):
        """
        Schedule tasks to run periodically (every `interval_seconds`).
        """
        logging.info("Scheduling periodic tasks...")
        while True:
            tasks = self.get_all_tasks()
            if tasks:
                self.perform_batch_operations(tasks)
            time.sleep(interval_seconds)

    def generate_report(self):
        """
        Generate a task status report.
        """
        tasks = self.get_all_tasks()
        report = f"Task Status Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += "-" * 50 + "\n"
        for task in tasks:
            task_id = task.get("id")
            status = task.get("status")
            report += f"Task ID: {task_id} | Status: {status}\n"
        report += "-" * 50
        return report

    def send_report_by_email(self, report, email_address):
        """
        Send the generated task report via email.
        Placeholder function, replace with real email-sending code.
        """
        logging.info(f"Sending report to {email_address}")
        print(f"Sending report to {email_address}...")
        # Placeholder for actual email-sending logic (using SMTP, etc.)
        logging.info(f"Report sent to {email_address}.")

    def monitor_and_alert(self):
        """
        Monitor ongoing tasks and alert on any issues (e.g., critical failures).
        """
        tasks = self.get_all_tasks()
        for task in tasks:
            if task.get("status") == "failed":
                self.handle_task_failure(task.get("id"))

if __name__ == "__main__":
    # Example usage of the WhiteRabbitAI class
    api_key = "your_api_key_here"
    ai = WhiteRabbitAI(api_key)

    # Fetch all tasks and process them
    tasks = ai.get_all_tasks()
    ai.perform_batch_operations(tasks)

    # Monitor tasks periodically and alert if necessary
    ai.schedule_periodic_tasks(60)  # Check tasks every 60 seconds

    # Generate and send a task report
    report = ai.generate_report()
    ai.send_report_by_email(report, "admin@example.com")
