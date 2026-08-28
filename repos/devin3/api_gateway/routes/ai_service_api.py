# Devin/api_gateway/routes/ai_service_api.py # Purpose: API endpoints for interacting directly with core AI/LLM services.

import time
import logging
from fastapi import APIRouter, HTTPException, Body, Path, Depends, Request # Added Request for potential rate limiting key
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union, Literal

# --- Conceptual Imports / Dependencies ---
# Import the connectors and the rate limiter defined previously
# Adjust paths as needed based on final project structure
try:
    from ...ai_integrations.chatgpt_connector import ChatGPTConnector
    from ...ai_integrations.gemini_connector import GeminiConnector
    from ...ai_integrations.perplexity_ai_connector import PerplexityConnector
    from ...ai_integrations.copilot_ai_connector import CopilotConnector # Assumed for code
    from ...ai_integrations.pentestgpt_ai_connector import PentestGPTConnector # Hypothetical
    from ...ai_integrations.all_other_ais_connector import LocalLLMConnector # Generic for local/uncensored
    from ...ai_integrations.api_rate_limiter import APIRateLimiter
except ImportError:
    print("WARNING: Could not import one or more AI connectors or RateLimiter. Using placeholders.")
    # Define placeholders if imports fail
    class PlaceholderConnector:
        def __init__(self, *args, **kwargs): print(f"Initialized PlaceholderConnector for missing import.")
        def get_chat_completion(self, *args, **kwargs): print("Placeholder get_chat_completion called"); return "Placeholder response"
        def get_code_completion(self, *args, **kwargs): print("Placeholder get_code_completion called"); return "Placeholder code"
        def analyze_scan_results(self, *args, **kwargs): print("Placeholder analyze_scan_results called"); return {"summary":"Placeholder analysis"}
        def suggest_exploits(self, *args, **kwargs): print("Placeholder suggest_exploits called"); return [{"name":"placeholder_exploit"}]
    ChatGPTConnector = PlaceholderConnector
    GeminiConnector = PlaceholderConnector
    PerplexityConnector = PlaceholderConnector
    CopilotConnector = PlaceholderConnector
    PentestGPTConnector = PlaceholderConnector
    LocalLLMConnector = PlaceholderConnector

    class APIRateLimiter:
        def acquire(self, service_key: str, tokens_required: float = 1.0, blocking: bool = True, timeout: Optional[float] = None) -> bool:
             print(f"Placeholder Rate Limiter: Allowing request for '{service_key}'.")
             return True # Always allow in placeholder
        def __init__(self, *args, **kwargs): print("Initialized Placeholder Rate Limiter.")


# --- Placeholder for Dependency Injection ---
# In a real FastAPI app, you'd set these up properly, perhaps using a central registry
# or FastAPI's dependency management features more robustly.

# Assume instances are created and managed elsewhere (e.g., in bootstrap.py or main gateway app)
# For this skeleton, we'll just instantiate placeholders directly if imports failed.
# Real app should inject configured instances.
print("API Route Init: Setting up conceptual service instances...")
rate_limiter = APIRateLimiter()
# Configure some default limits (these should ideally come from config)
rate_limiter.configure_limit("openai_chat_rpm", 20, 60) # Example: 20 requests/min
rate_limiter.configure_limit("gemini_chat_rpm", 15, 60) # Example: 15 requests/min
rate_limiter.configure_limit("perplexity_chat_rpm", 30, 60) # Example: 30 requests/min
rate_limiter.configure_limit("openai_code_rpm", 20, 60)
rate_limiter.configure_limit("pentestgpt_rpm", 10, 60)
rate_limiter.configure_limit("local_llm_rpm", 60, 60) # Higher limit for local


chatgpt_connector = ChatGPTConnector()
gemini_connector = GeminiConnector()
perplexity_connector = PerplexityConnector()
copilot_connector = CopilotConnector() # Assumed instance for code tasks
pentestgpt_connector = PentestGPTConnector() # Hypothetical
local_llm_connector = LocalLLMConnector() # Generic local

# Map service names used in API path to connector instances and rate limit keys
SERVICE_MAP = {
    "openai": (chatgpt_connector, "openai_chat_rpm"),
    "gemini": (gemini_connector, "gemini_chat_rpm"),
    "perplexity": (perplexity_connector, "perplexity_chat_rpm"),
    "openai_code": (copilot_connector, "openai_code_rpm"), # Using copilot connector instance
    "pentestgpt": (pentestgpt_connector, "pentestgpt_rpm"), # Hypothetical
    "local": (local_llm_connector, "local_llm_rpm"), # Generic local
    # Add other configured connectors here...
}

# --- Pydantic Models for API ---

# General Chat
class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_items=1)
    model: Optional[str] = None # Allow overriding default model of the connector
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(1024, gt=0)
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0)
    # Add other common parameters supported by multiple backends if needed
    stream: Optional[bool] = False # Note: Streaming responses require different endpoint handling (not implemented here)

class ChatResponse(BaseModel):
    service: str
    model_used: Optional[str] # Which specific model was actually called
    response_content: str
    finish_reason: Optional[str] = None # e.g., "stop", "length", "safety"

# Code Completion
class CodeCompletionRequest(BaseModel):
    code_context: str
    language: Optional[str] = None
    model: Optional[str] = None # Override default code model
    temperature: Optional[float] = Field(0.2, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(150, gt=0)
    stop_sequences: Optional[List[str]] = None

class CodeCompletionResponse(BaseModel):
    service: str
    model_used: Optional[str]
    completion: str

# Pentesting AI (Hypothetical structure)
class PentestAIRequest(BaseModel):
    task_type: Literal["analyze_scan", "suggest_exploits", "generate_plan", "ask_question"]
    parameters: Dict[str, Any] # Structure depends on task_type
    # e.g., {'tool_name': 'nmap', 'scan_output': '...', 'context': {...}} for analyze_scan
    # e.g., {'vulnerability_info': {...}, 'target_info': {...}} for suggest_exploits
    model: Optional[str] = None # Override default pentest model

class PentestAIResponse(BaseModel):
    service: str
    model_used: Optional[str]
    task_type: str
    result: Any # Structure depends heavily on the task_type (e.g., dict for analysis, list for suggestions, dict for plan, str for answer)


# --- API Router ---

router = APIRouter(
    prefix="/ai",
    tags=["AI Services Direct Access"],
    # Add authentication dependency here if needed
    # dependencies=[Depends(get_current_active_user)],
    responses={
        404: {"description": "Service name not found"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "AI Service unavailable or failed"},
    },
)

# --- Helper Function to get Connector/Rate Key ---
def get_service_connector(service_name: str) -> Tuple[Any, str]:
    """Looks up connector instance and rate limit key."""
    service_info = SERVICE_MAP.get(service_name.lower())
    if not service_info:
        raise HTTPException(status_code=404, detail=f"AI service '{service_name}' not found or configured.")
    return service_info # Returns (connector_instance, rate_limit_key)

# --- Endpoints ---

# --- API Endpoints ---

@router.post("/chat/{service_name}", response_model=ChatResponse, summary="Send Chat Request to Specified AI")
async def chat_endpoint(
    service_name: str = Path(..., description="Name of the AI service (e.g., 'openai', 'gemini', 'perplexity', 'local')"),
    request: ChatRequest = Body(...),
    # --- Conceptual Dependency Injection ---
    # In a real app, inject configured instances:
    # limiter: APIRateLimiter = Depends(get_rate_limiter_instance),
    # service_info: Tuple[Any, str] = Depends(get_service_connector) # Gets (connector, rate_key)
):
    """
    Routes a chat request to the specified backend AI service.

    Handles rate limiting before forwarding the request.
    """
    print(f"API Route /chat/{service_name}: Received request.")
    try:
        # --- Conceptual Dependency Resolution ---
        # Replace direct calls with proper dependency injection in real app
        connector, rate_limit_key = get_service_connector(service_name) # Raises 404 if service unknown
        limiter = rate_limiter # Use globally defined instance for skeleton
        # --- End Conceptual Dependency Resolution ---

        # --- Rate Limiting ---
        print(f"  - Checking rate limit for key: '{rate_limit_key}'")
        # Use client IP or authenticated user ID for per-user limiting if needed
        # Example key: f"{rate_limit_key}_{request.client.host}"
        # Using service-wide key for simplicity here:
        if not limiter.acquire(service_key=rate_limit_key, blocking=True, timeout=10.0): # Wait up to 10s
             print(f"  - Rate limit exceeded for '{rate_limit_key}'.")
             raise HTTPException(status_code=429, detail=f"Rate limit exceeded for service '{service_name}'. Please try again later.")
        print(f"  - Rate limit check passed for '{rate_limit_key}'.")
        # --- End Rate Limiting ---

        # --- Call Backend Connector ---
        print(f"  - Forwarding request to {type(connector).__name__}...")
        response_content = connector.get_chat_completion(
            messages=request.messages,
            model=request.model, # Allow user to override connector's default
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            # Pass other relevant params from request if connector supports them
        )
        # --- End Backend Connector Call ---

        if response_content is None:
            # Connector method returned None, indicating an internal error or safety block
            print(f"  - Error: Connector for '{service_name}' failed to return content.")
            raise HTTPException(status_code=503, detail=f"AI service '{service_name}' failed to generate a response.")

        # TODO: Extract actual model name used and finish reason from connector response if available
        model_used = request.model or getattr(connector, 'default_model', 'unknown') # Best guess
        finish_reason = "stop" # Placeholder

        return ChatResponse(
            service=service_name,
            model_used=model_used,
            response_content=response_content,
            finish_reason=finish_reason
        )

    except HTTPException as http_exc:
        # Re-raise HTTPExceptions (like 404 from get_service_connector or 429 from rate limiter)
        raise http_exc
    except Exception as e:
        logging.exception(f"API Route /chat/{service_name}: Unexpected error.") # Log full traceback
        raise HTTPException(status_code=500, detail=f"Internal server error processing chat request: {e}")


@router.post("/code/{service_name}", response_model=CodeCompletionResponse, summary="Request Code Completion")
async def code_endpoint(
    service_name: str = Path(..., description="Name of the AI code service (e.g., 'openai_code')"),
    request: CodeCompletionRequest = Body(...),
    # limiter: APIRateLimiter = Depends(get_rate_limiter_instance), # Conceptual DI
    # service_info: Tuple[Any, str] = Depends(get_service_connector) # Conceptual DI
):
    """
    Routes a code completion request to the specified backend AI service.
    """
    print(f"API Route /code/{service_name}: Received request.")
    try:
        # --- Conceptual Dependency Resolution ---
        connector, rate_limit_key = get_service_connector(service_name) # Raises 404
        limiter = rate_limiter # Use global for skeleton
        # --- End Conceptual Dependency Resolution ---

        # Ensure the connector has the expected method
        if not hasattr(connector, 'get_code_completion'):
             raise HTTPException(status_code=501, detail=f"Service '{service_name}' does not support code completion via this API.")

        # --- Rate Limiting ---
        print(f"  - Checking rate limit for key: '{rate_limit_key}'")
        if not limiter.acquire(service_key=rate_limit_key, blocking=True, timeout=5.0): # Shorter timeout maybe?
             print(f"  - Rate limit exceeded for '{rate_limit_key}'.")
             raise HTTPException(status_code=429, detail=f"Rate limit exceeded for service '{service_name}'.")
        print(f"  - Rate limit check passed for '{rate_limit_key}'.")
        # --- End Rate Limiting ---

        # --- Call Backend Connector ---
        print(f"  - Forwarding request to {type(connector).__name__}...")
        completion = connector.get_code_completion(
            code_context=request.code_context,
            language=request.language,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stop_sequences=request.stop_sequences,
        )
        # --- End Backend Connector Call ---

        if completion is None:
            print(f"  - Error: Connector for '{service_name}' failed to return code completion.")
            raise HTTPException(status_code=503, detail=f"AI service '{service_name}' failed to generate code completion.")

        model_used = request.model or getattr(connector, 'default_model', 'unknown')

        return CodeCompletionResponse(
            service=service_name,
            model_used=model_used,
            completion=completion
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logging.exception(f"API Route /code/{service_name}: Unexpected error.")
        raise HTTPException(status_code=500, detail=f"Internal server error processing code request: {e}")


@router.post("/pentest/{service_name}", response_model=PentestAIResponse, summary="Send Request to Pentesting AI")
async def pentest_ai_endpoint(
    service_name: str = Path(..., description="Name of the Pentesting AI service (e.g., 'pentestgpt')"),
    request: PentestAIRequest = Body(...),
    # limiter: APIRateLimiter = Depends(get_rate_limiter_instance), # Conceptual DI
    # service_info: Tuple[Any, str] = Depends(get_service_connector) # Conceptual DI
):
    """
    Routes a specialized request to the specified backend Pentesting AI service.
    The specific action is determined by the 'task_type' field in the request body.
    """
    print(f"API Route /pentest/{service_name}: Received request for task '{request.task_type}'.")
    try:
        # --- Conceptual Dependency Resolution ---
        connector, rate_limit_key = get_service_connector(service_name) # Raises 404
        limiter = rate_limiter # Use global for skeleton
        # --- End Conceptual Dependency Resolution ---

        # --- Rate Limiting ---
        print(f"  - Checking rate limit for key: '{rate_limit_key}'")
        if not limiter.acquire(service_key=rate_limit_key, blocking=True, timeout=15.0): # Longer timeout maybe
             print(f"  - Rate limit exceeded for '{rate_limit_key}'.")
             raise HTTPException(status_code=429, detail=f"Rate limit exceeded for service '{service_name}'.")
        print(f"  - Rate limit check passed for '{rate_limit_key}'.")
        # --- End Rate Limiting ---

        # --- Call Backend Connector based on task_type ---
        print(f"  - Forwarding request to {type(connector).__name__} for task '{request.task_type}'...")
        result_data = None
        if request.task_type == "analyze_scan":
             if not hasattr(connector, 'analyze_scan_results'): raise HTTPException(status_code=501, detail="Analyze scan not supported.")
             result_data = connector.analyze_scan_results(
                 tool_name=request.parameters.get('tool_name'),
                 scan_output=request.parameters.get('scan_output'),
                 context=request.parameters.get('context')
             )
        elif request.task_type == "suggest_exploits":
             if not hasattr(connector, 'suggest_exploits'): raise HTTPException(status_code=501, detail="Suggest exploits not supported.")
             result_data = connector.suggest_exploits(
                 vulnerability_info=request.parameters.get('vulnerability_info'),
                 target_info=request.parameters.get('target_info')
             )
        elif request.task_type == "generate_plan":
             if not hasattr(connector, 'generate_pentest_plan'): raise HTTPException(status_code=501, detail="Generate plan not supported.")
             result_data = connector.generate_pentest_plan(
                 scope=request.parameters.get('scope', []),
                 objectives=request.parameters.get('objectives', []),
                 constraints=request.parameters.get('constraints')
             )
        elif request.task_type == "ask_question":
             if not hasattr(connector, 'ask_pentest_question'): raise HTTPException(status_code=501, detail="Ask question not supported.")
             result_data = connector.ask_pentest_question(
                 question=request.parameters.get('question'),
                 context=request.parameters.get('context')
             )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported task_type for pentesting AI: '{request.task_type}'")
        # --- End Backend Connector Call ---

        if result_data is None:
            print(f"  - Error: Connector for '{service_name}' failed to return result for task '{request.task_type}'.")
            raise HTTPException(status_code=503, detail=f"AI service '{service_name}' failed processing task '{request.task_type}'.")

        model_used = request.model or getattr(connector, 'default_model', 'unknown')

        return PentestAIResponse(
            service=service_name,
            model_used=model_used,
            task_type=request.task_type,
            result=result_data
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logging.exception(f"API Route /pentest/{service_name}: Unexpected error.")
        raise HTTPException(status_code=500, detail=f"Internal server error processing pentest AI request: {e}")


# --- Note on Running ---
# This file defines an APIRouter. To run these endpoints, this router
# needs to be included in a main FastAPI application instance.
# Example in your main API gateway file (e.g., api_gateway/main.py):
#
# from fastapi import FastAPI
# from .routes import pentest_api, robotics_api, ai_service_api # Import routers
#
# app = FastAPI(title="Devin API Gateway")
#
# app.include_router(ai_service_api.router)
# app.include_router(pentest_api.router)
# app.include_router(robotics_api.router)
# # Include other routers...
#
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
