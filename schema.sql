-- ============================================================
-- StockFlow – Database Schema (Part 2)
-- ============================================================

-- ------------------------------------------------------------
-- 1. companies
-- ------------------------------------------------------------
CREATE TABLE companies (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- 2. warehouses
-- ------------------------------------------------------------
CREATE TABLE warehouses (
    id         SERIAL PRIMARY KEY,
    company_id INTEGER      NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name       VARCHAR(255) NOT NULL,
    address    TEXT,
    is_active  BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_warehouse_company_id ON warehouses(company_id);

-- ------------------------------------------------------------
-- 3. product_types  (drives low-stock threshold per category)
-- ------------------------------------------------------------
CREATE TABLE product_types (
    id                          SERIAL PRIMARY KEY,
    name                        VARCHAR(100) NOT NULL UNIQUE,
    default_low_stock_threshold INTEGER      NOT NULL DEFAULT 10,
    created_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Seed some sensible defaults
INSERT INTO product_types (name, default_low_stock_threshold) VALUES
    ('Raw Materials',   50),
    ('Finished Goods',  20),
    ('Consumables',     30),
    ('Spare Parts',     10);

-- ------------------------------------------------------------
-- 4. products
-- ------------------------------------------------------------
CREATE TABLE products (
    id              SERIAL PRIMARY KEY,
    company_id      INTEGER        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    product_type_id INTEGER        REFERENCES product_types(id) ON DELETE SET NULL,
    name            VARCHAR(255)   NOT NULL,
    sku             VARCHAR(100)   NOT NULL UNIQUE,
    price           NUMERIC(10,2)  NOT NULL CHECK (price >= 0),
    description     TEXT,
    is_bundle       BOOLEAN        NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN        NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_product_company_id ON products(company_id);
CREATE INDEX ix_product_sku        ON products(sku);

-- ------------------------------------------------------------
-- 5. inventory  (product × warehouse stock record)
-- ------------------------------------------------------------
CREATE TABLE inventory (
    id                   SERIAL PRIMARY KEY,
    product_id           INTEGER     NOT NULL REFERENCES products(id)   ON DELETE CASCADE,
    warehouse_id         INTEGER     NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    quantity             INTEGER     NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    low_stock_threshold  INTEGER,        -- NULL → fall back to product_type default
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_inventory_product_warehouse UNIQUE (product_id, warehouse_id)
);

CREATE INDEX ix_inventory_product_id   ON inventory(product_id);
CREATE INDEX ix_inventory_warehouse_id ON inventory(warehouse_id);

-- ------------------------------------------------------------
-- 6. inventory_transactions  (immutable audit log)
-- ------------------------------------------------------------
CREATE TYPE transaction_type AS ENUM (
    'restock',
    'sale',
    'adjustment',
    'transfer_in',
    'transfer_out'
);

CREATE TABLE inventory_transactions (
    id               SERIAL PRIMARY KEY,
    inventory_id     INTEGER          NOT NULL REFERENCES inventory(id) ON DELETE CASCADE,
    quantity_change  INTEGER          NOT NULL,   -- positive = added, negative = removed
    transaction_type transaction_type NOT NULL,
    reference_id     VARCHAR(100),               -- e.g. order_id, transfer_id
    notes            TEXT,
    created_at       TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    created_by       INTEGER                      -- FK to users table (out of scope here)
);

CREATE INDEX ix_inv_tx_inventory_id     ON inventory_transactions(inventory_id);
CREATE INDEX ix_inv_tx_type_created_at  ON inventory_transactions(transaction_type, created_at);

-- ------------------------------------------------------------
-- 7. suppliers
-- ------------------------------------------------------------
CREATE TABLE suppliers (
    id            SERIAL PRIMARY KEY,
    company_id    INTEGER      NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name          VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    address       TEXT,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_supplier_company_id ON suppliers(company_id);

-- ------------------------------------------------------------
-- 8. product_suppliers  (many-to-many: product ↔ supplier)
-- ------------------------------------------------------------
CREATE TABLE product_suppliers (
    id             SERIAL PRIMARY KEY,
    product_id     INTEGER       NOT NULL REFERENCES products(id)   ON DELETE CASCADE,
    supplier_id    INTEGER       NOT NULL REFERENCES suppliers(id)  ON DELETE CASCADE,
    unit_cost      NUMERIC(10,2),
    lead_time_days INTEGER,
    is_primary     BOOLEAN       NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_product_supplier UNIQUE (product_id, supplier_id)
);

CREATE INDEX ix_ps_product_id ON product_suppliers(product_id);

-- Only one primary supplier per product
CREATE UNIQUE INDEX uq_primary_supplier_per_product
    ON product_suppliers(product_id)
    WHERE is_primary = TRUE;

-- ------------------------------------------------------------
-- 9. bundle_items  (defines what a bundle contains)
-- ------------------------------------------------------------
CREATE TABLE bundle_items (
    id                   SERIAL PRIMARY KEY,
    bundle_product_id    INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    component_product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity             INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),

    CONSTRAINT uq_bundle_component     UNIQUE (bundle_product_id, component_product_id),
    CONSTRAINT ck_no_self_bundle       CHECK  (bundle_product_id <> component_product_id)
);
