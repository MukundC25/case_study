# StockFlow – Take-Home Submission

## Project Structure

```
case_study/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # SQLAlchemy models (all tables)
│   └── routes/
│       ├── products.py      # POST /api/products  (fixed – Part 1)
│       └── alerts.py        # GET  /api/companies/<id>/alerts/low-stock  (Part 3)
├── Mukund Chavan.pdf        # Case Study submission doc
├── config.py                # Environment-based configuration
├── run.py                   # Entry point
├── seed.py                  # Demo data for testing
├── schema.sql               # Full SQL DDL (Part 2)
├── requirements.txt
├── SOLUTION.md              # Written analysis (all 3 parts)
└── README.md
```

## Quick Start

```bash
pip install -r requirements.txt

python seed.py        # creates stockflow.db and loads demo data
python run.py         # starts Flask on http://localhost:5001
```

## Test the Endpoints

```bash
# Low-stock alerts (Part 3)
curl http://localhost:5001/api/companies/1/alerts/low-stock

# Create product (Part 1 – fixed endpoint)
curl -X POST http://localhost:5001/api/products \
     -H "Content-Type: application/json" \
     -d '{"name":"Bolt M6","sku":"BLT-001","price":0.25,"warehouse_id":1,"initial_quantity":100}'

# Duplicate SKU → 409
curl -X POST http://localhost:5001/api/products \
     -H "Content-Type: application/json" \
     -d '{"name":"Dup","sku":"WID-001","price":1.00,"warehouse_id":1,"initial_quantity":10}'

# Missing fields → 400
curl -X POST http://localhost:5001/api/products \
     -H "Content-Type: application/json" \
     -d '{"name":"Incomplete"}'
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///stockflow.db` | SQLAlchemy DB URI |
| `SECRET_KEY` | `dev-secret-key-...` | Flask secret key |
| `FLASK_ENV` | `development` | `development` or `production` |
