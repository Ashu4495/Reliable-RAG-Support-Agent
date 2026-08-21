import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from app.config import config

class OrderLookupService:
    def __init__(self, orders_path: Optional[Path] = None):
        self.orders_path = orders_path or config.ORDERS_DATA_PATH
        self._orders_db: Dict[str, Dict[str, Any]] = {}
        self._snapshot_at: str = "2026-08-15T12:00:00Z"
        self._load_orders()

    def _load_orders(self):
        if not self.orders_path.exists():
            return
        with open(self.orders_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self._snapshot_at = data.get("snapshot_at", "2026-08-15T12:00:00Z")
            for order in data.get("orders", []):
                oid = order.get("order_id", "").strip().upper()
                if oid:
                    self._orders_db[oid] = order

    @staticmethod
    def extract_order_id(text: str) -> Optional[str]:
        """Extracts potential order ID (ORD-XXXX) from text."""
        if not text:
            return None
        match = re.search(r"\b(ORD-\d{4})\b", text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None

    @staticmethod
    def normalize_order_id(order_id: str) -> str:
        """Normalizes order ID formatting (handles casing, whitespace, punctuation)."""
        if not order_id:
            return ""
        clean = order_id.strip().strip(".,;:!?\"'()[]{}").upper()
        return clean

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Looks up order by ID and returns ONLY customer-safe fields.
        Never returns customer name, email, shipping address, or internal fields.
        Enforces status precedence.
        """
        norm_id = self.normalize_order_id(order_id)
        if not norm_id:
            return {
                "found": False,
                "error": "No order ID provided. Please provide a valid order ID in the format ORD-XXXX.",
                "needs_handoff": False,
            }

        order = self._orders_db.get(norm_id)
        if not order:
            return {
                "found": False,
                "order_id": norm_id,
                "error": f"Order {norm_id} was not found in our system. Please check the order ID or contact customer support for assistance.",
                "needs_handoff": True,
            }

        # Filter safe items
        safe_items = []
        for itm in order.get("items", []):
            safe_items.append({
                "name": itm.get("name"),
                "quantity": itm.get("quantity"),
                "final_sale": itm.get("final_sale", False),
            })

        status = order.get("status")
        
        # Enforce status precedence and filter stale fields
        carrier = order.get("carrier")
        tracking_number = order.get("tracking_number")
        estimated_delivery = order.get("estimated_delivery")
        customer_safe_message = order.get("customer_safe_message")
        needs_handoff = False

        if status == "cancelled":
            # Avoid reporting stale delivery fields for cancelled orders
            estimated_delivery = None
            carrier = None
            tracking_number = None
            customer_safe_message = "The order was cancelled and will not be shipped."
        elif status == "returned":
            estimated_delivery = None
            customer_safe_message = "The return was received and processed."
        elif status == "exception":
            needs_handoff = True
            customer_safe_message = "The shipment has an operational exception that requires support review."
        elif status == "shipped" and not estimated_delivery:
            customer_safe_message = f"The order has shipped with {carrier or 'the carrier'}. A delivery estimate is not currently available."

        safe_result = {
            "found": True,
            "order_id": norm_id,
            "membership_tier": order.get("membership_tier"),
            "items": safe_items,
            "placed_at": order.get("placed_at"),
            "status": status,
            "status_updated_at": order.get("status_updated_at"),
            "shipped_at": order.get("shipped_at") if status in ("shipped", "delayed", "delivered", "exception") else None,
            "delivered_at": order.get("delivered_at") if status == "delivered" else None,
            "carrier": carrier,
            "tracking_number": tracking_number,
            "estimated_delivery": estimated_delivery,
            "customer_safe_message": customer_safe_message,
            "needs_handoff": needs_handoff,
        }

        return safe_result

order_service = OrderLookupService()

def get_order_status(order_id: str) -> Dict[str, Any]:
    """Public tool entrypoint for order lookup."""
    return order_service.get_order_status(order_id)
