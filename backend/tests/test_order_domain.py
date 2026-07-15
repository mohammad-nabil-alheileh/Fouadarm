import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from fastapi.exceptions import ResponseValidationError

from src.application.orders_service import OrdersService
from src.domain.models import OrderAggregate, ProductBatchDomain
from src.presentation.order_routes import place_order
from src.schemas import PlaceOrderRequest


class OrderDomainTests(unittest.TestCase):
    def test_place_order_uses_product_price_and_honors_total_override(self):
        class StubInventoryRepo:
            def get_batches_for_product_fifo(self, product_id):
                batch = ProductBatchDomain(1, product_id, date.today(), 10, 0, "Q1", "F1", "L1")
                return [batch]

            def get_product_unit_price(self, product_id):
                return Decimal("5.50")

        class StubOrderRepo:
            def save(self, order):
                return 42

        service = OrdersService(conn=None, inventory_repo=StubInventoryRepo(), order_repo=StubOrderRepo())

        order = service.place_order(
            customer_name="Alice",
            requested_items=[{"product_id": 1, "quantity": 2}],
            price_override=Decimal("11.00")
        )

        self.assertEqual(order.total_price, Decimal("11.00"))
        self.assertEqual(order.items[0].price_per_unit, Decimal("5.50"))

    def test_order_item_exposes_product_id_for_serialization(self):
        batch = ProductBatchDomain(1, 7, date.today(), 10, 0, "Q1", "F1", "L1")
        order = OrderAggregate("Alice", date.today())

        order.add_item(batch, 3, Decimal("12.50"))

        self.assertEqual(order.items[0].product_id, batch.product_id)

    def test_place_order_returns_schema_compatible_response(self):
        class StubOrder:
            def __init__(self):
                self.order_id = 3
                self.customer_name = "Alice"
                self.order_date = date.today()
                self.items = [type("Item", (), {"product_id": 7, "quantity": 40, "price_per_unit": Decimal("0")})()]
                self.payments = [type("Payment", (), {"amount": Decimal("0")})()]
                self.manual_total_override = None
                self.total_price = Decimal("0")

        class StubService:
            def __init__(self, *args, **kwargs):
                pass

            def place_order(self, *args, **kwargs):
                return StubOrder()

        payload = PlaceOrderRequest(
            customer_name="Alice",
            items=[{"product_id": 7, "quantity": 40, "price_per_unit": Decimal("0")}],
            payment_method="cash",
            payment_amount=Decimal("0")
        )

        with patch("src.presentation.order_routes.OrdersService", StubService):
            response = place_order(payload, conn=None)

        self.assertEqual(response["total_amount"], Decimal("0"))
        self.assertEqual(response["payment_method"], "cash")


if __name__ == "__main__":
    unittest.main()
