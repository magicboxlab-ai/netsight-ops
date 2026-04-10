"""Exception types for netsight-ops."""

from __future__ import annotations


class ServiceRegistrationError(Exception):
    """Raised when a service fails to register into the ServiceRegistry."""

    def __init__(self, service_name: str, detail: str) -> None:
        self.service_name = service_name
        self.detail = detail
        super().__init__(f"Service '{service_name}' registration failed: {detail}")


class ServiceConflictError(Exception):
    """Raised when two services attempt to register with the same name."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(
            f"Service '{name}' is already registered. "
            "Check for duplicate entry-point declarations."
        )


class ServiceIncompatibleError(Exception):
    """Raised when a service's declared compatibility doesn't match the running ops platform."""

    def __init__(self, service_name: str, detail: str) -> None:
        self.service_name = service_name
        self.detail = detail
        super().__init__(f"Service '{service_name}' is incompatible: {detail}")
