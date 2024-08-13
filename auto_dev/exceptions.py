"""Base exceptions for the auto_dev package."""


class OperationError(Exception):
    """Operation error."""


class NotFound(FileNotFoundError):
    """File not found error."""
