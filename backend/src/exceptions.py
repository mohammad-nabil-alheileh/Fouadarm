class NurseryException(Exception):
    """Base exception for all nursery domain errors."""

class ProductAlreadyExistsError(NurseryException):
    """Raised when trying to register a product name that already exists."""

class ProductNotFoundError(NurseryException):
    """Raised when a requested product does not exist."""

class ProductBatchNotFoundError(NurseryException):
    """Raised when a requested product batch does not exist."""

class InsufficientStockError(NurseryException):
    """Raised when there is not enough stock to fulfill an order."""

class InvalidBatchCountError(NurseryException):
    """Raised when a batch count is invalid (e.g., negative or zero)."""

class OrderNotFound(NurseryException):
    """Raised when a requested order does not exist."""
class OrderIsAlreadyCancelled(NurseryException):
    """Raised when a requested order is cancelled."""

class PaymentNotFound(NurseryException):
    """Raised when a requested payment record does not exist."""

class InvalidPaymentAmount(NurseryException):
    """Raised when a payment amount is invalid (e.g., negative or zero)."""