from backend.services import route_question

def test_router_routes_order_to_sql():
    assert route_question("Where is order 1005?") == "sql"

def test_router_routes_refund_policy_to_rag():
    assert route_question("What is your refund policy?") == "rag"

def test_router_routes_revenue_to_reports():
    assert route_question("Show monthly sales revenue") == "reports"
