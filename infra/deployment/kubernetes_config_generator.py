# Devin/infra/deployment/kubernetes_config_generator.py
# Purpose: Generates Kubernetes deployment configurations (YAML) for Devin components.

import logging
import os
import sys
from typing import Dict, Any, List, Optional, Literal

# --- YAML Library Import ---
# Requires: pip install pyyaml
try:
    import yaml
    PYYAML_AVAILABLE = True
    print("Conceptual: 'PyYAML' library assumed available for YAML generation.")
except ImportError:
    yaml = None # type: ignore
    PYYAML_AVAILABLE = False
    print("WARNING: 'PyYAML' library not found. YAML output will be non-functional.")

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("K8sConfigGenerator")

# --- Default Values and Constants ---
DEFAULT_K8S_API_VERSION_DEPLOYMENT = "apps/v1"
DEFAULT_K8S_API_VERSION_SERVICE = "v1"
DEFAULT_K8S_API_VERSION_CONFIGMAP = "v1"
DEFAULT_K8S_API_VERSION_PVC = "v1"

class K8sConfigGenerator:
    """
    Generates Kubernetes YAML configurations for various Devin components.
    """

    def __init__(self,
                 namespace: str = "devin-services",
                 default_app_label: str = "devin-app",
                 default_image_pull_policy: str = "IfNotPresent"):
        """
        Initializes the Kubernetes Config Generator.

        Args:
            namespace (str): Default Kubernetes namespace for generated resources.
            default_app_label (str): Default base label value for 'app' (e.g., 'devin-api', 'devin-worker').
            default_image_pull_policy (str): Default image pull policy for containers.
        """
        self.namespace = namespace
        self.default_app_label = default_app_label
        self.default_image_pull_policy = default_image_pull_policy
        logger.info(f"K8sConfigGenerator initialized. Default Namespace: '{namespace}', App Label: '{default_app_label}'")
        if not PYYAML_AVAILABLE:
            logger.error("PyYAML library is not available. YAML dumping will not work.")

    def _generate_metadata(self,
                           name: str,
                           custom_labels: Optional[Dict[str, str]] = None,
                           annotations: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Helper to generate the 'metadata' section for K8s objects."""
        metadata: Dict[str, Any] = {
            "name": name,
            "namespace": self.namespace,
            "labels": { # Default labels
                "app.kubernetes.io/name": name, # Specific instance name
                "app.kubernetes.io/part-of": self.default_app_label # Belongs to the "devin" app suite
            }
        }
        if custom_labels:
            metadata["labels"].update(custom_labels)
        if annotations:
            metadata["annotations"] = annotations
        return metadata

    def _generate_selector(self, match_labels: Dict[str, str]) -> Dict[str, Any]:
        """Helper to generate a 'selector' block."""
        return {"matchLabels": match_labels}

    def _generate_probe(self,
                        probe_type: Literal["httpGet", "tcpSocket", "exec"],
                        path_or_port_or_command: Union[str, int, List[str]],
                        initial_delay_seconds: int = 30,
                        period_seconds: int = 10,
                        timeout_seconds: int = 5,
                        success_threshold: int = 1,
                        failure_threshold: int = 3,
                        scheme: Optional[str] = "HTTP" # For httpGet
                        ) -> Dict[str, Any]:
        """Helper to generate a liveness or readiness probe configuration."""
        probe_config: Dict[str, Any] = {}
        if probe_type == "httpGet":
            probe_config["httpGet"] = {"path": str(path_or_port_or_command), "port": "http", "scheme": scheme} # Assume port name 'http'
        elif probe_type == "tcpSocket":
            probe_config["tcpSocket"] = {"port": int(path_or_port_or_command)}
        elif probe_type == "exec":
            probe_config["exec"] = {"command": path_or_port_or_command}
        else:
            raise ValueError(f"Unsupported probe type: {probe_type}")

        probe_config.update({
            "initialDelaySeconds": initial_delay_seconds,
            "periodSeconds": period_seconds,
            "timeoutSeconds": timeout_seconds,
            "successThreshold": success_threshold,
            "failureThreshold": failure_threshold,
        })
        return probe_config

    def _generate_container_spec(self,
                                 container_name: str,
                                 image_name: str,
                                 image_tag: str = "latest",
                                 container_ports: Optional[List[Dict[str, Any]]] = None, # e.g., [{"name": "http", "containerPort": 80}]
                                 env_vars: Optional[List[Dict[str, Any]]] = None, # e.g., [{"name": "MY_VAR", "value": "my_value"}] or from ConfigMap/Secret
                                 volume_mounts: Optional[List[Dict[str, Any]]] = None, # e.g., [{"name": "config-volume", "mountPath": "/etc/config"}]
                                 resources: Optional[Dict[str, Any]] = None, # e.g., {"requests": {"cpu": "100m", "memory": "128Mi"}, "limits": {...}}
                                 liveness_probe_config: Optional[Dict[str, Any]] = None, # Generated by _generate_probe
                                 readiness_probe_config: Optional[Dict[str, Any]] = None, # Generated by _generate_probe
                                 image_pull_policy: Optional[str] = None
                                 ) -> Dict[str, Any]:
        """Helper to generate a container specification for a Deployment or Pod."""
        spec = {
            "name": container_name,
            "image": f"{image_name}:{image_tag}",
            "imagePullPolicy": image_pull_policy or self.default_image_pull_policy,
        }
        if container_ports: spec["ports"] = container_ports
        if env_vars: spec["env"] = env_vars
        if volume_mounts: spec["volumeMounts"] = volume_mounts
        if resources: spec["resources"] = resources
        if liveness_probe_config: spec["livenessProbe"] = liveness_probe_config
        if readiness_probe_config: spec["readinessProbe"] = readiness_probe_config
        return spec

    # --- Deployment Generator ---
    def generate_deployment_dict(self,
                                 name: str,
                                 image_name: str,
                                 image_tag: str = "latest",
                                 replicas: int = 1,
                                 container_name_override: Optional[str] = None,
                                 container_ports: Optional[List[Dict[str, Any]]] = None, # e.g., [{"name": "http", "containerPort": 8080}]
                                 labels: Optional[Dict[str, str]] = None, # Additional labels for metadata AND selector
                                 annotations: Optional[Dict[str, str]] = None,
                                 env_vars: Optional[List[Dict[str, Any]]] = None,
                                 volumes: Optional[List[Dict[str, Any]]] = None, # e.g., [{"name": "config-volume", "configMap": {"name": "my-configmap"}}]
                                 volume_mounts: Optional[List[Dict[str, Any]]] = None,
                                 resources: Optional[Dict[str, Any]] = None,
                                 liveness_probe: Optional[Dict[str, Any]] = None, # Directly pass the probe config dict
                                 readiness_probe: Optional[Dict[str, Any]] = None,
                                 strategy: Optional[Dict[str, Any]] = None # e.g. {"type": "RollingUpdate", "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}
                                 ) -> Dict[str, Any]:
        """
        Generates a Kubernetes Deployment object as a Python dictionary.

        Args:
            name (str): Name of the Deployment (e.g., "devin-api-server").
            image_name (str): Docker image name (e.g., "devin/api-server").
            image_tag (str): Docker image tag.
            replicas (int): Number of pod replicas.
            container_name_override (Optional[str]): Name for the container within the pod, defaults to `name`.
            container_ports (Optional[List[Dict]]): List of container port mappings.
            labels (Optional[Dict]): Custom labels to apply. Base 'app' label will be `name`.
            annotations (Optional[Dict]): Annotations for the Deployment.
            env_vars (Optional[List[Dict]]): Environment variables for the container.
            volumes (Optional[List[Dict]]): Volumes to define for the Pod.
            volume_mounts (Optional[List[Dict]]): Volume mounts for the container.
            resources (Optional[Dict]): Resource requests/limits for the container.
            liveness_probe (Optional[Dict]): Liveness probe configuration dictionary.
            readiness_probe (Optional[Dict]): Readiness probe configuration dictionary.
            strategy (Optional[Dict]): Deployment strategy.

        Returns:
            Dict[str, Any]: A dictionary representing the Kubernetes Deployment YAML.
        """
        logger.info(f"Generating K8s Deployment config for: {name}")
        container_name = container_name_override or name
        final_labels = {"app": name} # Main label for matching service selector
        if labels:
            final_labels.update(labels)

        metadata = self._generate_metadata(name, custom_labels=final_labels, annotations=annotations)
        selector_labels = final_labels.copy() # Selector should match these pod labels

        container_spec = self._generate_container_spec(
            container_name=container_name,
            image_name=image_name,
            image_tag=image_tag,
            container_ports=container_ports,
            env_vars=env_vars,
            volume_mounts=volume_mounts,
            resources=resources,
            liveness_probe_config=liveness_probe,
            readiness_probe_config=readiness_probe,
            image_pull_policy=self.default_image_pull_policy
        )

        pod_template_metadata_labels = final_labels.copy()
        pod_template_metadata_labels["app.kubernetes.io/name"] = name # For pod metadata
        pod_template_metadata_labels["app.kubernetes.io/part-of"] = self.default_app_label

        deployment_dict = {
            "apiVersion": DEFAULT_K8S_API_VERSION_DEPLOYMENT,
            "kind": "Deployment",
            "metadata": metadata,
            "spec": {
                "replicas": replicas,
                "selector": self._generate_selector(selector_labels),
                "template": {
                    "metadata": {
                        "labels": pod_template_metadata_labels
                    },
                    "spec": {
                        "containers": [container_spec]
                    }
                }
            }
        }

        if strategy:
            deployment_dict["spec"]["strategy"] = strategy
        if volumes:
            deployment_dict["spec"]["template"]["spec"]["volumes"] = volumes
        # Add other spec fields like serviceAccountName, affinity, tolerations etc. as needed

        return deployment_dict

import logging
import os
import sys
from typing import Dict, Any, List, Optional, Literal, Union # Ensure Union is imported

# --- YAML Library Import (from Part 1) ---
try:
    import yaml
    PYYAML_AVAILABLE = True
except ImportError:
    yaml = None # type: ignore
    PYYAML_AVAILABLE = False

# Logger (from Part 1)
logger = logging.getLogger("K8sConfigGenerator")

# Default API Versions (from Part 1)
DEFAULT_K8S_API_VERSION_DEPLOYMENT = "apps/v1"
DEFAULT_K8S_API_VERSION_SERVICE = "v1"
DEFAULT_K8S_API_VERSION_CONFIGMAP = "v1"
DEFAULT_K8S_API_VERSION_PVC = "v1"


class K8sConfigGenerator:
    # (Assume __init__, _generate_metadata, _generate_selector, _generate_probe,
    #  _generate_container_spec, and generate_deployment_dict from Part 1 are here)

    # --- Service Generator ---
    def generate_service_dict(self,
                              name: str, # e.g., "devin-api-service"
                              selector_labels: Dict[str, str], # Labels to match Pods from a Deployment, e.g., {"app": "devin-api-server"}
                              ports: List[Dict[str, Any]], # e.g., [{"name": "http", "port": 80, "targetPort": 8080, "protocol": "TCP"}]
                              service_type: Literal["ClusterIP", "NodePort", "LoadBalancer", "ExternalName"] = "ClusterIP",
                              custom_labels: Optional[Dict[str, str]] = None,
                              annotations: Optional[Dict[str, str]] = None,
                              cluster_ip: Optional[str] = None, # Only for ClusterIP if specific IP needed (rarely)
                              external_name: Optional[str] = None # Only for ExternalName type
                              ) -> Dict[str, Any]:
        """
        Generates a Kubernetes Service object as a Python dictionary.

        Args:
            name (str): Name of the Service.
            selector_labels (Dict[str, str]): Labels used by the Service to select Pods.
                                              MUST match labels on the Pods targeted by this Service.
            service_type (str): Type of Service (ClusterIP, NodePort, LoadBalancer, ExternalName).
            ports (List[Dict]): List of port mappings. Each dict should define 'port', 'targetPort',
                                 optionally 'protocol' (TCP/UDP), and 'name'.
            custom_labels (Optional[Dict]): Custom labels for the Service metadata.
            annotations (Optional[Dict]): Annotations for the Service metadata.
            cluster_ip (Optional[str]): Specific ClusterIP to assign (if type is ClusterIP and not 'None').
            external_name (Optional[str]): External DNS name (if type is ExternalName).

        Returns:
            Dict[str, Any]: A dictionary representing the Kubernetes Service YAML.
        """
        logger.info(f"Generating K8s Service config for: {name} (Type: {service_type})")
        metadata = self._generate_metadata(name, custom_labels=custom_labels, annotations=annotations)

        spec: Dict[str, Any] = {
            "type": service_type,
            "ports": ports
        }
        # Selector is not used for ExternalName services
        if service_type != "ExternalName":
            spec["selector"] = selector_labels
        
        if service_type == "ClusterIP" and cluster_ip:
            spec["clusterIP"] = cluster_ip
        if service_type == "ExternalName" and external_name:
            spec["externalName"] = external_name
        elif service_type == "ExternalName" and not external_name:
            logger.warning(f"Service '{name}' is of type ExternalName but no 'external_name' was provided.")


        service_dict = {
            "apiVersion": DEFAULT_K8S_API_VERSION_SERVICE,
            "kind": "Service",
            "metadata": metadata,
            "spec": spec
        }
        return service_dict

    # --- ConfigMap Generator ---
    def generate_configmap_dict(self,
                                name: str, # e.g., "devin-api-config"
                                data: Dict[str, str], # Key-value pairs for the ConfigMap data
                                custom_labels: Optional[Dict[str, str]] = None,
                                immutable: Optional[bool] = None # K8s 1.19+
                                ) -> Dict[str, Any]:
        """
        Generates a Kubernetes ConfigMap object as a Python dictionary.

        Args:
            name (str): Name of the ConfigMap.
            data (Dict[str, str]): Dictionary where keys are filenames (or keys) and
                                   values are their string content.
            custom_labels (Optional[Dict]): Custom labels for the ConfigMap metadata.
            immutable (Optional[bool]): If true, the ConfigMap is immutable.

        Returns:
            Dict[str, Any]: A dictionary representing the Kubernetes ConfigMap YAML.
        """
        logger.info(f"Generating K8s ConfigMap config for: {name}")
        metadata = self._generate_metadata(name, custom_labels=custom_labels)
        configmap_dict: Dict[str, Any] = {
            "apiVersion": DEFAULT_K8S_API_VERSION_CONFIGMAP,
            "kind": "ConfigMap",
            "metadata": metadata,
            "data": data
        }
        if immutable is not None:
             configmap_dict["immutable"] = immutable
        return configmap_dict

    # --- PersistentVolumeClaim (PVC) Generator ---
    def generate_pvc_dict(self,
                          name: str, # e.g., "devin-database-pvc"
                          size: str, # e.g., "10Gi", "100Mi"
                          access_modes: List[Literal["ReadWriteOnce", "ReadOnlyMany", "ReadWriteMany", "ReadWriteOncePod"]],
                          storage_class_name: Optional[str] = None, # Name of the StorageClass
                          custom_labels: Optional[Dict[str, str]] = None,
                          annotations: Optional[Dict[str, str]] = None
                          ) -> Dict[str, Any]:
        """
        Generates a Kubernetes PersistentVolumeClaim object as a Python dictionary.

        Args:
            name (str): Name of the PVC.
            size (str): Requested storage size (e.g., "5Gi", "1Ti").
            access_modes (List[str]): Access modes (e.g., ["ReadWriteOnce"]).
            storage_class_name (Optional[str]): Name of the StorageClass to use. If None, default SC is used.
            custom_labels (Optional[Dict]): Custom labels for the PVC metadata.
            annotations (Optional[Dict]): Annotations for the PVC metadata.

        Returns:
            Dict[str, Any]: A dictionary representing the Kubernetes PVC YAML.
        """
        logger.info(f"Generating K8s PersistentVolumeClaim config for: {name} (Size: {size})")
        metadata = self._generate_metadata(name, custom_labels=custom_labels, annotations=annotations)
        spec: Dict[str, Any] = {
            "accessModes": access_modes,
            "resources": {
                "requests": {
                    "storage": size
                }
            }
        }
        if storage_class_name:
            spec["storageClassName"] = storage_class_name

        pvc_dict = {
            "apiVersion": DEFAULT_K8S_API_VERSION_PVC,
            "kind": "PersistentVolumeClaim",
            "metadata": metadata,
            "spec": spec
        }
        return pvc_dict

    # --- YAML Output Utilities ---
    def dump_to_yaml_string(self, k8s_object_dict: Dict[str, Any], sort_keys: bool = False) -> str:
        """Converts a Python dictionary representing a K8s object to a YAML string."""
        if not yaml:
            logger.error("Cannot dump to YAML string: PyYAML library not available.")
            return json.dumps(k8s_object_dict, indent=2) # Fallback to JSON string

        try:
            return yaml.dump(k8s_object_dict, sort_keys=sort_keys, indent=2, Dumper=yaml.SafeDumper)
        except Exception as e:
            logger.error(f"Error dumping dictionary to YAML: {e}")
            return ""

    def save_to_yaml_file(self,
                          k8s_object_dict: Dict[str, Any],
                          filename: str,
                          output_dir: str = "./k8s_configs_generated",
                          sort_keys: bool = False) -> bool:
        """Saves a K8s object dictionary to a YAML file."""
        yaml_string = self.dump_to_yaml_string(k8s_object_dict, sort_keys=sort_keys)
        if not yaml_string:
            return False

        try:
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w') as f:
                f.write(yaml_string)
            logger.info(f"Saved K8s config to: {filepath}")
            return True
        except IOError as e:
            logger.error(f"Error saving YAML to file {filepath}: {e}")
            return False

    # --- Orchestration Method for a Devin Component ---
    def generate_devin_component_set(self,
                                     component_name: str, # e.g., "api-server", "task-worker"
                                     image_name: str,
                                     image_tag: str = "latest",
                                     replicas: int = 1,
                                     # Deployment specific
                                     container_ports_map: Optional[Dict[str, int]] = None, # {"http": 8080, "metrics": 9090}
                                     deployment_env_vars: Optional[List[Dict[str, Any]]] = None,
                                     deployment_volumes: Optional[List[Dict[str, Any]]] = None,
                                     deployment_volume_mounts: Optional[List[Dict[str, Any]]] = None,
                                     deployment_resources: Optional[Dict[str, Any]] = None,
                                     liveness_probe_spec: Optional[Dict[str, Any]] = None, # e.g. {"type": "httpGet", "path": "/healthz", "port": "http"}
                                     readiness_probe_spec: Optional[Dict[str, Any]] = None,
                                     # Service specific
                                     expose_service: bool = True,
                                     service_type: Literal["ClusterIP", "NodePort", "LoadBalancer"] = "ClusterIP",
                                     service_ports_map: Optional[Dict[str, Tuple[int, int]]] = None, # {"http": (80, 8080)} -> service_port, target_port
                                     # ConfigMap specific
                                     config_data: Optional[Dict[str, str]] = None,
                                     # PVC specific
                                     pvc_spec: Optional[Dict[str, Any]] = None, # {"name_suffix": "data", "size": "10Gi", "access_modes": ["ReadWriteOnce"], "storage_class": "standard"}
                                     common_labels: Optional[Dict[str, str]] = None
                                     ) -> List[Dict[str, Any]]:
        """
        Generates a set of K8s configurations (Deployment, Service, ConfigMap, PVC)
        for a specific Devin component.

        Returns:
            List[Dict[str, Any]]: A list of generated K8s object dictionaries.
        """
        base_name = f"{self.default_app_label}-{component_name}" # e.g., "devin-app-api-server"
        all_configs: List[Dict[str, Any]] = []
        
        final_common_labels = {"component": component_name}
        if common_labels:
            final_common_labels.update(common_labels)

        # --- Prepare Container Ports for Deployment ---
        dep_container_ports = []
        if container_ports_map:
            for name, port_num in container_ports_map.items():
                dep_container_ports.append({"name": name, "containerPort": port_num, "protocol": "TCP"}) # Assume TCP

        # --- Prepare Probes ---
        actual_liveness_probe = None
        if liveness_probe_spec:
             probe_port = liveness_probe_spec.get("port_name") or liveness_probe_spec.get("port_number") or (dep_container_ports[0]["name"] if dep_container_ports else None)
             if probe_port:
                 actual_liveness_probe = self._generate_probe(
                     probe_type=liveness_probe_spec["type"],
                     path_or_port_or_command=liveness_probe_spec.get("path") or probe_port or liveness_probe_spec.get("command"),
                     initial_delay_seconds=liveness_probe_spec.get("initial_delay_seconds", 60),
                     period_seconds=liveness_probe_spec.get("period_seconds", 15)
                 )
        actual_readiness_probe = None
        if readiness_probe_spec:
             probe_port = readiness_probe_spec.get("port_name") or readiness_probe_spec.get("port_number") or (dep_container_ports[0]["name"] if dep_container_ports else None)
             if probe_port:
                 actual_readiness_probe = self._generate_probe(
                     probe_type=readiness_probe_spec["type"],
                     path_or_port_or_command=readiness_probe_spec.get("path") or probe_port or readiness_probe_spec.get("command"),
                     initial_delay_seconds=readiness_probe_spec.get("initial_delay_seconds", 15),
                     period_seconds=readiness_probe_spec.get("period_seconds", 10)
                 )

        # 1. Generate Deployment
        deployment_dict = self.generate_deployment_dict(
            name=base_name,
            image_name=image_name,
            image_tag=image_tag,
            replicas=replicas,
            labels=final_common_labels, # These labels go on the Deployment itself and its Pod template
            container_ports=dep_container_ports,
            env_vars=deployment_env_vars,
            volumes=deployment_volumes,
            volume_mounts=deployment_volume_mounts,
            resources=deployment_resources,
            liveness_probe=actual_liveness_probe,
            readiness_probe=actual_readiness_probe
        )
        all_configs.append(deployment_dict)

        # 2. Generate Service (if requested)
        if expose_service and service_ports_map:
            svc_ports = []
            for name, (port_num, target_port_num_or_name) in service_ports_map.items():
                svc_ports.append({"name": name, "port": port_num, "targetPort": target_port_num_or_name, "protocol": "TCP"})

            # Service selector MUST match the labels on the Pods created by the Deployment
            # The 'app' label on the pod template of the deployment is `base_name`
            service_selector_labels = {"app": base_name}
            # If final_common_labels were intended for pod selection too, ensure they align.
            # Often, a simple `app: base_name` is sufficient for service selection.
            # For more complex scenarios, ensure pod labels and service selectors are correctly aligned.
            
            service_dict = self.generate_service_dict(
                name=f"{base_name}-svc",
                selector_labels=service_selector_labels, # Use the labels that are on the PODs
                service_type=service_type,
                ports=svc_ports,
                custom_labels=final_common_labels
            )
            all_configs.append(service_dict)

        # 3. Generate ConfigMap (if data provided)
        if config_data:
            configmap_dict = self.generate_configmap_dict(
                name=f"{base_name}-config",
                data=config_data,
                custom_labels=final_common_labels
            )
            all_configs.append(configmap_dict)

        # 4. Generate PVC (if spec provided)
        if pvc_spec:
            pvc_name = f"{base_name}-{pvc_spec.get('name_suffix', 'data')}-pvc"
            pvc_dict = self.generate_pvc_dict(
                name=pvc_name,
                size=pvc_spec["size"],
                access_modes=pvc_spec["access_modes"],
                storage_class_name=pvc_spec.get("storage_class"),
                custom_labels=final_common_labels
            )
            all_configs.append(pvc_dict)

        return all_configs


# Example Usage (conceptual)
if __name__ == "__main__":
    print("=========================================================")
    print("=== Running K8s Config Generator Prototype ===")
    print("=========================================================")
    if not PYYAML_AVAILABLE:
        print("\nPyYAML library not found. YAML output will be displayed as JSON fallback.")
        print("Please install it: pip install PyYAML")

    generator = K8sConfigGenerator(namespace="devin-production", default_app_label="devin")
    output_directory = "./k8s_configs_generated_devin"

    # --- Generate for Devin API Server ---
    print("\n--- Generating Configs for Devin API Server ---")
    api_server_configs = generator.generate_devin_component_set(
        component_name="api-server",
        image_name="devinai/api-server",
        image_tag="v0.2.1",
        replicas=3,
        container_ports_map={"http": 8080, "metrics": 9100},
        service_type="LoadBalancer",
        service_ports_map={"http": (80, 8080), "metrics-svc": (9100,9100)}, # service_port, target_port_num_or_name
        config_data={
            "API_TIMEOUT_MS": "5000",
            "LOG_LEVEL": "INFO",
            "WELCOME_MESSAGE": "Hello from Devin API deployed via K8s!"
        },
        deployment_env_vars=[
            {"name": "POD_NAMESPACE", "valueFrom": {"fieldRef": {"fieldPath": "metadata.namespace"}}},
            {"name": "API_CONFIG_PATH", "value": "/app/config/api.properties"} # Assumes ConfigMap mounted
        ],
        deployment_volumes=[ # Example: mount ConfigMap
            {"name": "api-config-volume", "configMap": {"name": f"{generator.default_app_label}-api-server-config"}} # Matches generated CM name
        ],
        deployment_volume_mounts=[
            {"name": "api-config-volume", "mountPath": "/app/config"}
        ],
        deployment_resources={
            "requests": {"cpu": "200m", "memory": "256Mi"},
            "limits": {"cpu": "1000m", "memory": "1Gi"}
        },
        liveness_probe_spec={"type": "httpGet", "path": "/healthz", "port_name": "http", "initial_delay_seconds": 60},
        readiness_probe_spec={"type": "httpGet", "path": "/readyz", "port_name": "http", "initial_delay_seconds": 20},
        common_labels={"tier": "backend", "environment": "production"}
    )
    for config in api_server_configs:
        print("---")
        print(generator.dump_to_yaml_string(config))
        filename = f"{config['metadata']['name']}-{config['kind'].lower()}.yaml"
        generator.save_to_yaml_file(config, filename, output_dir=output_directory)


    # --- Generate for Devin Task Worker ---
    print("\n--- Generating Configs for Devin Task Worker ---")
    worker_configs = generator.generate_devin_component_set(
        component_name="task-worker",
        image_name="devinai/task-worker",
        image_tag="v0.2.1",
        replicas=5,
        container_ports_map=None, # No service exposed directly for worker usually
        expose_service=False,
        config_data={"MAX_CONCURRENT_TASKS": "10", "QUEUE_NAME": "devin_task_queue"},
        pvc_spec={
            "name_suffix": "cache", # devin-app-task-worker-cache-pvc
            "size": "5Gi",
            "access_modes": ["ReadWriteOnce"], # Typical for a single pod or statefulset replica
            "storage_class": "standard-ssd" # Example storage class
        },
        deployment_env_vars=[{"name": "WORKER_ID", "valueFrom": {"fieldRef": {"fieldPath": "metadata.name"}}}],
        deployment_volumes=[ # Example: mount PVC
            {"name": "worker-cache-volume", "persistentVolumeClaim": {"claimName": f"{generator.default_app_label}-task-worker-cache-pvc"}}
        ],
        deployment_volume_mounts=[
            {"name": "worker-cache-volume", "mountPath": "/mnt/cache"}
        ],
        deployment_resources={"requests": {"cpu": "500m", "memory": "512Mi"}},
        common_labels={"tier": "processing", "environment": "production"}
    )

    for config in worker_configs:
        print("---")
        print(generator.dump_to_yaml_string(config))
        filename = f"{config['metadata']['name']}-{config['kind'].lower()}.yaml"
        generator.save_to_yaml_file(config, filename, output_dir=output_directory)

    print(f"\nGenerated K8s config files saved to '{os.path.abspath(output_directory)}' directory.")
    print("Review these YAML files. They are templates and may need further customization.")
    print("\n=========================================================")
    print("=== K8s Config Generator Prototype Complete ===")
    print("=========================================================")
