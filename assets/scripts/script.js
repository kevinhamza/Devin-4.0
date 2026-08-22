// Devin/assets/scripts/script.js
// Main client-side JavaScript for interacting with the Devin backend API Gateway.

// Wait for the HTML document to be fully loaded before running scripts
document.addEventListener('DOMContentLoaded', function() {
    console.log("Devin Frontend JS Initialized.");

    // --- Configuration ---
    const API_BASE_URL = "/api"; // Assuming the API gateway is served relative to the frontend

    // --- DOM Element Placeholders ---
    // Get references to HTML elements (replace with actual IDs/selectors)
    const commandInput = document.getElementById('command-input');
    const submitButton = document.getElementById('submit-command-btn');
    const outputArea = document.getElementById('output-area');
    const statusIndicator = document.getElementById('status-indicator');
    const taskInputTarget = document.getElementById('task-input-target'); // e.g., for scan target
    const taskTypeSelector = document.getElementById('task-type-selector'); // e.g., dropdown for scan type
    const startTaskButton = document.getElementById('start-task-btn');

    // --- Authentication Token Handling (Placeholder) ---
    function getAuthToken() {
        // CRITICAL: Implement secure token retrieval (e.g., from localStorage, sessionStorage after login)
        // This is essential for calling protected API endpoints.
        const token = localStorage.getItem('devinAuthToken'); // Example
        if (!token) {
            console.warn("Auth token not found. API calls to protected endpoints will likely fail.");
        }
        // Return in the format expected by the API (e.g., 'Bearer <token>')
        return token ? `Bearer ${token}` : null;
    }

    // --- Generic API Call Function ---
    async function callDevinApi(endpoint, method = 'GET', body = null) {
        const url = `${API_BASE_URL}${endpoint}`;
        const options = {
            method: method.toUpperCase(),
            headers: {
                // 'Content-Type': 'application/json', // Needed for POST/PUT with JSON body
                // Add other headers if needed
            },
            // credentials: 'omit', // Or 'include', 'same-origin' depending on CORS setup
        };

        // Add authentication header if token exists
        const authToken = getAuthToken();
        if (authToken) {
            options.headers['Authorization'] = authToken;
        }

        if (body && (method.toUpperCase() === 'POST' || method.toUpperCase() === 'PUT' || method.toUpperCase() === 'PATCH')) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(body);
        }

        console.log(`Calling API: ${method} ${url}`);
        updateStatus("Sending request...", "loading");

        try {
            const response = await fetch(url, options);

            // Handle non-OK HTTP responses
            if (!response.ok) {
                let errorDetail = `HTTP error ${response.status}: ${response.statusText}`;
                try {
                    const errorJson = await response.json();
                    errorDetail = errorJson.detail || JSON.stringify(errorJson);
                } catch (e) {
                    // Response body wasn't JSON or couldn't be parsed
                }
                console.error("API call failed:", errorDetail);
                throw new Error(errorDetail); // Throw error to be caught below
            }

            // Handle successful responses
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                const data = await response.json();
                console.log("API Response JSON:", data);
                updateStatus("Request successful.", "success");
                return data; // Return parsed JSON data
            } else {
                // Handle non-JSON success responses if expected (e.g., downloading a file)
                console.log("API Response (non-JSON):", response.statusText);
                updateStatus("Request successful (non-JSON response).", "success");
                // return await response.blob(); // Example for file download
                return { success: true, message: "Received non-JSON response." }; // Or return status/text
            }

        } catch (error) {
            console.error("Error during API call:", error);
            updateStatus(`Error: ${error.message}`, "error");
            // Re-throw or return specific error structure if needed downstream
            throw error; // Allow calling function to handle UI update for error
        }
    }

    // --- UI Update Functions ---
    function updateStatus(message, type = "info") { // type: 'info', 'loading', 'success', 'error', 'warning'
        if (statusIndicator) {
            statusIndicator.textContent = message;
            statusIndicator.className = `status-indicator status-${type}`; // Use classes for styling
            console.log(`Status Update (${type}): ${message}`);
        } else {
            console.log(`Status Update (${type}): ${message}`);
        }
    }

    function displayOutput(data) {
        if (outputArea) {
            const outputElement = document.createElement('pre'); // Use <pre> for formatted output
            try {
                // Try to pretty-print if it's likely JSON, otherwise show as text
                if (typeof data === 'object' && data !== null) {
                    outputElement.textContent = JSON.stringify(data, null, 2);
                } else {
                     outputElement.textContent = String(data);
                }
            } catch (e) {
                outputElement.textContent = String(data); // Fallback to string
            }
            // Append new output, or replace content depending on desired UI
            outputArea.appendChild(outputElement);
            outputArea.scrollTop = outputArea.scrollHeight; // Scroll to bottom
        } else {
            console.log("Output data:", data);
        }
    }

    function clearOutput() {
        if (outputArea) {
            outputArea.innerHTML = ''; // Clear previous output
        }
    }

    // --- Event Handlers ---
    async function handleChatSubmit(event) {
        event.preventDefault(); // Prevent default form submission if applicable
        if (!commandInput || !commandInput.value.trim()) return;

        const userMessage = commandInput.value.trim();
        displayOutput(`You: ${userMessage}`); // Display user message immediately
        commandInput.value = ''; // Clear input field

        // --- Prepare request body for a chat endpoint ---
        // This assumes your API has an endpoint like POST /api/ai/chat/{service}
        // And the backend connector uses a message history format
        const requestBody = {
            messages: [
                // TODO: Include actual chat history here if maintaining it
                { "role": "user", "content": userMessage }
            ],
            // Add other parameters like model, temperature if needed/configurable
            // "model": "openai" // Example
        };
        const serviceName = "openai"; // Or get from UI selector

        try {
            const result = await callDevinApi(`/ai/chat/${serviceName}`, 'POST', requestBody);
            if (result && result.response_content) {
                displayOutput(`Devin (${serviceName}): ${result.response_content}`);
            } else {
                 displayOutput(`Devin (${serviceName}): Received no content.`);
            }
        } catch (error) {
            // Error already logged by callDevinApi, specific UI update here if needed
            displayOutput(`Error communicating with ${serviceName}: ${error.message}`);
        }
    }

    async function handleStartTask(event) {
        event.preventDefault();
        // Get task details from UI elements (placeholders)
        const targetValue = taskInputTarget ? taskInputTarget.value.trim() : null;
        const taskType = taskTypeSelector ? taskTypeSelector.value : null; // e.g., 'nmap_quick_scan'

        if (!targetValue || !taskType) {
            updateStatus("Please provide both target and task type.", "warning");
            return;
        }

        clearOutput(); // Clear previous outputs when starting a new task
        updateStatus(`Starting task '${taskType}' on target '${targetValue}'...`, "loading");

        // --- Prepare request body based on task type ---
        // Example for a scan task routed through /api/pentest/scan/start
        let endpoint;
        let requestBody;

        if (taskType === 'nmap_quick_scan') {
            endpoint = '/pentest/scan/start';
            requestBody = {
                target: { type: 'ip', value: targetValue }, // TODO: Detect target type (ip/domain/url)
                parameters: { profile: 'quick', tool: 'nmap' }
            };
        } else if (taskType === 'web_analysis') {
             endpoint = '/pentest/analyze'; // Example analysis endpoint
             requestBody = {
                 tool_name: 'generic_web_analyzer', // Or get from UI
                 tool_output: `Analyze target: ${targetValue}`, // Simple input example
                 context: { "target_url": targetValue }
             };
        } else {
            updateStatus(`Unknown task type: ${taskType}`, "error");
            return;
        }

        try {
            const result = await callDevinApi(endpoint, 'POST', requestBody);
            if (result && result.task_id) { // Check for task ID if endpoint returns one
                 updateStatus(`Task successfully queued/started. Task ID: ${result.task_id}`, "success");
                 displayOutput(result); // Show task info
                 // TODO: Implement polling or WebSocket for task status updates
            } else if (result) {
                updateStatus(`Task completed or response received.`, "success");
                displayOutput(result); // Show direct result if no task ID
            } else {
                // Should have been caught by callDevinApi, but as fallback
                 throw new Error("Received empty response from API.");
            }
        } catch (error) {
            // Error already logged by callDevinApi
             updateStatus(`Failed to start task '${taskType}': ${error.message}`, "error");
        }
    }


    // --- Attach Event Listeners ---
    if (submitButton && commandInput) {
        // Handle chat/command input submission (e.g., pressing Enter or clicking button)
        if (commandInput.form) {
             commandInput.form.addEventListener('submit', handleChatSubmit);
        } else {
             submitButton.addEventListener('click', handleChatSubmit);
             commandInput.addEventListener('keypress', function(e) {
                  if (e.key === 'Enter' && !e.shiftKey) { // Submit on Enter, allow Shift+Enter for newline
                      e.preventDefault(); // Prevent default newline insertion
                      handleChatSubmit(e);
                  }
             });
        }
        console.log("Attached chat/command input handler.");
    }

    if (startTaskButton && taskInputTarget && taskTypeSelector) {
        // Handle dedicated task submission button
         startTaskButton.addEventListener('click', handleStartTask);
         console.log("Attached task start handler.");
    }

    // Add more event listeners and UI logic as needed...
    updateStatus("Devin frontend ready.");

}); // End DOMContentLoaded
