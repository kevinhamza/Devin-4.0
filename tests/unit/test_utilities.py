# Devin/tests/unit/test_utilities.py
# Purpose: A suite of unit tests for validating small, isolated pieces of
#          logic, such as data normalization and text parsing functions.

import unittest
from unittest.mock import MagicMock

# --- Important: We need to set up the path to import our modules ---
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

_import_error = None

try:
    # --- Import the specific utility classes and functions to be tested ---
    from modules.cloud_integration_utilities import DataNormalizer, CloudProvider, CloudResourceType, NormalizedCloudResource
    from modules.system_monitor import RemoteMonitor
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    _import_error = e

# --- Suppress regular logging output during tests for clarity ---
import logging
logging.disable(logging.CRITICAL)

# --- Sample Raw API Response Data for Cloud Tests ---
SAMPLE_AWS_EC2_RESPONSE_INSTANCE = {
    "InstanceId": "i-01a2b3c4d5e6f7g8h", "InstanceType": "t2.micro",
    "State": {"Name": "running"}, "PublicIpAddress": "54.123.45.67",
    "Tags": [{"Key": "Name", "Value": "WebServer-Prod"}]
}
SAMPLE_GCP_COMPUTE_RESPONSE_INSTANCE = {
    "id": "1234567890", "name": "gce-dev-instance", "status": "RUNNING",
    "machineType": "zones/us-central1-a/machineTypes/e2-medium",
    "networkInterfaces": [{"accessConfigs": [{"natIP": "34.67.89.10"}]}],
    "labels": {"env": "dev"}
}


@unittest.skipUnless(DEPS_AVAILABLE, f"Skipping unit tests, dependency missing: {_import_error}")
class TestDataNormalizer(unittest.TestCase):
    """Unit tests for the DataNormalizer class."""

    def setUp(self):
        """Create an instance of the normalizer for each test."""
        self.normalizer = DataNormalizer()

    def test_normalize_aws_vm(self):
        """Verify normalization of a standard AWS EC2 instance dictionary."""
        print("\n\n--- Unit Test: DataNormalizer for AWS VM ---")
        result = self.normalizer.from_aws_ec2_instance(SAMPLE_AWS_EC2_RESPONSE_INSTANCE, region="us-east-1")

        self.assertIsInstance(result, NormalizedCloudResource)
        self.assertEqual(result.provider, CloudProvider.AWS)
        self.assertEqual(result.resource_type, CloudResourceType.VIRTUAL_MACHINE)
        self.assertEqual(result.provider_id, "i-01a2b3c4d5e6f7g8h")
        self.assertEqual(result.name, "WebServer-Prod")
        self.assertEqual(result.status, "running")
        self.assertEqual(result.public_ip, "54.123.45.67")
        self.assertEqual(result.metadata["instance_type"], "t2.micro")
        print("  [SUCCESS] Correctly normalized standard AWS VM data.")

    def test_normalize_aws_vm_missing_name_tag(self):
        """Verify fallback to provider_id when 'Name' tag is missing."""
        data = SAMPLE_AWS_EC2_RESPONSE_INSTANCE.copy()
        data["Tags"] = [{"Key": "env", "Value": "prod"}] # Remove the 'Name' tag

        result = self.normalizer.from_aws_ec2_instance(data, region="us-east-1")
        self.assertEqual(result.name, result.provider_id, "Name should fall back to InstanceId when tag is missing.")
        print("  [SUCCESS] Correctly handled missing 'Name' tag for AWS VM.")

    def test_normalize_gcp_vm(self):
        """Verify normalization of a standard GCP Compute Engine instance dictionary."""
        print("\n\n--- Unit Test: DataNormalizer for GCP VM ---")
        result = self.normalizer.from_gcp_compute_instance(SAMPLE_GCP_COMPUTE_RESPONSE_INSTANCE, zone="us-central1-a")

        self.assertIsInstance(result, NormalizedCloudResource)
        self.assertEqual(result.provider, CloudProvider.GCP)
        self.assertEqual(result.resource_type, CloudResourceType.VIRTUAL_MACHINE)
        self.assertEqual(result.provider_id, "1234567890")
        self.assertEqual(result.name, "gce-dev-instance")
        self.assertEqual(result.status, "RUNNING")
        self.assertEqual(result.public_ip, "34.67.89.10")
        self.assertEqual(result.tags, {"env": "dev"})
        self.assertIn("e2-medium", result.metadata["machine_type"])
        print("  [SUCCESS] Correctly normalized standard GCP VM data.")


@unittest.skipUnless(DEPS_AVAILABLE, f"Skipping unit tests, dependency missing: {_import_error}")
class TestRemoteMonitorParsing(unittest.TestCase):
    """Unit tests for the text-parsing methods of the RemoteMonitor."""

    def setUp(self):
        """Create an instance of the monitor for each test."""
        # The monitor needs a mock SSH client, but we won't use the client itself.
        mock_ssh_client = MagicMock()
        self.monitor = RemoteMonitor(ssh_client=mock_ssh_client)

    def test_parse_top_output_cpu(self):
        """Verify parsing of CPU idle percentage from `top` command output."""
        print("\n\n--- Unit Test: RemoteMonitor CPU Parsing ---")
        mock_output = "top - 10:00:00 up 10 days,  1:00,  1 user,  load average: 0.00, 0.01, 0.05\n%Cpu(s): 10.0 us,  5.0 sy,  0.0 ni, 85.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st"
        result = self.monitor._parse_top_output_cpu(mock_output)
        self.assertAlmostEqual(result, 15.0) # 100 - 85.0 idle
        print("  [SUCCESS] Correctly parsed CPU usage from 'top' output.")
        
    def test_parse_free_output_memory(self):
        """Verify parsing of memory usage percentage from `free -b` command output."""
        print("\n\n--- Unit Test: RemoteMonitor Memory Parsing ---")
        mock_output = "              total        used        free      shared  buff/cache   available\nMem:        8000000     4800000     3200000       10000       500000     3700000"
        result = self.monitor._parse_free_output_memory(mock_output)
        self.assertAlmostEqual(result, 60.0) # 4,800,000 / 8,000,000
        print("  [SUCCESS] Correctly parsed memory usage from 'free' output.")
        
    def test_parse_df_output_disk(self):
        """Verify parsing of disk usage percentage from `df -h` command output."""
        print("\n\n--- Unit Test: RemoteMonitor Disk Parsing ---")
        mock_output = "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1       100G   90G   10G  90% /\n/dev/sdb1        50G    5G   45G  10% /data"
        result = self.monitor._parse_df_output_disk(mock_output)
        self.assertAlmostEqual(result, 90.0) # Should take the root filesystem '/'
        print("  [SUCCESS] Correctly parsed disk usage from 'df' output.")


if __name__ == '__main__':
    unittest.main()
