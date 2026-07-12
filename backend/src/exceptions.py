class NurseryException(Exception):
    """Base exception for all nursery domain errors."""
    pass

class ProductAlreadyExistsError(NurseryException):
    """Raised when trying to register a product name that already exists."""
    pass

class ProductNotFoundError(NurseryException):
    """Raised when a requested product does not exist."""
    pass

class ProductBatchNotFoundError(NurseryException):
    """Raised when a requested product batch does not exist."""
    pass

class OrderNotFound(NurseryException):
    """Raised when a requested order does not exist."""
    pass
class OrderIsAlreadyCancelled(NurseryException):
    """Raised when a requested order is cancelled."""
    pass