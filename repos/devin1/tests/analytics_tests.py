"""
Analytics Module Tests
This script contains tests for the analytics module of the Devin project.
"""

import unittest
from databases.analytics import AnalyticsDatabase

class TestAnalyticsModule(unittest.TestCase):
    """Test cases for the Analytics Module."""

    @classmethod
    def setUpClass(cls):
        """Set up resources for all test cases."""
        cls.analytics_db = AnalyticsDatabase()
        cls.analytics_db.connect()
        cls.sample_data = [
            {"id": 1, "metric": "page_views", "value": 150},
            {"id": 2, "metric": "unique_visitors", "value": 75},
            {"id": 3, "metric": "bounce_rate", "value": 0.25}
        ]
        for record in cls.sample_data:
            cls.analytics_db.insert_data(record)

    @classmethod
    def tearDownClass(cls):
        """Clean up resources after all tests."""
        cls.analytics_db.clear_data()
        cls.analytics_db.disconnect()

    def test_data_insertion(self):
        """Test if data is correctly inserted into the database."""
        data_count = self.analytics_db.count_entries()
        self.assertEqual(data_count, len(self.sample_data))

    def test_data_retrieval(self):
        """Test if data is correctly retrieved from the database."""
        retrieved_data = self.analytics_db.get_all_data()
        self.assertEqual(len(retrieved_data), len(self.sample_data))
        for record in self.sample_data:
            self.assertIn(record, retrieved_data)

    def test_analytics_metrics(self):
        """Test analytics metrics calculations."""
        total_views = self.analytics_db.calculate_metric("page_views")
        self.assertEqual(total_views, 150)

        unique_visitors = self.analytics_db.calculate_metric("unique_visitors")
        self.assertEqual(unique_visitors, 75)

        bounce_rate = self.analytics_db.calculate_metric("bounce_rate")
        self.assertAlmostEqual(bounce_rate, 0.25, places=2)

    def test_metric_update(self):
        """Test updating a metric value."""
        new_value = 200
        self.analytics_db.update_metric("page_views", new_value)
        updated_value = self.analytics_db.calculate_metric("page_views")
        self.assertEqual(updated_value, new_value)

    def test_data_deletion(self):
        """Test deleting specific data from the database."""
        self.analytics_db.delete_entry_by_id(1)
        remaining_data = self.analytics_db.get_all_data()
        self.assertEqual(len(remaining_data), len(self.sample_data) - 1)
        for record in remaining_data:
            self.assertNotEqual(record["id"], 1)

if __name__ == "__main__":
    unittest.main()
