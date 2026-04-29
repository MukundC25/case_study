from datetime import datetime, timedelta
from flask import Blueprint, jsonify
from sqlalchemy import func

from app import db
from app.models import (
    Company,
    Inventory,
    InventoryTransaction,
    Product,
    ProductSupplier,
    TransactionType,
    Warehouse,
)

alerts_bp = Blueprint("alerts", __name__)

RECENT_SALES_WINDOW_DAYS = 30
GLOBAL_DEFAULT_THRESHOLD = 10


@alerts_bp.route("/api/companies/<int:company_id>/alerts/low-stock", methods=["GET"])
def low_stock_alerts(company_id):

    company = db.session.get(Company, company_id)
    if not company:
        return jsonify({"error": "Company not found"}), 404

    since = datetime.utcnow() - timedelta(days=RECENT_SALES_WINDOW_DAYS)

    recent_sales_rows = (
        db.session.query(
            InventoryTransaction.inventory_id,
            func.sum(func.abs(InventoryTransaction.quantity_change)).label("total_sold"),
        )
        .filter(
            InventoryTransaction.transaction_type == TransactionType.SALE,
            InventoryTransaction.created_at >= since,
        )
        .group_by(InventoryTransaction.inventory_id)
        .all()
    )

    if not recent_sales_rows:
        return jsonify({"alerts": [], "total_alerts": 0}), 200

    sales_map = {row.inventory_id: int(row.total_sold) for row in recent_sales_rows}

    inventories = (
        Inventory.query.join(Warehouse, Inventory.warehouse_id == Warehouse.id)
        .join(Product, Inventory.product_id == Product.id)
        .filter(
            Warehouse.company_id == company_id,
            Warehouse.is_active.is_(True),
            Inventory.id.in_(list(sales_map.keys())),
        )
        .all()
    )

    alerts = []
    for inv in inventories:
        product = inv.product
        warehouse = inv.warehouse

        if not product.is_active:
            continue

        if inv.low_stock_threshold is not None:
            threshold = inv.low_stock_threshold
        elif product.product_type_id and product.product_type:
            threshold = product.product_type.default_low_stock_threshold
        else:
            threshold = GLOBAL_DEFAULT_THRESHOLD

        if inv.quantity >= threshold:
            continue

        total_sold = sales_map.get(inv.id, 0)
        avg_daily_sales = total_sold / RECENT_SALES_WINDOW_DAYS
        days_until_stockout = (
            int(inv.quantity / avg_daily_sales) if avg_daily_sales > 0 else None
        )

        primary_ps = ProductSupplier.query.filter_by(
            product_id=product.id, is_primary=True
        ).first()

        supplier_data = None
        if primary_ps and primary_ps.supplier:
            s = primary_ps.supplier
            supplier_data = {
                "id": s.id,
                "name": s.name,
                "contact_email": s.contact_email,
            }

        alerts.append(
            {
                "product_id": product.id,
                "product_name": product.name,
                "sku": product.sku,
                "warehouse_id": warehouse.id,
                "warehouse_name": warehouse.name,
                "current_stock": inv.quantity,
                "threshold": threshold,
                "days_until_stockout": days_until_stockout,
                "supplier": supplier_data,
            }
        )

    alerts.sort(
        key=lambda a: (
            a["days_until_stockout"]
            if a["days_until_stockout"] is not None
            else float("inf"),
            a["current_stock"],
        )
    )

    return jsonify({"alerts": alerts, "total_alerts": len(alerts)}), 200
