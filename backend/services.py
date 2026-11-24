
import re
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .models import Customer, Product, Order, SupportTicket
from .rag import answer_from_rag


def route_question(question: str):
    q = question.lower()

    # Sales-related questions go to reports
    if any(w in q for w in ["sales report", "monthly sales", "revenue"]):
        return "reports"

    # Database-related questions go to SQL
    if any(w in q for w in [
        "order", "tracking", "shipment", "customer",
        "refund status", "payment", "ticket", "complaint",
        "stock", "inventory"
    ]):
        return "sql"

    # Other questions go to document-based RAG
    return "rag"


def sql_lookup(question: str, db: Session):
    q = question.lower()

    # 1. Search for a specific order ID
    order_match = re.search(
        r"(?:order\s*(?:id|number|#)?\s*)(\d{1,8})", q
    )

    if order_match:
        order_id = int(order_match.group(1))

        row = db.execute(
            select(Order, Customer)
            .join(Customer, Order.customer_id == Customer.id)
            .where(Order.id == order_id)
        ).first()

        if not row:
            return {
                "answer": f"I could not find order {order_id}.",
                "data": []
            }

        order, customer = row

        return {
            "answer": (
                f"Order {order.id} for {customer.name}: "
                f"status is {order.status}; "
                f"total is ₹{order.total_amount:,.2f}; "
                f"payment status is {order.payment_status}; "
                f"tracking number is {order.tracking_number}."
            ),
            "data": [{
                "order_id": order.id,
                "customer": customer.name,
                "status": order.status,
                "total_amount": order.total_amount,
                "payment_status": order.payment_status,
                "tracking_number": order.tracking_number
            }]
        }

    # 2. Display all orders and their statuses
    if "order" in q:
        rows = db.execute(
            select(Order, Customer)
            .join(Customer, Order.customer_id == Customer.id)
            .order_by(Order.id)
            .limit(50)
        ).all()

        data = [{
            "order_id": order.id,
            "customer": customer.name,
            "status": order.status,
            "total_amount": order.total_amount,
            "payment_status": order.payment_status
        } for order, customer in rows]

        return {
            "answer": f"Found {len(data)} orders.",
            "data": data
        }

    # 3. Customer information
    if "customer" in q:
        customers = db.scalars(
            select(Customer).limit(20)
        ).all()

        data = [{
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "city": c.city
        } for c in customers]

        return {
            "answer": f"Found {len(data)} sample customers.",
            "data": data
        }

    # 4. Support tickets
    if "ticket" in q or "complaint" in q:
        tickets = db.scalars(
            select(SupportTicket).limit(30)
        ).all()

        data = [{
            "id": t.id,
            "customer_id": t.customer_id,
            "subject": t.subject,
            "status": t.status,
            "priority": t.priority
        } for t in tickets]

        return {
            "answer": f"Found {len(data)} support tickets.",
            "data": data
        }

    # 5. Inventory and low-stock products
    if "stock" in q or "inventory" in q:
        query = select(Product)

        if "low stock" in q or "below 5" in q:
            query = query.where(Product.stock < 5)

        products = db.scalars(
            query.order_by(Product.stock.asc())
        ).all()

        data = [{
            "id": p.id,
            "product": p.name,
            "stock": p.stock,
            "price": p.price
        } for p in products]

        return {
            "answer": f"Found {len(data)} matching inventory products.",
            "data": data
        }

    return {
        "answer": (
            "I can look up orders, customers, support tickets "
            "and inventory. Please try a more specific question."
        ),
        "data": []
    }


def report_lookup(question: str, db: Session):
    revenue = db.scalar(
        select(func.coalesce(func.sum(Order.total_amount), 0))
        .where(Order.status != "Cancelled")
    ) or 0

    order_count = db.scalar(
        select(func.count(Order.id))
    ) or 0

    low_stock = db.scalars(
        select(Product)
        .where(Product.stock < 5)
        .order_by(Product.stock)
    ).all()

    data = [
        {"product": p.name, "stock": p.stock}
        for p in low_stock
    ]

    return {
        "answer": (
            f"Sample business snapshot: {order_count} orders recorded; "
            f"gross value of non-cancelled orders is ₹{revenue:,.2f}; "
            f"{len(data)} products have fewer than 5 units in stock."
        ),
        "data": data,
        "metrics": {
            "orders": order_count,
            "revenue": float(revenue),
            "low_stock_products": len(data)
        }
    }


def handle_question(question: str, db: Session):
    route = route_question(question)

    if route == "sql":
        result = sql_lookup(question, db)
    elif route == "reports":
        result = report_lookup(question, db)
    else:
        result = answer_from_rag(question)

    result["route"] = route
    return result
