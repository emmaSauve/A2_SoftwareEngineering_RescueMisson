"""A small starting test suite for the order desk."""

from pathlib import Path
import tempfile
import unittest

from supplydesk.service import OrderService


class OrderSmokeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "state.json"
        self.service = OrderService(self.path)

    def test_regular_pickup_quote(self):
        quote = self.service.quote("regular", [{"product_id": "notebook", "quantity": 2}])
        self.assertEqual(quote["subtotal_cents"], 1000)
        self.assertEqual(quote["discount_cents"], 0)
        self.assertEqual(quote["delivery_cents"], 0)
        self.assertEqual(quote["total_cents"], 1000)

    def test_student_delivery_quote(self):
        quote = self.service.quote("student", [{"product_id": "hoodie", "quantity": 2}], "delivery")
        self.assertEqual(quote["discount_cents"], 800)
        self.assertEqual(quote["delivery_cents"], 600)
        self.assertEqual(quote["total_cents"], 7800)

    def test_order_can_be_reopened(self):
        order = self.service.place_order("regular", [{"product_id": "mug", "quantity": 1}])
        self.assertEqual(order["order_id"], "ORD-0001")
        self.assertEqual(order["status"], "placed")
        self.assertEqual(OrderService(self.path).get_order(order["order_id"]), order)

    def test_cancel_order_restores_stock(self):
        before = self.service.catalog()
        order = self.service.place_order("regular", [{"product_id": "pen-pack", "quantity": 2}])
        cancelled = self.service.cancel_order(order["order_id"])
        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(self.service.catalog(), before)

       #Task 2 tests
    
    def test_successful_order_reduces_stock(self):
        before = self.service.catalog()
        order = self.service.place_order(
            "regular",
            [{"product_id": "notebook", "quantity": 3}]
        )

        after = self.service.catalog()

        self.assertEqual(order["total_cents"], 1500)
        self.assertEqual(after[0]["stock"], before[0]["stock"] - 3)

    def test_student_discount_at_exactly_50_dollars(self):
        quote = self.service.quote(
            "student",
            [{"product_id": "notebook", "quantity": 10}]
        )

        self.assertEqual(quote["subtotal_cents"], 5000)
        self.assertEqual(quote["discount_cents"], 500)
        self.assertEqual(quote["total_cents"], 4500)

    def test_zero_quantity_is_rejected(self):
        before = self.service.catalog()

        with self.assertRaises(ValueError):
            self.service.place_order(
                "regular",
                [{"product_id": "notebook", "quantity": 0}]
            )

        self.assertEqual(self.service.catalog(), before)
        self.assertEqual(self.service.list_orders(), [])

    def test_unknown_product_is_rejected(self):
        before = self.service.catalog()

        with self.assertRaises(ValueError):
            self.service.place_order(
                "regular",
                [{"product_id": "unknown-product", "quantity": 1}]
            )

        self.assertEqual(self.service.catalog(), before)
        self.assertEqual(self.service.list_orders(), [])

    def test_quote_does_not_change_inventory(self):
        before = self.service.catalog()

        self.service.quote(
            "regular",
            [{"product_id": "notebook", "quantity": 2}]
        )

        self.assertEqual(self.service.catalog(), before)
        self.assertEqual(self.service.list_orders(), [])

    def test_duplicate_product_lines_cannot_exceed_stock(self):
        before = self.service.catalog()

        with self.assertRaises(ValueError):
            self.service.place_order(
                "regular",
                [
                    {"product_id": "pen-pack", "quantity": 6},
                    {"product_id": "pen-pack", "quantity": 5}
                ]
            )

        self.assertEqual(self.service.catalog(), before)
        self.assertEqual(self.service.list_orders(), [])

    def test_cancelling_twice_does_not_restore_stock_twice(self):
        order = self.service.place_order(
            "regular",
            [{"product_id": "pen-pack", "quantity": 2}]
        )

        self.service.cancel_order(order["order_id"])
        stock_after_first_cancellation = self.service.catalog()

        self.service.cancel_order(order["order_id"])
        stock_after_second_cancellation = self.service.catalog()

        self.assertEqual(
            stock_after_second_cancellation,
            stock_after_first_cancellation
        )


if __name__ == "__main__":
    unittest.main()
