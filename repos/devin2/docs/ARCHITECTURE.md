# Devin AGI - System Architecture

## 1. Core Philosophy

The Devin AGI is designed as a **modular, agentic system**. Its architecture is built around a central "brain" (the `AIAgent`) that perceives its environment, formulates plans, and uses a suite of specialized "tools" to execute those plans. The system prioritizes security, extensibility, and clear separation of concerns.

---

## 2. Major Components

The project is divided into several key directories, each with a distinct responsibility:

-   **`servers/`**: Contains all backend, network-accessible services. These are typically Flask applications that expose a REST API to provide an abstraction layer over complex or hardware-dependent tasks (e.g., `CloudIntegrationServer`, `AILearningServer`).
-   **`modules/`**: The core logic of the AGI.
    -   **`ai_...`**: The AI "brain," including the central `AIAgent` and connectors to various LLM providers.
    -   **`automation_tools.py`**: High-level facades for controlling the desktop (`DesktopAutomator`) and web (`WebAutomator`).
    -   **`cloud_...`**: The cloud abstraction layer (`CloudFacade`) and its provider-specific tools.
    -   **`os_operations/`**: The OS abstraction layer (`UniversalOSOperator`) for cross-platform compatibility.
    -   **`pentesting_tools/`**: The offensive security toolchain (`PentestingFacade`, scanners, etc.).
    -   **`robotics/`**: The complete robotics stack, from low-level motor control to high-level navigation and perception.
-   **`singularity/`**: Contains the highest-level conceptual logic for the AGI, including its `UtilityFunction` for value-aligned decision-making and its `SelfModifyingCodeGenerator` for recursive self-improvement.
-   **`threat_intel/`**: The threat intelligence suite, providing knowledge about real-world cybersecurity threats (`MitreAttackDB`, `VirusTotalClient`, etc.).
-   **`security/`**: Contains modules directly related to the AGI's own security, such as the `SecurityDashboard`.
-   **`tests/`**: A comprehensive testing suite, including unit, integration, performance, and security tests.

---

## 3. The "Think-Act" Loop

Most operations follow a standardized "Think-Act" loop, orchestrated by a high-level agent.

```mermaid
sequenceDiagram
    participant User
    participant MainLoop (main.py)
    participant AIAgent
    participant ToolExecutor
    participant Tool # (e.g., CloudServicesManager)

    User->>MainLoop: "Stop all non-prod AWS VMs"
    MainLoop->>AIAgent: Formulate a plan for the goal.
    AIAgent->>AIAgent: (LLM Call) Decide first step is to list VMs.
    AIAgent-->>MainLoop: Plan: {"tool": "list_vms", "params": {"provider": "AWS"}}
    MainLoop->>ToolExecutor: Execute this tool call.
    ToolExecutor->>Tool: call list_vms("AWS")
    Tool-->>ToolExecutor: Returns list of VM data.
    ToolExecutor-->>MainLoop: Execution Result: [VM1, VM2, ...]
    MainLoop->>AIAgent: Plan for goal, with new context (VM list).
    AIAgent->>AIAgent: (LLM Call) Analyze list, decide to stop VM2.
    AIAgent-->>MainLoop: Plan: {"tool": "stop_vm", "params": {"id": "vm2_id"}}
    MainLoop->>ToolExecutor: Execute this tool call.
    ToolExecutor->>Tool: call stop_vm("vm2_id")
    Tool-->>ToolExecutor: Execution Result: {"status": "success"}
    ToolExecutor-->>MainLoop: Execution Result: {"status": "success"}
    MainLoop->>User: "Action complete. Stopped VM 'VM2'."
