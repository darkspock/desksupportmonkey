from enum import Enum


class UserRole(str, Enum):
    """User roles with hierarchical access levels.

    Hierarchy (highest to lowest): SUPER_ADMIN > ADMIN > TECHNICIAN > EMPLOYEE
    """

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    TECHNICIAN = "technician"
    EMPLOYEE = "employee"

    @property
    def level(self) -> int:
        """Numeric level for role comparison."""
        levels = {
            UserRole.SUPER_ADMIN: 4,
            UserRole.ADMIN: 3,
            UserRole.TECHNICIAN: 2,
            UserRole.EMPLOYEE: 1,
        }
        return levels[self]

    def has_access(self, required: "UserRole") -> bool:
        """Check if this role meets or exceeds the required role level."""
        return self.level >= required.level
