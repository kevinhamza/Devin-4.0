# Devin/cyber_range/resource_manager.py
# Purpose: Handles provisioning and deprovisioning of virtual resources.

import os
import json
import uuid
import logging
import time
import threading # For potential background tasks or locking state file
from typing import Dict, Any, List, Optional, TypedDict, Literal

# --- Conceptual Imports for Backend SDKs ---
# These would need to be installed and configured
# import docker
# from kubernetes import client, config
# import libvirt
# from ..cloud.aws_integration import AWSIntegration # Example
# from ..cloud.gcp_integration import GCPIntegration # Example

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Data Structures ---

class ResourceDefinition(TypedDict):
    """Defines a type of resource that can be provisioned."""
    resource_id: str # Unique identifier for this type (e.g., "kali_tools_vm", "vuln_web_app_container")
    type: Literal["vm", "container", "network", "storage_volume"]
    backend: Literal["docker", "kubernetes", "libvirt", "aws", "gcp", "azure", "private_cloud"] # Which system provisions it
    # Backend-specific parameters
    source_image_or_template: str # e.g., Docker image name, K8s manifest path, VM template name, AMI ID
    compute_specs: Optional[Dict[str, Any]] # e.g., {'cpu': 1, 'memory_mb': 1024}, K8s resource requests/limits, instance type
    network_attachments: Optional[List[Dict[str, str]]] # e.g., [{'network_id': 'ctf_internal_net', 'ip_address': 'static/10.0.0.5'}]
    storage_specs: Optional[List[Dict[str, Any]]] # e.g., [{'size_gb': 10, 'mount_point': '/data'}]
    # Other config like ports to expose, startup commands etc.
    misc_config: Optional[Dict[str, Any]]

class ProvisionedResource(TypedDict):
    """Tracks details of an actually provisioned resource instance."""
    instance_specific_id: str # ID assigned by the backend (e.g., container ID, VM ID, K8s pod name)
    resource_definition_id: str # Links back to the ResourceDefinition
    backend: str # Backend used
    status: Literal["creating", "running", "stopped", "error", "deleting", "deleted"]
    connection_info: Dict[str, Any] # e.g., {'ip_address': '...', 'ssh_port': 22, 'url': '...'}
    provision_timestamp_utc: str
    last_check_timestamp_utc: str
    associated_scenario_instance_id: str # Link back to the scenario instance using this resource

# --- Conceptual Backend Handler Base Class ---
class ResourceHandlerBase:
    """Abstract base class for backend-specific resource handlers."""
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = self._connect()

    def _connect(self) -> Any: raise NotImplementedError
    def provision_resource(self, definition: ResourceDefinition, instance_id_tag: str) -> ProvisionedResource: raise NotImplementedError
    def deprovision_resource(self, provisioned_info: ProvisionedResource) -> bool: raise NotImplementedError
    def get_resource_status(self, provisioned_info: ProvisionedResource) -> str: raise NotImplementedError
    # Add other methods: stop, start, snapshot etc.

# --- Conceptual Backend Handler Implementations (Placeholders) ---

class DockerHandler(ResourceHandlerBase):
    """Handles Docker resources using docker-py (conceptual)."""
    def _connect(self) -> Any:
        logger.info("Conceptual: Initializing Docker client...")
        # try: import docker; return docker.from_env()
        # except ImportError: logger.error("Docker SDK not found"); return None
        # except Exception as e: logger.error(f"Docker client init error: {e}"); return None
        return "mock_docker_client" # Placeholder
    def provision_resource(self, definition: ResourceDefinition, instance_id_tag: str) -> ProvisionedResource:
        logger.info(f"DockerHandler: Provisioning container from image '{definition['source_image_or_template']}'...")
        # --- Placeholder: docker run command ---
        # container_name = f"{instance_id_tag}-{definition['resource_id']}-{uuid.uuid4().hex[:4]}"
        # ports_dict = {f"{p['containerPort']}/tcp": p['hostPort'] for p in definition.get('misc_config',{}).get('ports',[])} # Example port mapping
        # volumes_dict = {v['hostPath']: {'bind': v['mount_point'], 'mode': 'rw'} for v in definition.get('storage_specs',[])} # Example volume mapping
        # container = self.client.containers.run(
        #     image=definition['source_image_or_template'],
        #     name=container_name,
        #     detach=True,
        #     ports=ports_dict,
        #     volumes=volumes_dict,
        #     labels={'scenario_instance': instance_id_tag, 'resource_def': definition['resource_id']}
        # )
        # ip = self.client.containers.get(container.id).attrs['NetworkSettings']['IPAddress'] # Get IP (depends on network)
        # return ProvisionedResource(instance_specific_id=container.id, ..., status='running', connection_info={'ip': ip})
        # --- End Placeholder ---
        mock_id = f"docker-cont-{uuid.uuid4().hex[:6]}"
        logger.info(f"  - Simulated docker run, Container ID: {mock_id}")
        return ProvisionedResource(
            instance_specific_id=mock_id, resource_definition_id=definition['resource_id'],
            backend='docker', status='running', connection_info={'ip_address': f'172.17.0.{random.randint(2,254)}'},
            provision_timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            last_check_timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            associated_scenario_instance_id=instance_id_tag
        )
    def deprovision_resource(self, provisioned_info: ProvisionedResource) -> bool:
        logger.info(f"DockerHandler: Deprovisioning container ID '{provisioned_info['instance_specific_id']}'...")
        # --- Placeholder: docker stop / docker rm ---
        # try:
        #     container = self.client.containers.get(provisioned_info['instance_specific_id'])
        #     container.stop(timeout=10)
        #     container.remove()
        #     return True
        # except Exception as e: logger.error(f"Error removing container: {e}"); return False
        # --- End Placeholder ---
        logger.info("  - Simulated docker stop/rm.")
        return True
    def get_resource_status(self, provisioned_info: ProvisionedResource) -> str:
        # Placeholder: Get status using docker ps or SDK
        return random.choice(["running", "stopped"]) # Simulate

# --- Add Placeholder Handlers for Kubernetes, Libvirt, AWS, GCP, Azure, PrivateCloud ---
# Example Kubernetes Handler structure
class KubernetesHandler(ResourceHandlerBase):
    def _connect(self) -> Any:
        logger.info("Conceptual: Initializing Kubernetes client...")
        # try: config.load_kube_config(); return client.AppsV1Api() # Example: Apps API
        # except Exception as e: logger.error(f"K8s client init error: {e}"); return None
        return "mock_k8s_apps_api_client"
    def provision_resource(self, definition: ResourceDefinition, instance_id_tag: str) -> ProvisionedResource:
        logger.info(f"KubernetesHandler: Provisioning resource from manifest/template '{definition['source_image_or_template']}'...")
        # --- Placeholder: kubectl apply / client library create ---
        # 1. Load YAML definition from definition['source_image_or_template']
        # 2. Modify metadata (e.g., add instance_id_tag label/annotation, set namespace)
        # 3. Use client library (e.g., self.client.create_namespaced_deployment) to create resource
        # 4. Wait for resource (e.g., Pod) to be ready
        # 5. Get connection info (e.g., Service IP/port, NodePort)
        # --- End Placeholder ---
        mock_id = f"k8s-pod-{definition['resource_id']}-{uuid.uuid4().hex[:4]}"
        logger.info(f"  - Simulated kubectl apply, Pod Name: {mock_id}")
        return ProvisionedResource(
             instance_specific_id=mock_id, resource_definition_id=definition['resource_id'],
             backend='kubernetes', status='running', connection_info={'cluster_ip': f'10.96.1.{random.randint(10,250)}', 'port': 80},
             provision_timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
             last_check_timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
             associated_scenario_instance_id=instance_id_tag
        )
    def deprovision_resource(self, provisioned_info: ProvisionedResource) -> bool:
        logger.info(f"KubernetesHandler: Deprovisioning resource '{provisioned_info['instance_specific_id']}'...")
        # --- Placeholder: kubectl delete / client library delete ---
        # Use K8s client library (e.g., self.client.delete_namespaced_deployment) based on resource type and name/id
        # --- End Placeholder ---
        logger.info("  - Simulated kubectl delete.")
        return True
    def get_resource_status(self, provisioned_info: ProvisionedResource) -> str:
        # Placeholder: Use client library to get Pod/Deployment status
        return random.choice(["running", "pending", "succeeded", "failed"]) # Simulate

# --- ResourceManager Class ---

class ResourceManager:
    """
    Manages the lifecycle of infrastructure resources for cyber range scenarios.

    Abstracts different backend providers (Docker, K8s, Cloud, etc.)
    and tracks provisioned resources associated with scenario instances.
    """
    DEFAULT_DEFINITIONS_PATH = "./cyber_range/resource_definitions.json" # Example path for definitions
    DEFAULT_STATE_PATH = "./data/cyber_range_provisioned_state.json" # Example path for state

    def __init__(self,
                 definitions_path: Optional[str] = None,
                 state_path: Optional[str] = None,
                 cloud_integrations: Optional[Dict[str, Any]] = None): # Pass AWS/GCP/Azure clients if used
        """
        Initializes the ResourceManager.

        Args:
            definitions_path (Optional[str]): Path to resource definitions file/directory.
            state_path (Optional[str]): Path to file for persisting provisioned state.
            cloud_integrations (Optional[Dict[str, Any]]): Dictionary holding initialized
                                                           cloud integration clients (AWSIntegration, etc.).
        """
        self.definitions_path = definitions_path or self.DEFAULT_DEFINITIONS_PATH
        self.state_path = state_path or self.DEFAULT_STATE_PATH
        # {resource_definition_id: ResourceDefinition}
        self.resource_definitions: Dict[str, ResourceDefinition] = {}
        # {scenario_instance_id: List[ProvisionedResource]}
        self.provisioned_state: Dict[str, List[ProvisionedResource]] = {}
        # Backend handlers {backend_name: HandlerInstance}
        self.handlers: Dict[str, ResourceHandlerBase] = {}
        self._lock = threading.Lock() # For thread-safe state modification

        self._load_resource_definitions()
        self._load_provisioned_state()
        self._initialize_handlers(cloud_integrations or {}) # Initialize handlers based on available backends/config
        logger.info("ResourceManager initialized.")

    def _initialize_handlers(self, cloud_integrations: Dict[str, Any]):
        """Initialize handlers for configured/available backends."""
        logger.info("Initializing resource handlers...")
        # Conceptual: Check config or available SDKs to decide which handlers to enable
        # Docker
        try:
            import docker # Check if available
            self.handlers['docker'] = DockerHandler({}) # Pass config if needed
            logger.info("  - Docker handler initialized.")
        except ImportError: logger.info("  - Docker SDK not found, Docker handler disabled.")
        # Kubernetes
        try:
            from kubernetes import config # Check if available
            self.handlers['kubernetes'] = KubernetesHandler({}) # Pass config if needed
            logger.info("  - Kubernetes handler initialized.")
        except ImportError: logger.info("  - Kubernetes client not found, Kubernetes handler disabled.")
        # Cloud Handlers (requires passing pre-configured clients)
        # Example:
        # if 'aws' in cloud_integrations:
        #     self.handlers['aws'] = AWSCloudHandler({'client': cloud_integrations['aws']})
        #     logger.info("  - AWS Cloud handler initialized.")
        # if 'gcp' in cloud_integrations:
        #     self.handlers['gcp'] = GCPCloudHandler({'client': cloud_integrations['gcp']})
        #     logger.info("  - GCP Cloud handler initialized.")
        # Add Libvirt, VMware, OpenStack handlers similarly if needed...
        logger.info(f"Initialized {len(self.handlers)} resource handlers: {list(self.handlers.keys())}")


    def _load_resource_definitions(self):
        """Loads resource definitions from file/directory (conceptual)."""
        logger.info(f"Loading resource definitions from '{self.definitions_path}'...")
        # Example: Load from a JSON file {resource_id: definition_dict}
        # In reality, could scan a directory of YAML/JSON files.
        if os.path.exists(self.definitions_path) and self.definitions_path.endswith(".json"):
             try:
                 with open(self.definitions_path, 'r') as f:
                      defs_raw = json.load(f)
                      # Basic validation could happen here
                      self.resource_definitions = defs_raw # Assume format is correct for now
                 logger.info(f"Loaded {len(self.resource_definitions)} resource definitions.")
             except (IOError, json.JSONDecodeError) as e:
                 logger.error(f"Failed to load resource definitions from '{self.definitions_path}': {e}")
                 self.resource_definitions = {}
        else:
             logger.warning(f"Resource definition source '{self.definitions_path}' not found or not a JSON file. Using defaults.")
             # Add default/dummy definitions if file not found
             self.resource_definitions = {
                 "kali_tools_container": {"resource_id": "kali_tools_container", "type": "container", "backend": "docker", "source_image_or_template": "kalilinux/kali-rolling", "compute_specs": {"memory_mb": 2048}, "misc_config": {"command": ["sleep", "infinity"]}},
                 "vuln_webapp_container": {"resource_id": "vuln_webapp_container", "type": "container", "backend": "docker", "source_image_or_template": "vulnhub/juiceshop:latest", "misc_config": {"ports": [{"containerPort": 3000, "hostPort": 8080}]}},
                 "ad_dc_vm": {"resource_id": "ad_dc_vm", "type": "vm", "backend": "kubernetes", "source_image_or_template": "manifests/ad-dc-deployment.yaml", "compute_specs": {"cpu": "1", "memory_mb": 4096}},
                 # Add more examples...
             }
             logger.info(f"Loaded {len(self.resource_definitions)} default/dummy definitions.")


    def _load_provisioned_state(self):
        """Loads the state of currently provisioned resources."""
        if not os.path.exists(self.state_path):
            logger.info(f"Provisioned state file '{self.state_path}' not found. Starting fresh.")
            self.provisioned_state = {}
            return
        try:
            with open(self.state_path, 'r') as f:
                self.provisioned_state = json.load(f)
            logger.info(f"Loaded provisioned state for {len(self.provisioned_state)} instances from '{self.state_path}'.")
            # TODO: Should potentially reconcile this state with actual backend state on startup? Complex.
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load provisioned state from '{self.state_path}': {e}. Resetting state.")
            self.provisioned_state = {}

    def _save_provisioned_state(self):
        """Saves the current state of provisioned resources."""
        # Add locking for thread safety if accessed concurrently
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
                with open(self.state_path, 'w') as f:
                    json.dump(self.provisioned_state, f, indent=2)
                # logger.debug("Saved provisioned state.")
            except IOError as e:
                logger.error(f"Failed to save provisioned state to '{self.state_path}': {e}")

# --- ResourceManager Class Continued ---

    def provision(self,
                  instance_id: str, # Unique ID for this provisioning request (e.g., scenario instance ID)
                  resource_identifiers: List[str],
                  setup_script: Optional[str] = None,
                  context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Provisions a set of resources defined by their identifiers for a specific instance.

        Args:
            instance_id (str): A unique ID identifying this instance of provisioned resources.
            resource_identifiers (List[str]): List of resource definition IDs to provision.
            setup_script (Optional[str]): Path to a script to run after resources are up (conceptual).
            context (Optional[Dict[str, Any]]): Additional context (user ID, scenario name).

        Returns:
            Dict[str, Any]: A dictionary containing the status ('success' or 'failed'),
                            a message, and potentially 'outputs' with connection info.
        """
        logger.info(f"Provisioning resources for instance '{instance_id}': {resource_identifiers}")
        with self._lock:
            if instance_id in self.provisioned_state:
                 msg = f"Instance ID '{instance_id}' already exists in provisioned state. Deprovision first or use a unique ID."
                 logger.error(msg)
                 return {"status": "failed", "message": msg}

            provisioned_resources_info: List[ProvisionedResource] = []
            success = True
            error_message = ""
            combined_connection_info = {}

            for res_id in resource_identifiers:
                definition = self.resource_definitions.get(res_id)
                if not definition:
                    error_message = f"Resource definition '{res_id}' not found."
                    logger.error(f"Instance '{instance_id}': {error_message}")
                    success = False
                    break # Stop provisioning if definition missing

                backend_name = definition.get('backend')
                handler = self.handlers.get(backend_name)
                if not handler:
                    error_message = f"No available handler for backend '{backend_name}' required by resource '{res_id}'."
                    logger.error(f"Instance '{instance_id}': {error_message}")
                    success = False
                    break # Stop provisioning if handler missing

                logger.info(f"Instance '{instance_id}': Provisioning '{res_id}' using handler '{backend_name}'...")
                try:
                    provisioned_info = handler.provision_resource(definition, instance_id)
                    provisioned_resources_info.append(provisioned_info)
                    combined_connection_info[res_id] = provisioned_info.get("connection_info", {}) # Aggregate connection info
                    logger.info(f"  - Resource '{res_id}' provisioned successfully (ID: {provisioned_info['instance_specific_id']}).")
                except Exception as e:
                    error_message = f"Failed to provision resource '{res_id}' using handler '{backend_name}': {e}"
                    logger.exception(f"Instance '{instance_id}': {error_message}") # Log traceback
                    success = False
                    break # Stop provisioning on first failure

            # --- Cleanup or Finalize ---
            if success:
                self.provisioned_state[instance_id] = provisioned_resources_info
                self._save_provisioned_state()
                logger.info(f"Instance '{instance_id}': All {len(provisioned_resources_info)} resources provisioned successfully.")
                # --- Conceptual: Run Setup Script ---
                if setup_script:
                    logger.info(f"Instance '{instance_id}': Running setup script '{setup_script}' (Conceptual)...")
                    # Example: self._run_setup_script(instance_id, setup_script, combined_connection_info)
                # --- End Conceptual ---
                return {"status": "success", "message": "Resources provisioned.", "outputs": combined_connection_info}
            else:
                # Provisioning failed, attempt rollback/cleanup of already created resources for this instance
                logger.error(f"Instance '{instance_id}': Provisioning failed. Attempting cleanup...")
                cleanup_success = True
                for provisioned in reversed(provisioned_resources_info): # Deprovision in reverse order
                    backend_name = provisioned.get('backend')
                    handler = self.handlers.get(backend_name)
                    if handler:
                         logger.warning(f"  - Cleaning up failed provision: Deprovisioning '{provisioned['instance_specific_id']}' via '{backend_name}'...")
                         try:
                             if not handler.deprovision_resource(provisioned):
                                  logger.error(f"    - Cleanup failed for resource ID '{provisioned['instance_specific_id']}'. Manual cleanup might be required.")
                                  cleanup_success = False
                         except Exception as e:
                              logger.error(f"    - Error during cleanup for resource ID '{provisioned['instance_specific_id']}': {e}. Manual cleanup might be required.")
                              cleanup_success = False
                if instance_id in self.provisioned_state:
                     del self.provisioned_state[instance_id] # Remove partial state
                self._save_provisioned_state()
                return {"status": "failed", "message": f"Provisioning failed: {error_message}. Cleanup attempt: {'Partial' if not cleanup_success else 'OK'}"}


    def deprovision(self, instance_id: str) -> bool:
        """
        Deprovisions all resources associated with a specific instance ID.

        Args:
            instance_id (str): The unique ID of the instance whose resources should be deprovisioned.

        Returns:
            bool: True if deprovisioning of all associated resources was attempted successfully,
                  False if the instance wasn't found or any deprovisioning step failed.
        """
        logger.info(f"Deprovisioning all resources for instance '{instance_id}'...")
        with self._lock:
            if instance_id not in self.provisioned_state:
                 logger.warning(f"Instance ID '{instance_id}' not found in provisioned state. Nothing to deprovision.")
                 return True # Consider it success if nothing to do

            resources_to_deprovision = self.provisioned_state.get(instance_id, [])
            overall_success = True

            logger.info(f"Found {len(resources_to_deprovision)} resources to deprovision for instance '{instance_id}'.")

            for resource_info in reversed(resources_to_deprovision): # Deprovision in reverse order of provision
                backend_name = resource_info.get('backend')
                handler = self.handlers.get(backend_name)
                resource_spec_id = resource_info['instance_specific_id']

                if handler:
                    logger.info(f"  - Deprovisioning '{resource_spec_id}' (Def: {resource_info['resource_definition_id']}) via '{backend_name}'...")
                    try:
                        if not handler.deprovision_resource(resource_info):
                             logger.error(f"    - Deprovisioning failed for resource ID '{resource_spec_id}'. Manual cleanup might be required.")
                             overall_success = False
                    except Exception as e:
                         logger.error(f"    - Error during deprovisioning for resource ID '{resource_spec_id}': {e}. Manual cleanup might be required.")
                         overall_success = False
                else:
                    logger.error(f"  - Cannot deprovision '{resource_spec_id}': No handler found for backend '{backend_name}'. Manual cleanup required.")
                    overall_success = False

            # Remove the instance from state regardless of individual deprovisioning success,
            # as errors indicate manual cleanup needed anyway.
            del self.provisioned_state[instance_id]
            self._save_provisioned_state()

            if overall_success:
                 logger.info(f"Successfully deprovisioned all tracked resources for instance '{instance_id}'.")
            else:
                 logger.warning(f"Completed deprovisioning attempt for instance '{instance_id}' with one or more errors. Manual verification/cleanup may be needed.")

            return overall_success


    def get_instance_resources(self, instance_id: str) -> Optional[List[ProvisionedResource]]:
        """
        Retrieves the list of resources currently provisioned for a given instance ID.
        """
        logger.debug(f"Getting provisioned resource list for instance '{instance_id}'...")
        with self._lock: # Ensure reading state is safe if saving happens concurrently
             return self.provisioned_state.get(instance_id, None)


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- Resource Manager Example (Conceptual) ---")

    # Create dummy definition file
    defs_file = "./temp_resource_defs.json"
    state_file = "./temp_resource_state.json"
    dummy_defs_content = {
        "kali_tools_container": {"resource_id": "kali_tools_container", "type": "container", "backend": "docker", "source_image_or_template": "kalilinux/kali-rolling", "compute_specs": {"memory_mb": 2048}, "misc_config": {"command": ["sleep", "infinity"]}},
        "vuln_webapp_container": {"resource_id": "vuln_webapp_container", "type": "container", "backend": "docker", "source_image_or_template": "vulnhub/juiceshop:latest", "misc_config": {"ports": [{"containerPort": 3000, "hostPort": 8080}]}},
        "k8s_nginx": {"resource_id": "k8s_nginx", "type": "deployment", "backend": "kubernetes", "source_image_or_template": "manifests/nginx.yaml"}
    }
    if os.path.exists(state_file): os.remove(state_file)
    with open(defs_file, 'w') as f: json.dump(dummy_defs_content, f, indent=2)

    # Initialize manager (will use dummy handlers if SDKs not installed)
    resource_manager = ResourceManager(definitions_path=defs_file, state_path=state_file)

    # Provision resources for a scenario instance
    instance_id_1 = f"scn_inst_{uuid.uuid4().hex[:6]}"
    resources_to_provision = ["kali_tools_container", "vuln_webapp_container"] # Only docker resources
    print(f"\nProvisioning resources for instance '{instance_id_1}': {resources_to_provision}")

    provision_result = resource_manager.provision(instance_id_1, resources_to_provision)
    print("\nProvisioning Result:")
    print(json.dumps(provision_result, indent=2))

    # Get the state of provisioned resources
    if provision_result.get("status") == "success":
        print(f"\nGetting resources for instance '{instance_id_1}':")
        instance_resources = resource_manager.get_instance_resources(instance_id_1)
        if instance_resources:
             print(json.dumps(instance_resources, indent=2))
        else:
             print("  - No resources found (unexpected).")

        # Deprovision the resources
        print(f"\nDeprovisioning resources for instance '{instance_id_1}':")
        deprovision_ok = resource_manager.deprovision(instance_id_1)
        print(f"Deprovisioning successful: {deprovision_ok}")

        # Verify state is cleared
        print("\nGetting resources after deprovisioning:")
        instance_resources_after = resource_manager.get_instance_resources(instance_id_1)
        print(f"  - Resources found: {instance_resources_after}") # Should be None or empty list

    # Clean up dummy files
    if os.path.exists(defs_file): os.remove(defs_file)
    if os.path.exists(state_file): os.remove(state_file)


    print("\n--- End Example ---")
