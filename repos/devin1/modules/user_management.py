"""
modules/user_management.py

Comprehensive user management module for handling user authentication, authorization,
profile management, and activity tracking.
"""

import hashlib
import os
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional, List

# Constants
JWT_SECRET = os.getenv('JWT_SECRET', 'default_secret_key')
JWT_ALGORITHM = 'HS256'
TOKEN_EXPIRY_HOURS = 24

# In-memory user database (for demo purposes; replace with a database in production)
user_database: Dict[str, Dict] = {}

# Exception classes
class UserManagementError(Exception):
    pass

class UserAlreadyExistsError(UserManagementError):
    pass

class UserNotFoundError(UserManagementError):
    pass

class AuthenticationError(UserManagementError):
    pass

# Utility Functions
def hash_password(password: str) -> str:
    """Hashes a password with a salt."""
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ':' + hashed.hex()

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verifies a provided password against a stored hash."""
    try:
        salt, hashed = stored_password.split(':')
        provided_hashed = hashlib.pbkdf2_hmac(
            'sha256', provided_password.encode('utf-8'), bytes.fromhex(salt), 100000
        )
        return provided_hashed.hex() == hashed
    except ValueError:
        return False

# Core Functions
def register_user(username: str, password: str, email: str) -> Dict:
    """Registers a new user."""
    if username in user_database:
        raise UserAlreadyExistsError(f"User '{username}' already exists.")
    user_database[username] = {
        'password': hash_password(password),
        'email': email,
        'created_at': datetime.now(),
        'last_login': None,
        'roles': ['user'],  # Default role
    }
    return {'message': f"User '{username}' successfully registered."}

def authenticate_user(username: str, password: str) -> str:
    """Authenticates a user and returns a JWT token."""
    user = user_database.get(username)
    if not user or not verify_password(user['password'], password):
        raise AuthenticationError("Invalid username or password.")
    
    user['last_login'] = datetime.now()
    token = jwt.encode(
        {
            'username': username,
            'roles': user['roles'],
            'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    return token

def get_user_profile(username: str) -> Optional[Dict]:
    """Fetches user profile details."""
    return user_database.get(username)

def assign_role(username: str, role: str) -> Dict:
    """Assigns a new role to a user."""
    user = user_database.get(username)
    if not user:
        raise UserNotFoundError(f"User '{username}' not found.")
    if role not in user['roles']:
        user['roles'].append(role)
    return {'message': f"Role '{role}' assigned to user '{username}'."}

def delete_user(username: str) -> Dict:
    """Deletes a user."""
    if username not in user_database:
        raise UserNotFoundError(f"User '{username}' not found.")
    del user_database[username]
    return {'message': f"User '{username}' successfully deleted."}

# Example usage for testing (to be removed in production)
if __name__ == "__main__":
    # Register a user
    try:
        print(register_user("john_doe", "securepassword", "john@example.com"))
    except UserAlreadyExistsError as e:
        print(e)

    # Authenticate the user
    try:
        token = authenticate_user("john_doe", "securepassword")
        print("JWT Token:", token)
    except AuthenticationError as e:
        print(e)

    # Fetch profile
    print(get_user_profile("john_doe"))

    # Assign a role
    print(assign_role("john_doe", "admin"))

    # Delete the user
    print(delete_user("john_doe"))
