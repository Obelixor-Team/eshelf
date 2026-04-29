"""Domain exceptions for the services layer."""


class ServiceError(Exception):
    """Base class for exceptions in the services layer."""

    pass


class ExtractionError(ServiceError):
    """Raised when extraction of metadata or covers fails."""

    pass
