from datetime import datetime, timedelta
from sqlalchemy import select
from .db import Base, engine, SessionLocal
from .models import Customer, Product, Order, OrderItem, SupportTicket

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.scalar(select(Customer.id).limit(1)):
            return
        customers = [
            Customer(name="Aarav Sharma", email="aarav@example.com", city="Bengaluru"),
            Customer(name="Diya Rao", email="diya@example.com", city="Mysuru"),
            Customer(name="Kabir Mehta", email="kabir@example.com", city="Hyderabad"),
            Customer(name="Ananya Iyer", email="ananya@example.com", city="Chennai"),
            Customer(name="Rohan Das", email="rohan@example.com", city="Pune"),
        ]
        products = [
            Product(name="Wireless Headphones", category="Electronics", price=2499, stock=12),
            Product(name="Mechanical Keyboard", category="Electronics", price=3499, stock=4),
            Product(name="Cotton T-Shirt", category="Fashion", price=599, stock=48),
            Product(name="Running Shoes", category="Fashion", price=2199, stock=7),
            Product(name="Insulated Water Bottle", category="Home", price=799, stock=2),
        ]
        db.add_all(customers + products)
        db.flush()
        statuses = ["Delivered", "Shipped", "Processing", "Cancelled", "Delivered", "Shipped", "Processing"]
        for i in range(1, 16):
            customer = customers[(i - 1) % len(customers)]
            product = products[(i - 1) % len(products)]
            qty = (i % 3) + 1
            status = statuses[(i - 1) % len(statuses)]
            order = Order(customer_id=customer.id, order_date=datetime.utcnow()-timedelta(days=i*2),
                          status=status, total_amount=round(product.price*qty, 2),
                          payment_status="Refunded" if status == "Cancelled" else "Paid",
                          tracking_number=f"TRK-{10000+i}")
            db.add(order)
            db.flush()
            db.add(OrderItem(order_id=order.id, product_id=product.id, quantity=qty, unit_price=product.price))
        db.add_all([
            SupportTicket(customer_id=customers[0].id, subject="Package delayed", status="Open", priority="High",
                          description="Customer reports that the package has not arrived."),
            SupportTicket(customer_id=customers[1].id, subject="Refund status", status="In Progress", priority="Normal",
                          description="Customer is checking on a refund."),
            SupportTicket(customer_id=customers[2].id, subject="Product information", status="Closed", priority="Low",
                          description="Question about product specifications."),
        ])
        db.commit()
    finally:
        db.close()
