"""
Run:  python seed.py
"""
from datetime import datetime, timedelta
from decimal import Decimal

from app import create_app, db
from app.models import (
    BundleItem,
    Company,
    Inventory,
    InventoryTransaction,
    Product,
    ProductSupplier,
    ProductType,
    Supplier,
    TransactionType,
    Warehouse,
)


def seed():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        company = Company(name="Acme Corp")
        db.session.add(company)
        db.session.flush()

        wh1 = Warehouse(company_id=company.id, name="Main Warehouse", address="123 Main St, Springfield")
        wh2 = Warehouse(company_id=company.id, name="East Warehouse", address="456 East Ave, Shelbyville")
        db.session.add_all([wh1, wh2])
        db.session.flush()

        pt_raw = ProductType(name="Raw Materials",  default_low_stock_threshold=50)
        pt_fin = ProductType(name="Finished Goods", default_low_stock_threshold=20)
        pt_con = ProductType(name="Consumables",    default_low_stock_threshold=30)
        db.session.add_all([pt_raw, pt_fin, pt_con])
        db.session.flush()

        p1 = Product(company_id=company.id, product_type_id=pt_fin.id, name="Widget A",      sku="WID-001", price=Decimal("29.99"))
        p2 = Product(company_id=company.id, product_type_id=pt_fin.id, name="Gadget B",      sku="GAD-002", price=Decimal("49.99"))
        p3 = Product(company_id=company.id, product_type_id=pt_raw.id, name="Steel Rod",     sku="STL-001", price=Decimal("5.50"))
        p4 = Product(company_id=company.id, product_type_id=pt_con.id, name="Packaging Box", sku="PKG-001", price=Decimal("1.20"))
        p5 = Product(company_id=company.id, product_type_id=pt_fin.id, name="Starter Kit",   sku="KIT-001", price=Decimal("69.99"), is_bundle=True)
        db.session.add_all([p1, p2, p3, p4, p5])
        db.session.flush()

        db.session.add_all([
            BundleItem(bundle_product_id=p5.id, component_product_id=p1.id, quantity=1),
            BundleItem(bundle_product_id=p5.id, component_product_id=p2.id, quantity=1),
        ])

        inv1 = Inventory(product_id=p1.id, warehouse_id=wh1.id, quantity=5)    # LOW  (threshold 20)
        inv2 = Inventory(product_id=p2.id, warehouse_id=wh1.id, quantity=50)   # OK
        inv3 = Inventory(product_id=p3.id, warehouse_id=wh1.id, quantity=10)   # LOW  (threshold 50)
        inv4 = Inventory(product_id=p4.id, warehouse_id=wh1.id, quantity=25)   # LOW  (threshold 30)
        inv5 = Inventory(product_id=p1.id, warehouse_id=wh2.id, quantity=3)    # LOW
        inv6 = Inventory(product_id=p3.id, warehouse_id=wh2.id, quantity=200)  # OK
        db.session.add_all([inv1, inv2, inv3, inv4, inv5, inv6])
        db.session.flush()

        supplier = Supplier(
            company_id=company.id,
            name="Supplier Corp",
            contact_email="orders@supplier.com",
            contact_phone="+1-555-0100",
        )
        db.session.add(supplier)
        db.session.flush()

        db.session.add_all([
            ProductSupplier(product_id=p1.id, supplier_id=supplier.id, unit_cost=Decimal("18.00"), lead_time_days=7,  is_primary=True),
            ProductSupplier(product_id=p3.id, supplier_id=supplier.id, unit_cost=Decimal("3.50"),  lead_time_days=14, is_primary=True),
            ProductSupplier(product_id=p4.id, supplier_id=supplier.id, unit_cost=Decimal("0.80"),  lead_time_days=5,  is_primary=True),
        ])

        now = datetime.utcnow()
        db.session.add_all([
            InventoryTransaction(inventory_id=inv1.id, quantity_change=-5,  transaction_type=TransactionType.SALE, created_at=now - timedelta(days=5)),
            InventoryTransaction(inventory_id=inv1.id, quantity_change=-5,  transaction_type=TransactionType.SALE, created_at=now - timedelta(days=15)),
            InventoryTransaction(inventory_id=inv1.id, quantity_change=-5,  transaction_type=TransactionType.SALE, created_at=now - timedelta(days=25)),
            InventoryTransaction(inventory_id=inv3.id, quantity_change=-20, transaction_type=TransactionType.SALE, created_at=now - timedelta(days=10)),
            InventoryTransaction(inventory_id=inv3.id, quantity_change=-20, transaction_type=TransactionType.SALE, created_at=now - timedelta(days=20)),
            InventoryTransaction(inventory_id=inv4.id, quantity_change=-3,  transaction_type=TransactionType.SALE, created_at=now - timedelta(days=8)),
            InventoryTransaction(inventory_id=inv4.id, quantity_change=-2,  transaction_type=TransactionType.SALE, created_at=now - timedelta(days=18)),
            InventoryTransaction(inventory_id=inv2.id, quantity_change=-10, transaction_type=TransactionType.SALE, created_at=now - timedelta(days=12)),
            InventoryTransaction(inventory_id=inv5.id, quantity_change=-8,  transaction_type=TransactionType.SALE, created_at=now - timedelta(days=3)),
        ])

        db.session.commit()
        print("Seeded successfully!")
        print(f"  Company ID : {company.id}")
        print(f"  Warehouse IDs: {wh1.id} (Main), {wh2.id} (East)")
        print(f"\nTest: GET http://localhost:5001/api/companies/{company.id}/alerts/low-stock")


if __name__ == "__main__":
    seed()
