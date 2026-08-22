# Devin/api_gateway/middleware/auth_validator.py # Purpose: Middleware for validating authentication tokens (e.g., OAuth/JWT).

import os
import time
import logging
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from starlette.types import ASGIApp
from typing import Dict, Any, List, Optional, Tuple, Sequence, Union

# --- Conceptual JWT Handling ---
# Requires `pip install python-jose[cryptography]`
try:
    from jose import jwt, exceptions as jose_exceptions
    JWT_ENABLED = True
except ImportError:
    print("WARNING: 'python-jose' library not found. JWT validation will be disabled in middleware.")
    jwt = None
    jose_exceptions = None
    JWT_ENABLED = False

# --- Configuration Placeholders (Load securely in real app!) ---
# Example: Load from environment variables or a config service
JWT_SECRET_KEY = os.environ.get("API_JWT_SECRET_KEY", "a_very_insecure_default_secret_key_replace_me") # CHANGE THIS! Use a strong, random secret.
JWT_ALGORITHM = os.environ.get("API_JWT_ALGORITHM", "HS256") # e.g., HS256 or RS256 (needs public/private keys)
API_AUDIENCE = os.environ.get("API_JWT_AUDIENCE", "devin_api_users") # Expected 'aud' claim
API_ISSUER = os.environ.get("API_JWT_ISSUER", "devin_auth_service") # Expected 'iss' claim

# Example: Simple API Key store (Replace with database or secure lookup)
VALID_API_KEYS: Dict[str, Dict] = {
    os.environ.get("DEVIN_API_KEY_1", "dummy-api-key-admin-001"): {"user_id": "admin_user", "scopes": ["full_access"]},
    os.environ.get("DEVIN_API_KEY_2", "dummy-api-key-user-002"): {"user_id": "normal_user_abc", "scopes": ["read_status", "start_scan"]},
}
# --- End Configuration Placeholders ---

# --- Pydantic model for authenticated user info ---
# This can be attached to request.state
class AuthenticatedUser(BaseModel):
    id: str # User ID (e.g., from JWT 'sub' or API key mapping)
    scopes: List[str] = [] # Permissions/roles associated with the user/token
    # Add other relevant fields like username, email, tenant_id if needed
    auth_method: Literal['jwt', 'api_key', 'unknown'] = 'unknown'


class AuthValidationMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware to validate authentication credentials (JWT or API Key).

    - Extracts credentials from request headers.
    - Validates JWTs (signature, expiration, claims) or API Keys.
    - Attaches authenticated user information to `request.state.user`.
    - Rejects requests with missing or invalid credentials (401/403).
    - Allows bypassing auth for specified public paths.
    """
    def __init__(self, app: ASGIApp, public_paths: Optional[Sequence[str]] = None):
        """
        Args:
            app (ASGIApp): The FastAPI application instance.
            public_paths (Optional[Sequence[str]]): A list/set of URL paths
                                                     (e.g., "/docs", "/openapi.json", "/health")
                                                     that should bypass authentication.
        """
        super().__init__(app)
        self.public_paths = set(public_paths) if public_paths else set(['/docs', '/openapi.json', '/health'])
        print("AuthValidationMiddleware initialized.")
        print(f"  - Public paths (no auth required): {self.public_paths}")
        if not JWT_SECRET_KEY.startswith("dummy") and JWT_ENABLED:
             print("  - JWT Validation Enabled.")
        elif not JWT_ENABLED:
             print("  - JWT Validation Disabled ('python-jose' not installed).")
        else:
             print("  - WARNING: Using default/insecure JWT secret key!")
        if VALID_API_KEYS:
             print(f"  - API Key Validation Enabled ({len(VALID_API_KEYS)} keys configured conceptually).")


    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Processes request, performs auth check, and proceeds or rejects."""

        # --- 1. Bypass for Public Paths ---
        if request.url.path in self.public_paths:
            # print(f"DEBUG: Bypassing auth for public path: {request.url.path}") # Verbose
            response = await call_next(request)
            return response

        # --- 2. Extract Credentials ---
        auth_header = request.headers.get("Authorization")
        api_key_header_name = "X-API-Key" # Example header name for API keys
        api_key = request.headers.get(api_key_header_name)

        authenticated_user: Optional[AuthenticatedUser] = None
        error_detail = "Not authenticated"
        status_code = HTTP_401_UNAUTHORIZED

        # --- 3. Validate JWT (if present) ---
        if auth_header and auth_header.lower().startswith("bearer ") and JWT_ENABLED:
            token = auth_header.split(" ", 1)[1]
            print(f"DEBUG: Attempting JWT validation for token: {token[:10]}...") # Avoid logging full token
            validated_claims = self._validate_jwt(token)
            if validated_claims:
                user_id = validated_claims.get("sub") # Subject claim usually holds user ID
                scopes = validated_claims.get("scope", "").split() # Example scope claim
                if user_id:
                    authenticated_user = AuthenticatedUser(id=user_id, scopes=scopes, auth_method='jwt')
                    print(f"  - JWT VALID for user '{user_id}' with scopes {scopes}.")
                else:
                    error_detail = "Invalid JWT: Missing 'sub' claim."
                    status_code = HTTP_401_UNAUTHORIZED # Or 403 if technically valid but unusable
            else:
                # _validate_jwt handles logging specific JWT errors
                error_detail = "Invalid or expired JWT token."
                status_code = HTTP_401_UNAUTHORIZED

        # --- 4. Validate API Key (if no valid JWT found and API key present) ---
        elif api_key:
            print(f"DEBUG: Attempting API Key validation for key: ...{api_key[-4:]}") # Avoid logging full key
            key_info = self._validate_api_key(api_key)
            if key_info:
                 user_id = key_info.get("user_id", "api_key_user")
                 scopes = key_info.get("scopes", [])
                 authenticated_user = AuthenticatedUser(id=user_id, scopes=scopes, auth_method='api_key')
                 print(f"  - API Key VALID for user '{user_id}' with scopes {scopes}.")
            else:
                 error_detail = "Invalid API Key."
                 status_code = HTTP_401_UNAUTHORIZED

        # --- 5. Process Result ---
        if authenticated_user:
            # Attach user info to request state for access in endpoint functions
            request.state.user = authenticated_user
            # Proceed to the next middleware or endpoint
            response = await call_next(request)
            return response
        else:
            # Authentication failed or no credentials provided for protected route
            print(f"Authentication failed for {request.url.path}: {error_detail}")
            return JSONResponse(
                status_code=status_code,
                content={"detail": error_detail},
                headers={"WWW-Authenticate": "Bearer"} if not api_key else None # Hint for JWT if Bearer was expected
            )


    def _validate_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """Validates the JWT token and returns claims if valid."""
        if not jwt or not jose_exceptions: return None # Library not available
        try:
            # Decode the token, verifying signature, expiration, audience, issuer
            claims = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
                audience=API_AUDIENCE,
                issuer=API_ISSUER
            )
            # Add check for 'exp' claim validity implicitly handled by decode
            # Add check for 'nbf' claim if used
            # Add check for required scopes if implementing scope checks here (usually done in endpoint)
            return claims
        except jose_exceptions.ExpiredSignatureError:
            print("  - JWT Error: Token has expired.")
            return None
        except jose_exceptions.JWTClaimsError as e:
             print(f"  - JWT Error: Invalid claims (e.g., audience/issuer mismatch): {e}")
             return None
        except jose_exceptions.JWTError as e: # Catches other JWT errors (e.g., invalid signature)
            print(f"  - JWT Error: Token validation failed: {e}")
            return None
        except Exception as e: # Catch unexpected errors during validation
             print(f"  - Unexpected error during JWT validation: {e}")
             return None

    def _validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validates a simple API key against a predefined store."""
        # --- Replace with secure lookup (e.g., database query) ---
        # Avoid timing attacks if comparing hashes directly in production
        key_info = VALID_API_KEYS.get(api_key)
        # --- End Replace ---
        if key_info:
            return key_info # Return associated info (user_id, scopes)
        else:
            return None


# --- Usage Note ---
# To use this middleware:
# In your main FastAPI application file (e.g., api_gateway/main.py):
#
# from fastapi import FastAPI
# from .middleware.auth_validator import AuthValidationMiddleware # Adjust import
# # Import your routers...
#
# app = FastAPI(title="Devin API Gateway")
#
# # Define paths that DO NOT require authentication
# public_paths = {"/docs", "/openapi.json", "/health"}
#
# # Add the middleware *before* including routers that need protection
# app.add_middleware(AuthValidationMiddleware, public_paths=public_paths)
#
# # Include your API routers
# # app.include_router(ai_service_api.router) # Now protected
# # app.include_router(pentest_api.router) # Now protected
# # ... etc ...
#
# # Optional: Add dependency for endpoints to get user info
# # async def get_current_user(request: Request) -> AuthenticatedUser:
# #     if not hasattr(request.state, "user") or not request.state.user:
# #         raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Not authenticated")
# #     # Add scope checks here if needed based on request.state.user.scopes
# #     return request.state.user
# # Then use `current_user: AuthenticatedUser = Depends(get_current_user)` in endpoint signatures.
#
# if __name__ == "__main__":
#    import uvicorn
#    print("Conceptual: Run the main FastAPI app that includes this middleware.")
#    # uvicorn.run(app, host="0.0.0.0", port=8000)

print("Conceptual skeleton for AuthValidationMiddleware defined.")
