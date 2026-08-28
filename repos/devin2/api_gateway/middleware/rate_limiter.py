# Devin/api_gateway/middleware/rate_limiter.py # Purpose: Middleware to apply rate limiting to API requests.

import time
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
from starlette.types import ASGIApp
from typing import Optional

# --- Conceptual Import ---
# Import the APIRateLimiter class defined previously
# Adjust path based on actual project structure
try:
    from ...ai_integrations.api_rate_limiter import APIRateLimiter
except ImportError:
    print("WARNING: Could not import APIRateLimiter from ai_integrations. Using placeholder.")
    # Define placeholder if import fails
    class APIRateLimiter:
        def acquire(self, service_key: str, tokens_required: float = 1.0, blocking: bool = True, timeout: Optional[float] = None) -> bool:
             print(f"Placeholder Rate Limiter: Allowing request for '{service_key}'.")
             return True # Always allow in placeholder
        def configure_limit(self, *args, **kwargs): pass # Add configure method to placeholder
        def __init__(self, *args, **kwargs): print("Initialized Placeholder Rate Limiter.")

# --- Middleware Implementation ---

# Option 1: Using BaseHTTPMiddleware Class (more structured)
class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware using BaseHTTPMiddleware to enforce rate limits per client IP.

    Uses the shared APIRateLimiter instance.
    """
    def __init__(self, app: ASGIApp, limiter: APIRateLimiter, limit_key_prefix: str = "api_ip_rpm", default_rate: float = 60, default_period: float = 60):
        """
        Args:
            app (ASGIApp): The FastAPI application instance.
            limiter (APIRateLimiter): The shared APIRateLimiter instance.
            limit_key_prefix (str): Prefix for the service key used in the limiter (e.g., 'api_ip_rpm', 'api_user_rpm').
            default_rate (float): Default max requests if limit not specifically configured.
            default_period (float): Default period in seconds for the rate.
        """
        super().__init__(app)
        self.limiter = limiter
        self.limit_key_prefix = limit_key_prefix
        # Ensure a default limit is configured for generic IP limiting
        # In a real app, configure this more robustly during startup
        print(f"Middleware attempting to configure default limit: {self.limit_key_prefix}")
        try:
            # Check if already configured, only configure if not present maybe? Or always update? Let's update.
             self.limiter.configure_limit(self.limit_key_prefix, default_rate, default_period)
             print(f"  - Default limit for '{self.limit_key_prefix}' set/updated: {default_rate}/{default_period}s")
        except Exception as e:
             print(f"  - Warning: Failed to configure default limit '{self.limit_key_prefix}' in middleware init: {e}")


    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Processes the incoming request, checks rate limit, and proceeds or rejects.
        """
        # --- Identify Client ---
        # Use client IP address as the identifier for rate limiting
        # Note: request.client.host might be None if server runs behind misconfigured proxy.
        # Consider using X-Forwarded-For header carefully if behind a trusted proxy.
        client_ip = request.client.host if request.client else "unknown_client"

        # Construct the service key for the rate limiter instance
        service_key = f"{self.limit_key_prefix}_{client_ip}"

        # --- Check Rate Limit ---
        # Use blocking=False for middleware - respond immediately if limit exceeded.
        acquired = self.limiter.acquire(service_key=service_key, tokens_required=1.0, blocking=False)

        if not acquired:
            # Limit exceeded
            print(f"Rate Limit Exceeded for key: '{service_key}' (Client: {client_ip})")
            # Return HTTP 429 Too Many Requests
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."}
            )
        else:
            # Limit not exceeded, proceed with the request
            # print(f"Rate Limit OK for key: '{service_key}' (Client: {client_ip})") # Can be verbose
            response = await call_next(request)
            return response


# Option 2: Using @app.middleware("http") decorator (functional style)
# This requires the 'app' instance and 'rate_limiter' instance to be available in the scope
# where the middleware function is defined (e.g., in your main FastAPI app file).

# Example (place this in your main app file, not here):
#
# from fastapi import FastAPI, Request
# from starlette.responses import JSONResponse
# from ai_integrations.api_rate_limiter import APIRateLimiter # Adjust import
#
# app = FastAPI()
# rate_limiter_instance = APIRateLimiter()
# # Configure default limit during startup
# rate_limiter_instance.configure_limit("api_ip_rpm_functional", 60, 60)
#
# @app.middleware("http")
# async def rate_limit_middleware_functional(request: Request, call_next):
#     """Functional middleware for rate limiting per client IP."""
#     limiter = rate_limiter_instance # Access shared instance
#     limit_key_prefix = "api_ip_rpm_functional" # Define key prefix
#
#     client_ip = request.client.host if request.client else "unknown_client"
#     service_key = f"{limit_key_prefix}_{client_ip}"
#
#     acquired = limiter.acquire(service_key=service_key, tokens_required=1.0, blocking=False)
#
#     if not acquired:
#         print(f"Functional Rate Limit Exceeded for key: '{service_key}' (Client: {client_ip})")
#         return JSONResponse(
#             status_code=429,
#             content={"detail": "Rate limit exceeded. Please try again later."}
#         )
#     else:
#         response = await call_next(request)
#         return response
#
# # Add routers AFTER defining middleware
# # app.include_router(...)


# --- Usage Note ---
# To use the RateLimitingMiddleware class (Option 1):
# In your main FastAPI application file (e.g., api_gateway/main.py or similar):
#
# from fastapi import FastAPI
# from .middleware.rate_limiter import RateLimitingMiddleware # Adjust import
# from ...ai_integrations.api_rate_limiter import APIRateLimiter # Adjust import
# # Import your routers...
#
# # Create the shared rate limiter instance
# global_rate_limiter = APIRateLimiter()
# # Configure necessary limits (can be done here or more robustly via config loading)
# global_rate_limiter.configure_limit("api_ip_rpm", 60, 60) # e.g., 60 requests per minute per IP
# global_rate_limiter.configure_limit("openai_chat_rpm", 20, 60) # Limits used by specific routes
# # ... configure other limits ...
#
# app = FastAPI(title="Devin API Gateway")
#
# # Add the middleware, passing the limiter instance
# app.add_middleware(
#     RateLimitingMiddleware,
#     limiter=global_rate_limiter,
#     limit_key_prefix="api_ip_rpm", # Key prefix for this middleware's limit
#     default_rate=60, # Default rate for the IP limit
#     default_period=60
# )
#
# # Include your API routers AFTER adding middleware
# # app.include_router(ai_service_api.router)
# # app.include_router(pentest_api.router)
# # ... etc ...
#
# if __name__ == "__main__":
#    import uvicorn
#    # Note: Running this file directly does nothing without a FastAPI app instance.
#    # This example runs the main gateway app conceptually.
#    print("Conceptual: Run the main FastAPI app that includes this middleware.")
#    # uvicorn.run(app, host="0.0.0.0", port=8000)

print("Conceptual skeleton for RateLimitingMiddleware defined.")
# No runnable example here as middleware needs to be attached to an app.
