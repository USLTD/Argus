"""Permission hierarchy engine.

Usage:
    PermissionHierarchy.grants(Permission.CPU.WRITE, Permission.CPU.READ)  # True
    PermissionHierarchy.grants(Permission.CPU.READ, Permission.CPU.WRITE)  # False
"""

from __future__ import annotations

from collections.abc import Sequence

from backend.interfaces.enums import Permission


class PermissionHierarchy:
    """Determines whether one Permission grants another."""

    @staticmethod
    def grants(granted: Permission, required: Permission) -> bool:
        """Check whether *granted* satisfies *required* via the permission hierarchy.

        Rules:
        - Exact match → True
        - SCRIPT.READ → exact match only (no hierarchy)
        - EXECUTE grants WRITE and READ and all children in same subsystem
        - WRITE grants READ and all children in same subsystem
        - READ grants all READ children deeper in the path (same subsystem)
        - Cross-subsystem never grants (CPU.READ does NOT grant MEMORY.READ)
        """
        if granted == required:
            return True
        # SCRIPT permission — exact match only
        if granted.value.startswith("SCRIPT.") or required.value.startswith("SCRIPT."):
            return False
        g_parts = granted.value.split(".")
        r_parts = required.value.split(".")
        # Different subsystems → False
        if g_parts[0] != r_parts[0]:
            return False

        def _find_action(parts: Sequence[str]) -> tuple[int, str | None]:
            for i, p in enumerate(parts):
                if p in ("READ", "WRITE", "EXECUTE"):
                    return i, p
            return -1, None

        g_act_idx, g_act = _find_action(g_parts)
        r_act_idx, r_act = _find_action(r_parts)

        if g_act is None or r_act is None:
            return False

        TIERS: dict[str, int] = {"READ": 0, "WRITE": 1, "EXECUTE": 2}
        g_tier = TIERS[g_act]
        r_tier = TIERS[r_act]

        if g_tier < r_tier:
            return False
        if g_tier > r_tier:
            # Higher-tier action grants any lower-tier action in same subsystem
            return True

        # Same tier — both READ (same-tier WRITE or EXECUTE handled by exact match above)
        g_scope = g_parts[:g_act_idx]
        r_scope = r_parts[:r_act_idx]

        # granted scope must be a prefix of required scope
        # AND granted must have fewer total segments (parent grants child, not sibling)
        if len(g_parts) >= len(r_parts):
            return False
        return len(g_scope) <= len(r_scope) and all(
            g_scope[i] == r_scope[i] for i in range(len(g_scope))
        )
