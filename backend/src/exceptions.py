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

class InsufficientStockError(NurseryException):
    """Raised when there is not enough stock to fulfill an order."""
    pass

class InvalidBatchCountError(NurseryException):
    """Raised when a batch count is invalid (e.g., negative or zero)."""
    pass

class OrderNotFound(NurseryException):
    """Raised when a requested order does not exist."""
    pass
class OrderIsAlreadyCancelled(NurseryException):
    """Raised when a requested order is cancelled."""
    pass

class PaymentNotFound(NurseryException):
    """Raised when a requested payment record does not exist."""
    pass

class InvalidPaymentAmount(NurseryException):
    """Raised when a payment amount is invalid (e.g., negative or zero)."""
    pass