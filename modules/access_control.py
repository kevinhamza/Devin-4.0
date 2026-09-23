"""
modules/access_control.py — Role-based access control system

Manages tool permissions, user roles, and audit logging.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from enum import Enum

# Configuration
CONFIG_PATH = Path(__file__).parent.parent / "config" / "access_control.json"


class Permission(Enum):
    """Tool permission levels"""
    DENY = 0
    READ_ONLY = 1
    EXECUTE = 2
    ADMIN = 3


class Role(Enum):
    """User roles"""
    GUEST = "guest"           # Read-only access
    USER = "user"             # Execute tools
    POWER_USER = "power_user" # Execute + configure
    ADMIN = "admin"           # Full access


class AccessControl:
    """Role-based access control system"""

    def __init__(self, config_path: Path = CONFIG_PATH):
        """Initialize access control system"""
        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.permissions: Dict[str, Dict[str, Permission]] = {}
        self.roles: Dict[str, List[str]] = {}
        self.audit_log: List[Dict] = []
        self._init_config()

    def _init_config(self):
        """Initialize default configuration"""
        if not self.config_path.exists():
            self._create_default_config()
        else:
            self._load_config()

    def _create_default_config(self):
        """Create default access control configuration"""
        default_config = {
            "roles": {
                "guest": ["take_screenshot", "read_file", "web_search"],
                "user": [
                    "take_screenshot", "read_file", "write_file", "list_files",
                    "execute_shell", "web_search", "web_fetch", "memory_recall_persistent"
                ],
                "power_user": [
                    # All user tools plus advanced
                    "execute_shell", "execute_python", "git_command",
                    "memory_save_persistent", "memory_search",
                    "cheetah_code_review", "code_analyze"
                ],
                "admin": ["*"]  # All tools
            },
            "tool_categories": {
                "safe": ["take_screenshot", "read_file", "get_system_info", "web_search"],
                "moderate": ["write_file", "execute_shell", "memory_save_persistent"],
                "restricted": ["execute_python", "git_command", "run_security_scan"],
                "dangerous": ["port_scan", "run_nmap_scan", "cheetah_file_sync"]
            },
            "audit_enabled": True,
            "require_confirmation_for": ["execute_python", "run_security_scan", "port_scan"]
        }

        self.config_path.write_text(json.dumps(default_config, indent=2))
        self._load_config()

    def _load_config(self):
        """Load configuration from file"""
        try:
            config = json.loads(self.config_path.read_text())
            self.roles = config.get("roles", {})
            self.tool_categories = config.get("tool_categories", {})
            self.audit_enabled = config.get("audit_enabled", True)
            self.require_confirmation = config.get("require_confirmation_for", [])
        except Exception as e:
            print(f"Error loading access control config: {e}")

    def check_permission(self, user_role: str, tool_name: str) -> bool:
        """Check if user can execute tool"""
        if user_role not in self.roles:
            return False

        allowed_tools = self.roles[user_role]

        # Admin has access to all tools
        if "*" in allowed_tools:
            return True

        return tool_name in allowed_tools

    def get_allowed_tools(self, user_role: str) -> List[str]:
        """Get all tools allowed for a role"""
        if user_role not in self.roles:
            return []

        allowed = self.roles[user_role]
        if "*" in allowed:
            # Return special marker for admin
            return ["<all_tools>"]

        return allowed

    def get_role_permissions(self, user_role: str) -> Dict[str, List[str]]:
        """Get detailed permissions for a role"""
        return {
            "role": user_role,
            "allowed_tools": self.get_allowed_tools(user_role),
            "categories": self._get_allowed_categories(user_role),
            "dangerous_tools_blocked": self._get_blocked_dangerous_tools(user_role)
        }

    def _get_allowed_categories(self, user_role: str) -> List[str]:
        """Get allowed tool categories for role"""
        allowed_tools = self.get_allowed_tools(user_role)
        categories = []

        for cat, tools in self.tool_categories.items():
            if "*" in allowed_tools or any(t in allowed_tools for t in tools):
                categories.append(cat)

        return categories

    def _get_blocked_dangerous_tools(self, user_role: str) -> List[str]:
        """Get dangerous tools blocked for role"""
        allowed = set(self.get_allowed_tools(user_role))
        dangerous = set(self.tool_categories.get("dangerous", []))

        if "*" in allowed:
            return []

        return list(dangerous - allowed)

    def requires_confirmation(self, tool_name: str) -> bool:
        """Check if tool requires confirmation"""
        return tool_name in self.require_confirmation

    def audit(self, user: str, role: str, tool: str, action: str,
              success: bool, details: str = "") -> None:
        """Log access attempt to audit log"""
        if not self.audit_enabled:
            return

        entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "role": role,
            "tool": tool,
            "action": action,
            "success": success,
            "details": details
        }

        self.audit_log.append(entry)

    def get_audit_log(self, user: str = None, limit: int = 100) -> List[Dict]:
        """Get audit log entries"""
        log = self.audit_log

        if user:
            log = [e for e in log if e["user"] == user]

        return log[-limit:]

    def grant_tool_access(self, role: str, tool: str) -> bool:
        """Grant tool access to role"""
        if role not in self.roles:
            return False

        if tool not in self.roles[role] and "*" not in self.roles[role]:
            self.roles[role].append(tool)
            self._save_config()
            return True

        return False

    def revoke_tool_access(self, role: str, tool: str) -> bool:
        """Revoke tool access from role"""
        if role not in self.roles or "*" in self.roles[role]:
            return False

        if tool in self.roles[role]:
            self.roles[role].remove(tool)
            self._save_config()
            return True

        return False

    def _save_config(self):
        """Save configuration to file"""
        config = {
            "roles": self.roles,
            "tool_categories": self.tool_categories,
            "audit_enabled": self.audit_enabled,
            "require_confirmation_for": self.require_confirmation
        }

        self.config_path.write_text(json.dumps(config, indent=2))


# Global instance
_access_control = None


def get_access_control() -> AccessControl:
    """Get or create global access control instance"""
    global _access_control
    if _access_control is None:
        _access_control = AccessControl()
    return _access_control


# Tool functions for integration

def check_tool_permission(user_role: str, tool_name: str) -> Dict[str, Any]:
    """Check if user can execute tool"""
    ac = get_access_control()
    allowed = ac.check_permission(user_role, tool_name)
    needs_confirm = ac.requires_confirmation(tool_name)

    return {
        "tool": tool_name,
        "user_role": user_role,
        "allowed": allowed,
        "requires_confirmation": needs_confirm,
        "message": "Access granted" if allowed else "Access denied"
    }


def get_user_tools(user_role: str) -> Dict[str, Any]:
    """Get all tools available to user"""
    ac = get_access_control()
    return {
        "user_role": user_role,
        "permissions": ac.get_role_permissions(user_role),
        "allowed_tools": ac.get_allowed_tools(user_role),
        "tool_count": len(ac.get_allowed_tools(user_role))
    }


def log_tool_access(user: str, role: str, tool: str, success: bool) -> bool:
    """Log tool access"""
    ac = get_access_control()
    ac.audit(user, role, tool, "execute", success)
    return True


def get_access_audit_log(user: str = None, limit: int = 100) -> List[Dict]:
    """Get audit log for user or all"""
    ac = get_access_control()
    return ac.get_audit_log(user, limit)


def get_role_info(role: str) -> Dict[str, Any]:
    """Get role information"""
    ac = get_access_control()
    return ac.get_role_permissions(role)


def list_all_roles() -> Dict[str, List[str]]:
    """List all roles and their tools"""
    ac = get_access_control()
    return ac.roles


def grant_tool_to_role(role: str, tool: str) -> Dict[str, Any]:
    """Grant tool access to role (admin only)"""
    ac = get_access_control()
    success = ac.grant_tool_access(role, tool)

    return {
        "role": role,
        "tool": tool,
        "success": success,
        "message": "Access granted" if success else "Failed to grant access"
    }


def revoke_tool_from_role(role: str, tool: str) -> Dict[str, Any]:
    """Revoke tool access from role (admin only)"""
    ac = get_access_control()
    success = ac.revoke_tool_access(role, tool)

    return {
        "role": role,
        "tool": tool,
        "success": success,
        "message": "Access revoked" if success else "Failed to revoke access"
    }
