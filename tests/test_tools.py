import pytest
from app.tools import OrderLookupService, get_order_status

def test_order_id_normalization():
    svc = OrderLookupService()
    assert svc.normalize_order_id("ord-1007") == "ORD-1007"
    assert svc.normalize_order_id("  ORD-1007.  ") == "ORD-1007"
    assert svc.normalize_order_id("ORD-1007!") == "ORD-1007"
    assert svc.extract_order_id("Where is ord-1007 today?") == "ORD-1007"

def test_valid_order_lookup_and_privacy_whitelisting():
    res = get_order_status("ORD-1007")
    assert res["found"] is True
    assert res["order_id"] == "ORD-1007"
    assert res["status"] == "shipped"
    assert res["carrier"] == "UPS"
    assert res["estimated_delivery"] == "2026-08-22"

    # Verify sensitive/internal fields are NOT present
    assert "email" not in res
    assert "shipping_address" not in res
    assert "risk_score" not in res
    assert "internal" not in res
    assert "warehouse_note" not in res
    assert "support_tags" not in res

def test_cancelled_order_stale_eta_suppression():
    res = get_order_status("ORD-1004")
    assert res["found"] is True
    assert res["status"] == "cancelled"
    # Stale estimated delivery must be suppressed
    assert res["estimated_delivery"] is None
    assert res["carrier"] is None
    assert "cancelled" in res["customer_safe_message"].lower()

def test_shipped_order_without_eta():
    res = get_order_status("ORD-1011")
    assert res["found"] is True
    assert res["status"] == "shipped"
    assert res["carrier"] == "Canada Post"
    assert res["estimated_delivery"] is None

def test_order_exception_handoff():
    res = get_order_status("ORD-1010")
    assert res["found"] is True
    assert res["status"] == "exception"
    assert res["needs_handoff"] is True

def test_unknown_order_id():
    res = get_order_status("ORD-9999")
    assert res["found"] is False
    assert res["needs_handoff"] is True
    assert "not found" in res["error"].lower()
