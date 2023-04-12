"""PyWebnovel Error Classes."""


class PyWebnovelError(Exception):
    """A Dummy "root" Exception for all PyWebnovel-specific errors to inherit from."""


class ParseError(ValueError, PyWebnovelError):
    """An error caused due to a failure during parsing."""
