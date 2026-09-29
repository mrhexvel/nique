from __future__ import annotations


class NiqueError(Exception):
    """Base exception for all expected NiQue failures."""


class TransportError(NiqueError):
    """HTTP transport failed before a valid response was received."""


class TransportTimeoutError(TransportError):
    """HTTP request timed out."""


class TransportConnectionError(TransportError):
    """HTTP connection could not be established or was interrupted."""


class TransportProtocolError(TransportError):
    """Remote endpoint returned an invalid transport-level response."""


class DependencyResolutionError(NiqueError):
    """A dependency cannot be resolved in the active scope."""


class LifecycleError(NiqueError):
    """An operation is invalid for the current lifecycle state."""
