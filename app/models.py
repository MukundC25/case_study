from datetime import datetime
from enum import Enum as PyEnum

from app import db


class TransactionType(PyEnum):
    RESTOCK = "restock"
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    warehouses = db.relationship("Warehouse", backref="company", lazy="select")
    products = db.relationship("Product", backref="company", lazy="select")
    suppliers = db.relationship("Supplier", backref="company", lazy="select")


class Warehouse(db.Model):
    __tablename__ = "warehouses"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    inventories = db.relationship("Inventory", backref="warehouse", lazy="select")

    __table_args__ = (db.Index("ix_warehouse_company_id", "company_id"),)


class ProductType(db.Model):
    __tablename__ = "product_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    default_low_stock_threshold = db.Column(db.Integer, nullable=False, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    products = db.relationship("Product", backref="product_type", lazy="select")


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    product_type_id = db.Column(
        db.Integer, db.ForeignKey("product_types.id", ondelete="SET NULL"), nullable=True
    )
    name = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100), nullable=False, unique=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    is_bundle = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    inventories = db.relationship("Inventory", backref="product", lazy="select")
    bundle_items = db.relationship(
        "BundleItem",
        foreign_keys="BundleItem.bundle_product_id",
        backref="bundle_product",
        lazy="select",
    )
    component_of = db.relationship(
        "BundleItem",
        foreign_keys="BundleItem.component_product_id",
        backref="component_product",
        lazy="select",
    )
    product_suppliers = db.relationship(
        "ProductSupplier", backref="product", lazy="select"
    )

    __table_args__ = (
        db.Index("ix_product_company_id", "company_id"),
        db.Index("ix_product_sku", "sku"),
    )


class Inventory(db.Model):
    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    warehouse_id = db.Column(
        db.Integer, db.ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False
    )
    quantity = db.Column(db.Integer, nullable=False, default=0)
    low_stock_threshold = db.Column(db.Integer, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    transactions = db.relationship(
        "InventoryTransaction", backref="inventory", lazy="select"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "product_id", "warehouse_id", name="uq_inventory_product_warehouse"
        ),
        db.Index("ix_inventory_product_id", "product_id"),
        db.Index("ix_inventory_warehouse_id", "warehouse_id"),
        db.CheckConstraint("quantity >= 0", name="ck_inventory_quantity_non_negative"),
    )


class InventoryTransaction(db.Model):
    __tablename__ = "inventory_transactions"

    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(
        db.Integer, db.ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False
    )
    quantity_change = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.Enum(TransactionType), nullable=False)
    reference_id = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, nullable=True)

    __table_args__ = (
        db.Index("ix_inv_tx_inventory_id", "inventory_id"),
        db.Index("ix_inv_tx_type_created_at", "transaction_type", "created_at"),
    )


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    name = db.Column(db.String(255), nullable=False)
    contact_email = db.Column(db.String(255))
    contact_phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    product_suppliers = db.relationship(
        "ProductSupplier", backref="supplier", lazy="select"
    )

    __table_args__ = (db.Index("ix_supplier_company_id", "company_id"),)


class ProductSupplier(db.Model):
    __tablename__ = "product_suppliers"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    supplier_id = db.Column(
        db.Integer, db.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )
    unit_cost = db.Column(db.Numeric(10, 2))
    lead_time_days = db.Column(db.Integer)
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("product_id", "supplier_id", name="uq_product_supplier"),
        db.Index("ix_ps_product_id", "product_id"),
    )


class BundleItem(db.Model):
    __tablename__ = "bundle_items"

    id = db.Column(db.Integer, primary_key=True)
    bundle_product_id = db.Column(
        db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    component_product_id = db.Column(
        db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    quantity = db.Column(db.Integer, nullable=False, default=1)

    __table_args__ = (
        db.UniqueConstraint(
            "bundle_product_id",
            "component_product_id",
            name="uq_bundle_component",
        ),
        db.CheckConstraint(
            "bundle_product_id != component_product_id", name="ck_no_self_bundle"
        ),
        db.CheckConstraint(
            "quantity > 0", name="ck_bundle_item_quantity_positive"
        ),
    )
