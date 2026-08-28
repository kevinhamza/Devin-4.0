# Devin/tests/integration/test_cloud_services.py
# Purpose: An end-to-end integration test for the full "Think-Act" loop,
#          verifying that the AIAgent and ToolExecutor can drive the
#          cloud modules to perform complex, multi-step workflows.

import unittest
import json
from dataclasses import asdict
from unittest.mock import patch, MagicMock

# --- Important: We need to set up the path to import our modules ---
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

_import_error = None

try:
    from modules.all_ais_modules import AIAgent, AIProvider
    from modules.tool_executor import ToolExecutor
    from modules.cloud_services_manager import CloudServicesManager
    from modules.cloud_integration_module import CloudFacade
    from modules.cloud_integration_utilities import CloudProvider
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# --- Suppress regular logging output during tests for clarity ---
import logging
logging.disable(logging.CRITICAL)

# --- Sample Raw API Response Data ---
SAMPLE_AWS_EC2_RESPONSE = {
    "Reservations": [
        {"Instances": [{"InstanceId": "i-prod123", "State": {"Name": "running"}, "Tags": [{"Key": "env", "Value": "prod"}]}]},
        {"Instances": [{"InstanceId": "i-dev456", "State": {"Name": "running"}, "Tags": [{"Key": "env", "Value": "dev"}]}]},
        {"Instances": [{"InstanceId": "i-stopped789", "State": {"Name": "stopped"}, "Tags": [{"Key": "env", "Value": "dev"}]}]}
    ]
}


def _tool_call_message(tool_name: str, parameters: dict) -> dict:
    """
    Builds a fake response in the shape ChatGPTModule.get_tool_calling_response
    actually returns: an OpenAI chat message dict (via response.model_dump())
    with a single native tool call.
    """
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [{
            "id": "call_1",
            "type": "function",
            "function": {"name": tool_name, "arguments": json.dumps(parameters)},
        }],
    }


@unittest.skipUnless(DEVIN_CORE_AVAILABLE, f"Skipping integration tests, dependency missing: {_import_error}")
class TestEndToEndCloudServices(unittest.TestCase):
    """
    Tests the full workflow from AI decision to cloud automation execution.
    """

    def setUp(self):
        """Set up a complex mock environment."""
        # 1. Patch the lowest level: the cloud provider tools
        self.patcher_aws = patch('modules.cloud_integration_module.AWSTools')
        self.MockAWSTools = self.patcher_aws.start()
        self.mock_aws_instance = self.MockAWSTools.return_value

        # 2. Patch the external dependency: the AI Agent's underlying OpenAI
        # client. AIAgent wires this up as modules.all_ais_modules.ChatGPTModule
        # (not the separate, unrelated modules.ai_connector.OpenAIConnector).
        self.patcher_openai = patch('modules.all_ais_modules.ChatGPTModule')
        self.MockChatGPTModule = self.patcher_openai.start()
        self.mock_openai_instance = self.MockChatGPTModule.return_value

        # 3. Instantiate the REAL mid-level and high-level components.
        # aws_creds must be a non-empty dict for CloudFacade to actually
        # construct an AWSTools (patched -> our mock) instead of leaving
        # self.aws as None.
        self.cloud_facade = CloudFacade(aws_creds={"region_name": "us-east-1"})
        # CloudServicesManager.stop_vm gates on user consent via a
        # UserInteractionManager; a bare mock configured to approve is enough
        # here since we're testing tool dispatch, not the consent UI itself.
        self.mock_uim = MagicMock()
        self.mock_uim.ask_for_confirmation.return_value = True
        self.cloud_manager = CloudServicesManager(cloud_facade=self.cloud_facade, uim=self.mock_uim)
        self.tool_executor = ToolExecutor(cloud_services_manager=self.cloud_manager)
        self.agent = AIAgent(openai_api_key="fake-key")

    def tearDown(self):
        """Stop all patches after each test."""
        patch.stopall()

    def test_e2e_workflow_stop_untagged_vms(self):
        """
        Verify the full chain for a cloud management task:
        User -> Agent -> ToolExecutor -> CloudManager -> CloudFacade -> AWSTools (mocked)
        """
        print("\n\n--- Testing E2E Cloud Workflow: 'Stop Untagged VMs' ---")
        user_prompt = "In AWS, stop all running virtual machines that are NOT tagged with 'env=prod'."

        # --- PREPARE MOCKS ---
        # 1. Configure the mock Cloud API to return our sample data
        self.mock_aws_instance.ec2_describe_instances.return_value = SAMPLE_AWS_EC2_RESPONSE

        # 2. Configure the mock LLM's multi-step reasoning process
        # Step 1: The AI decides to list the VMs to see their state
        ai_plan_step1 = {
            "tool": "list_vms",
            "parameters": {"provider": "AWS"}
        }
        # Step 2: After seeing the list, the AI decides which specific VM to stop
        ai_plan_step2 = {
            "tool": "stop_vm",
            "parameters": {"provider": "AWS", "instance_id": "i-dev456"}
        }
        # Configure the mock to return these plans in sequence
        self.mock_openai_instance.get_tool_calling_response.side_effect = [
            _tool_call_message(ai_plan_step1["tool"], ai_plan_step1["parameters"]),
            _tool_call_message(ai_plan_step2["tool"], ai_plan_step2["parameters"]),
        ]

        # --- EXECUTE WORKFLOW ---
        # 1. THINK (Step 1): The agent formulates the first part of the plan
        print("  [Think] Agent decides to list VMs...")
        tool_call_1 = self.agent.get_tool_selection_response([{"role": "user", "content": user_prompt}], [])
        self.assertEqual(tool_call_1, ai_plan_step1)

        # 2. ACT (Step 1): The executor lists the VMs. execute_tool wraps the
        # tool's return value in a {"status": ..., "result": ...} envelope.
        print("  [Act] Executor lists VMs...")
        list_vms_response = self.tool_executor.execute_tool(tool_call_1)
        self.assertEqual(list_vms_response["status"], "success")
        list_vms_result = list_vms_response["result"]
        self.assertEqual(len(list_vms_result), 3) # Should find all 3 VMs from the mock data
        print(f"  --> Found {len(list_vms_result)} VMs.")

        # 3. THINK (Step 2): The agent analyzes the results and formulates the next step
        print("  [Think] Agent analyzes the list and decides to stop a specific VM...")
        # We feed the result back to the agent as context for its next decision.
        # list_vms_result is a list of NormalizedCloudResource dataclasses, so
        # it needs converting to plain dicts before it can be JSON-serialized.
        context_for_step2 = [
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": json.dumps(ai_plan_step1)}, # The tool call it made
            {"role": "tool", "content": json.dumps([asdict(vm) for vm in list_vms_result], default=str)} # The result of that tool call
        ]
        tool_call_2 = self.agent.get_tool_selection_response(context_for_step2, [])
        self.assertEqual(tool_call_2, ai_plan_step2)

        # 4. ACT (Step 2): The executor stops the specific VM
        print(f"  [Act] Executor stops VM '{ai_plan_step2['parameters']['instance_id']}'...")
        stop_vm_result = self.tool_executor.execute_tool(tool_call_2)
        self.assertEqual(stop_vm_result["status"], "success")
        self.assertTrue(stop_vm_result["result"]["success"])

        # --- VERIFY ---
        print("  [Verify] Verifying the correct low-level API calls were made...")
        # 1. Verify that we listed instances once
        self.mock_aws_instance.ec2_describe_instances.assert_called_once()

        # 2. Verify that we stopped the correct instance and ONLY the correct instance
        self.mock_aws_instance.ec2_stop_instances.assert_called_once_with(InstanceIds=['i-dev456'])

        print("  [SUCCESS] Full 'Perceive-Think-Act' cloud workflow completed successfully.")

if __name__ == '__main__':
    unittest.main()
