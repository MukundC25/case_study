from flask import Blueprint, request, jsonify
from decimal import Decimal, InvalidOperation
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Product, Inventory, Warehouse

products_bp = Blueprint("products", __name__)


@products_bp.route("/api/products", methods=["POST"])
def create_product():
    """
    Fixed version of the original create_product endpoint.

    Issues fixed from the original code:
    1. request.json can return None → use get_json(silent=True) and validate
    2. No required-field validation → KeyError crashes in production
    3. Two separate commits → partial failure leaves product without inventory (data inconsistency)
    4. No exception handling → raw 500 with stack trace returned to clients
    5. No price validation → negative or non-numeric values accepted
    6. No initial_quantity validation → negative quantities allowed
    7. No warehouse existence check → FK violation surfaces as unhandled 500
    8. No SKU uniqueness check → raw IntegrityError exposed; also race condition window
    9. Wrong HTTP status 200 → should be 201 Created for resource creation
    10. Product.warehouse_id design flaw → products can only be in one warehouse;
        fixed by removing warehouse_id from Product and handling it only via Inventory
    """

    data = request.get_json(silent=True)
    if not data:
        return (
            jsonify(
                {"error": "Request body must be valid JSON with Content-Type: application/json"}
            ),
            400,
        )

    required_fields = ["name", "sku", "price", "warehouse_id", "initial_quantity"]
    missing = [f for f in required_fields if f not in data or data[f] is None]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    name = str(data["name"]).strip()
    if not name:
        return jsonify({"error": "Product name cannot be empty"}), 400

    sku = str(data["sku"]).strip().upper()
    if not sku:
        return jsonify({"error": "SKU cannot be empty"}), 400

    try:
        price = Decimal(str(data["price"]))
        if price < 0:
            return jsonify({"error": "Price must be non-negative"}), 400
    except (InvalidOperation, TypeError):
        return jsonify({"error": "Price must be a valid number"}), 400

    try:
        initial_quantity = int(data["initial_quantity"])
        if initial_quantity < 0:
            return jsonify({"error": "Initial quantity must be non-negative"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "initial_quantity must be a non-negative integer"}), 400

    warehouse = db.session.get(Warehouse, data["warehouse_id"])
    if not warehouse:
        return jsonify({"error": f"Warehouse {data['warehouse_id']} not found"}), 404

    if Product.query.filter_by(sku=sku).first():
        return jsonify({"error": f"SKU '{sku}' already exists"}), 409

    try:
        product = Product(
            name=name,
            sku=sku,
            price=price,
            company_id=warehouse.company_id,
            description=data.get("description"),
            product_type_id=data.get("product_type_id"),
        )
        db.session.add(product)
        db.session.flush()

        inventory = Inventory(
            product_id=product.id,
            warehouse_id=warehouse.id,
            quantity=initial_quantity,
        )
        db.session.add(inventory)
        db.session.commit()

    except IntegrityError as e:
        db.session.rollback()
        if "sku" in str(e.orig).lower():
            return jsonify({"error": f"SKU '{sku}' already exists"}), 409
        return jsonify({"error": "Database integrity error"}), 409
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An unexpected error occurred"}), 500

    return jsonify({"message": "Product created", "product_id": product.id}), 201
