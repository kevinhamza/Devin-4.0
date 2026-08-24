# Devin/tests/cloud_tests.py
# Purpose: An integration test suite for the cloud stack, verifying that the
#          CloudFacade correctly orchestrates tools and normalizes data.

import unittest
from unittest.mock import patch, MagicMock

# --- Important: We need to set up the path to import our modules ---
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

_import_error = None

try:
    from modules.cloud_integration_module import CloudFacade
    from modules.cloud_integration_utilities import CloudProvider, CloudResourceType, NormalizedCloudResource
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# --- Suppress regular logging output during tests for clarity ---
import logging
logging.disable(logging.CRITICAL)

# --- Sample Raw API Response Data ---
# These dictionaries mimic the real, provider-specific data structures.
SAMPLE_AWS_EC2_RESPONSE = {
    "Reservations": [{
        "Instances": [{
            "InstanceId": "i-01a2b3c4d5e6f7g8h", "InstanceType": "t2.micro",
            "State": {"Name": "running"}, "PublicIpAddress": "54.123.45.67",
            "Tags": [{"Key": "Name", "Value": "WebServer-Prod"}]
        }]
    }]
}
SAMPLE_GCP_COMPUTE_RESPONSE = {
    "items": [{
        "id": "1234567890", "name": "gce-dev-instance", "status": "RUNNING",
        "networkInterfaces": [{"accessConfigs": [{"natIP": "34.67.89.10"}]}],
        "labels": {"env": "dev"}
    }]
}

@unittest.skipUnless(DEVIN_CORE_AVAILABLE, f"Skipping cloud tests, dependency missing: {_import_error}")
class TestCloudFacadeIntegration(unittest.TestCase):
    """
    Tests the CloudFacade's ability to dispatch to and normalize data from
    the correct underlying cloud tools.
    """

    def setUp(self):
        """
        Set up mocks for all CloudTools before each test.

        These are started via patcher.start()/addCleanup rather than as
        `setUp` decorators: a decorator-based patch is only active for the
        duration of the setUp() call itself and reverts before each test
        method runs, so any CloudFacade constructed later *inside* a test
        method (e.g. to test an unconfigured provider) would build a real,
        unmocked AWSTools/GCPTools/AzureTools and try to hit real cloud APIs.
        """
        self.patcher_aws = patch('modules.cloud_integration_module.AWSTools')
        self.patcher_gcp = patch('modules.cloud_integration_module.GCPTools')
        self.patcher_azure = patch('modules.cloud_integration_module.AzureTools')

        self.MockAWSTools = self.patcher_aws.start()
        self.MockGCPTools = self.patcher_gcp.start()
        self.MockAzureTools = self.patcher_azure.start()
        self.addCleanup(self.patcher_aws.stop)
        self.addCleanup(self.patcher_gcp.stop)
        self.addCleanup(self.patcher_azure.stop)

        self.mock_aws_instance = self.MockAWSTools.return_value
        self.mock_gcp_instance = self.MockGCPTools.return_value
        self.mock_azure_instance = self.MockAzureTools.return_value

        # Instantiate the CloudFacade. Its real __init__ takes provider *creds*
        # dicts and constructs the tool instances itself (AWSTools(**aws_creds),
        # etc.) -- since those classes are patched above, any non-empty creds
        # dict is enough to make the facade build our mock instances.
        self.facade = CloudFacade(
            aws_creds={"region_name": "us-east-1"},
            gcp_creds={"project_id": "test-project"},
            azure_creds={"subscription_id": "test-subscription"}
        )

    def test_list_vms_dispatches_to_aws_and_normalizes(self):
        """
        Verify list_vms calls the correct AWS method and normalizes the response.
        """
        print("\n\n--- Testing AWS VM Discovery and Normalization ---")
        # 1. Configure the mock to return our sample AWS data
        self.mock_aws_instance.ec2_describe_instances.return_value = SAMPLE_AWS_EC2_RESPONSE
        
        # 2. Call the high-level facade method
        vms = self.facade.list_vms(CloudProvider.AWS)
        
        # 3. Assert dispatch was correct
        self.mock_aws_instance.ec2_describe_instances.assert_called_once()
        self.mock_gcp_instance.compute_instances_list.assert_not_called()
        print("  [SUCCESS] Facade correctly dispatched to AWSTools.")

        # 4. Assert normalization was correct
        self.assertEqual(len(vms), 1)
        vm = vms[0]
        self.assertIsInstance(vm, NormalizedCloudResource)
        self.assertEqual(vm.provider, CloudProvider.AWS)
        self.assertEqual(vm.resource_type, CloudResourceType.VIRTUAL_MACHINE)
        self.assertEqual(vm.provider_id, "i-01a2b3c4d5e6f7g8h")
        self.assertEqual(vm.name, "WebServer-Prod")
        self.assertEqual(vm.status, "running")
        self.assertEqual(vm.public_ip, "54.123.45.67")
        print("  [SUCCESS] AWS VM data was correctly normalized.")

    def test_list_vms_dispatches_to_gcp_and_normalizes(self):
        """
        Verify list_vms calls the correct GCP method and normalizes the response.
        """
        print("\n\n--- Testing GCP VM Discovery and Normalization ---")
        # 1. Configure the mock to return our sample GCP data
        self.mock_gcp_instance.compute_instances_list.return_value = SAMPLE_GCP_COMPUTE_RESPONSE
        
        # 2. Call the high-level facade method
        vms = self.facade.list_vms(CloudProvider.GCP)
        
        # 3. Assert dispatch was correct
        self.mock_gcp_instance.compute_instances_list.assert_called_once()
        self.mock_aws_instance.ec2_describe_instances.assert_not_called()
        print("  [SUCCESS] Facade correctly dispatched to GCPTools.")

        # 4. Assert normalization was correct
        self.assertEqual(len(vms), 1)
        vm = vms[0]
        self.assertIsInstance(vm, NormalizedCloudResource)
        self.assertEqual(vm.provider, CloudProvider.GCP)
        self.assertEqual(vm.resource_type, CloudResourceType.VIRTUAL_MACHINE)
        self.assertEqual(vm.provider_id, "1234567890")
        self.assertEqual(vm.name, "gce-dev-instance")
        self.assertEqual(vm.status, "RUNNING")
        self.assertEqual(vm.public_ip, "34.67.89.10")
        self.assertEqual(vm.tags, {"env": "dev"})
        print("  [SUCCESS] GCP VM data was correctly normalized.")

    def test_facade_handles_unconfigured_provider_gracefully(self):
        """
        Verify that calling a method for a provider that wasn't configured
        returns an empty list and does not crash.
        """
        print("\n\n--- Testing Graceful Handling of Unconfigured Provider ---")
        # 1. Create a new facade with only AWS configured (an empty gcp_creds
        # dict means CloudFacade leaves self.gcp as None, per its real __init__).
        facade_with_missing_gcp = CloudFacade(aws_creds={"region_name": "us-east-1"}, gcp_creds={})
        
        # 2. Call a method for the unconfigured provider (GCP)
        vms = facade_with_missing_gcp.list_vms(CloudProvider.GCP)
        
        # 3. Assert that no tool method was called and the result is empty
        self.mock_gcp_instance.compute_instances_list.assert_not_called()
        self.assertEqual(vms, [])
        print("  [SUCCESS] Facade returned an empty list for an unconfigured provider.")

if __name__ == '__main__':
    # Re-enable logging for the test runner's output
    logging.disable(logging.NOTSET)
    unittest.main()
