import sqlite3
import os
import uuid
import datetime
import json
from typing import List, Dict, Any, Optional

USER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".estore_pos")
os.makedirs(USER_DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(USER_DATA_DIR, "shop_inventory.db")

class LocalDatabaseManager:
    """
    Offline-First Thread-Safe SQLite Database Manager for E-Store Fluent Desktop POS.
    Calculates Capital Investment, Stock Valuation, Hardware/Media Split Revenue, and Returns.
    """
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Shop Settings Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shop_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shop_name TEXT NOT NULL DEFAULT 'E-Store',
                    phone TEXT DEFAULT '',
                    address TEXT DEFAULT '',
                    theme_mode TEXT NOT NULL DEFAULT 'Dark',
                    currency TEXT NOT NULL DEFAULT 'PKR',
                    receipt_footer TEXT DEFAULT 'Thank you for shopping at E-Store!',
                    supabase_url TEXT DEFAULT '',
                    supabase_key TEXT DEFAULT ''
                )
            """)

            # Ensure columns exist if table was already created
            try:
                cursor.execute("ALTER TABLE shop_settings ADD COLUMN supabase_url TEXT DEFAULT ''")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE shop_settings ADD COLUMN supabase_key TEXT DEFAULT ''")
            except Exception:
                pass

            cursor.execute("SELECT COUNT(*) FROM shop_settings")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO shop_settings (shop_name, phone, address, theme_mode, currency, receipt_footer, supabase_url, supabase_key)
                    VALUES ('E-Store', '+92 300 1234567', 'Main Accessories Market', 'Dark', 'PKR', 'Thank you for shopping at E-Store!', '', '')
                """)

            # Dynamic Categories Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL
                )
            """)

            # Seed default categories if empty
            cursor.execute("SELECT COUNT(*) FROM categories")
            if cursor.fetchone()[0] == 0:
                default_cats = ['Fast Chargers', 'Wireless Earbuds', 'USB Cables', 'Power Banks', 'Mobile Covers', 'Screen Protectors']
                for c in default_cats:
                    cursor.execute("INSERT OR IGNORE INTO categories (id, name) VALUES (?, ?)", (str(uuid.uuid4()), c))

            # Dynamic Products Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category_name TEXT NOT NULL DEFAULT 'General',
                    barcode TEXT UNIQUE,
                    cost_price REAL NOT NULL DEFAULT 0.0,
                    selling_price REAL NOT NULL DEFAULT 0.0,
                    stock_quantity INTEGER NOT NULL DEFAULT 0,
                    low_stock_threshold INTEGER NOT NULL DEFAULT 5,
                    image_url TEXT DEFAULT '',
                    updated_at TEXT NOT NULL
                )
            """)

            # Sales Transactions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id TEXT PRIMARY KEY,
                    receipt_number TEXT UNIQUE NOT NULL,
                    total_amount REAL NOT NULL,
                    hardware_revenue REAL NOT NULL DEFAULT 0.0,
                    media_service_revenue REAL NOT NULL DEFAULT 0.0,
                    total_cost REAL NOT NULL DEFAULT 0.0,
                    total_profit REAL NOT NULL DEFAULT 0.0,
                    payment_method TEXT NOT NULL DEFAULT 'Cash',
                    discount REAL DEFAULT 0.0,
                    item_count INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'Completed',
                    created_at TEXT NOT NULL
                )
            """)

            # Sale Items Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sale_items (
                    id TEXT PRIMARY KEY,
                    sale_id TEXT NOT NULL,
                    product_id TEXT,
                    product_name TEXT NOT NULL,
                    item_type TEXT NOT NULL DEFAULT 'Hardware',
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    unit_cost REAL NOT NULL DEFAULT 0.0,
                    total_price REAL NOT NULL,
                    FOREIGN KEY (sale_id) REFERENCES sales (id) ON DELETE CASCADE
                )
            """)

            # Returns Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales_returns (
                    id TEXT PRIMARY KEY,
                    sale_id TEXT NOT NULL,
                    receipt_number TEXT NOT NULL,
                    product_id TEXT,
                    product_name TEXT NOT NULL,
                    returned_qty INTEGER NOT NULL,
                    refund_amount REAL NOT NULL,
                    reason TEXT DEFAULT 'Customer Return',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (sale_id) REFERENCES sales (id)
                )
            """)

            # Udhaar Ledger Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS udhaar_ledger (
                    id TEXT PRIMARY KEY,
                    party_name TEXT NOT NULL,
                    party_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    type TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # Offline Sync Queue Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL
                )
            """)

            # Device Pairings Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS device_pairings (
                    pair_code TEXT PRIMARY KEY,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL
                )
            """)

            conn.commit()

    # --- CATEGORIES CRUD ---
    def get_categories(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories ORDER BY name ASC")
            return [dict(row) for row in cursor.fetchall()]

    def add_category(self, name: str) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cat_id = str(uuid.uuid4())
            cursor.execute("INSERT INTO categories (id, name) VALUES (?, ?)", (cat_id, name.strip()))
            conn.commit()
            return cat_id

    def delete_category(self, cat_id: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
            conn.commit()

    # --- SHOP SETTINGS ---
    def get_shop_settings(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM shop_settings ORDER BY id ASC LIMIT 1")
            row = cursor.fetchone()
            return dict(row) if row else {
                "shop_name": "E-Store",
                "phone": "", "address": "", "theme_mode": "Dark", "currency": "PKR",
                "receipt_footer": "Thank you for shopping at E-Store!"
            }

    def save_shop_settings(self, settings: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE shop_settings SET
                    shop_name = ?,
                    phone = ?,
                    address = ?,
                    theme_mode = ?,
                    currency = ?,
                    receipt_footer = ?,
                    supabase_url = ?,
                    supabase_key = ?
                WHERE id = (SELECT id FROM shop_settings ORDER BY id ASC LIMIT 1)
            """, (
                settings.get('shop_name', 'E-Store'),
                settings.get('phone', ''),
                settings.get('address', ''),
                settings.get('theme_mode', 'Dark'),
                settings.get('currency', 'PKR'),
                settings.get('receipt_footer', 'Thank you!'),
                settings.get('supabase_url', ''),
                settings.get('supabase_key', '')
            ))
            conn.commit()

    # --- PRODUCTS CRUD ---
    def get_all_products(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products ORDER BY name ASC")
            return [dict(row) for row in cursor.fetchall()]

    def search_products(self, query: str = "", category: str = "All") -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            q = f"%{query}%"
            if category != "All" and category != "":
                cursor.execute("""
                    SELECT * FROM products 
                    WHERE (name LIKE ? OR barcode LIKE ?) AND category_name = ?
                    ORDER BY name ASC
                """, (q, q, category))
            else:
                cursor.execute("""
                    SELECT * FROM products 
                    WHERE name LIKE ? OR barcode LIKE ? OR category_name LIKE ?
                    ORDER BY name ASC
                """, (q, q, q))
            return [dict(row) for row in cursor.fetchall()]

    def add_or_update_product(self, product: Dict[str, Any]) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            p_id = product.get("id") or str(uuid.uuid4())
            now = datetime.datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO products (id, name, category_name, barcode, cost_price, selling_price, stock_quantity, low_stock_threshold, image_url, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    category_name=excluded.category_name,
                    barcode=excluded.barcode,
                    cost_price=excluded.cost_price,
                    selling_price=excluded.selling_price,
                    stock_quantity=excluded.stock_quantity,
                    low_stock_threshold=excluded.low_stock_threshold,
                    image_url=excluded.image_url,
                    updated_at=excluded.updated_at
            """, (
                p_id, product['name'], product.get('category_name', 'General'), product.get('barcode', ''),
                float(product.get('cost_price', 0.0)), float(product.get('selling_price', 0.0)),
                int(product.get('stock_quantity', 0)), int(product.get('low_stock_threshold', 5)),
                product.get('image_url', ''), now
            ))

            payload = {**product, "id": p_id, "updated_at": now}
            cursor.execute("""
                INSERT INTO sync_queue (table_name, action, payload, created_at)
                VALUES (?, ?, ?, ?)
            """, ("products", "UPSERT", json.dumps(payload), now))

            conn.commit()
            return p_id

    def delete_product(self, product_id: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()

    # --- POS SALE TRANSACTION ---
    def process_pos_sale(self, cart_items: List[Dict[str, Any]], payment_method: str = "Cash", discount: float = 0.0) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sale_id = str(uuid.uuid4())
            now = datetime.datetime.now().isoformat()
            receipt_num = f"INV-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

            hardware_rev = 0.0
            media_rev = 0.0
            total_cost = 0.0
            sale_items = []

            for item in cart_items:
                product_id = item.get('id')
                item_type = item.get('item_type', 'Hardware')
                qty = item['quantity']
                unit_price = float(item['selling_price'])
                unit_cost = float(item.get('cost_price', 0.0))
                item_total = unit_price * qty
                item_cost_total = unit_cost * qty

                if item_type == 'MediaService':
                    media_rev += item_total
                else:
                    hardware_rev += item_total
                    total_cost += item_cost_total
                    if product_id:
                        cursor.execute("""
                            UPDATE products SET stock_quantity = stock_quantity - ?, updated_at = ?
                            WHERE id = ?
                        """, (qty, now, product_id))

                item_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO sale_items (id, sale_id, product_id, product_name, item_type, quantity, unit_price, unit_cost, total_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (item_id, sale_id, product_id, item['name'], item_type, qty, unit_price, unit_cost, item_total))

                sale_items.append({
                    "id": item_id,
                    "sale_id": sale_id,
                    "product_id": product_id,
                    "product_name": item['name'],
                    "item_type": item_type,
                    "quantity": qty,
                    "unit_price": unit_price,
                    "unit_cost": unit_cost,
                    "total_price": item_total
                })

            gross_total = hardware_rev + media_rev
            final_total = max(0.0, gross_total - discount)
            total_profit = final_total - total_cost

            cursor.execute("""
                INSERT INTO sales (id, receipt_number, total_amount, hardware_revenue, media_service_revenue, total_cost, total_profit, payment_method, discount, item_count, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Completed', ?)
            """, (sale_id, receipt_num, final_total, hardware_rev, media_rev, total_cost, total_profit, payment_method, discount, len(cart_items), now))

            sync_payload = {
                "sale": {
                    "id": sale_id, "receipt_number": receipt_num, "total_amount": final_total,
                    "hardware_revenue": hardware_rev, "media_service_revenue": media_rev,
                    "total_cost": total_cost, "total_profit": total_profit, "payment_method": payment_method,
                    "discount": discount, "item_count": len(cart_items), "created_at": now
                },
                "items": sale_items
            }

            cursor.execute("""
                INSERT INTO sync_queue (table_name, action, payload, created_at)
                VALUES (?, ?, ?, ?)
            """, ("sales", "INSERT_SALE", json.dumps(sync_payload), now))

            conn.commit()

            return {
                "sale_id": sale_id,
                "receipt_number": receipt_num,
                "total_amount": final_total,
                "hardware_revenue": hardware_rev,
                "media_service_revenue": media_rev,
                "total_profit": total_profit,
                "item_count": len(cart_items)
            }

    # --- FINANCIAL & OVERVIEW DASHBOARD METRICS ---
    def get_overview_dashboard_metrics(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Capital Invested (Sum of cost_price * stock_quantity)
            cursor.execute("SELECT COALESCE(SUM(cost_price * stock_quantity), 0.0) FROM products")
            total_capital = cursor.fetchone()[0]

            # Total Stock Valuation (Sum of selling_price * stock_quantity)
            cursor.execute("SELECT COALESCE(SUM(selling_price * stock_quantity), 0.0) FROM products")
            total_stock_value = cursor.fetchone()[0]

            # Products Count & Low Stock Count
            cursor.execute("SELECT COUNT(*), COALESCE(SUM(CASE WHEN stock_quantity <= low_stock_threshold THEN 1 ELSE 0 END), 0) FROM products")
            p_count, low_stock_count = cursor.fetchone()

            # Sales Summary
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(hardware_revenue), 0.0) as total_hardware,
                    COALESCE(SUM(media_service_revenue), 0.0) as total_media,
                    COALESCE(SUM(total_amount), 0.0) as gross_revenue,
                    COALESCE(SUM(total_profit), 0.0) as net_profit,
                    COUNT(*) as total_sales_count
                FROM sales
            """)
            s_row = cursor.fetchone()
            sales_summary = dict(s_row)

            return {
                "capital_invested": total_capital,
                "stock_valuation": total_stock_value,
                "total_products_count": p_count,
                "low_stock_count": low_stock_count,
                "total_hardware_revenue": sales_summary['total_hardware'],
                "total_media_revenue": sales_summary['total_media'],
                "gross_revenue": sales_summary['gross_revenue'],
                "net_profit": sales_summary['net_profit'],
                "total_sales_count": sales_summary['total_sales_count']
            }

    # --- SALES RETURNS & REFUNDS ---
    def get_sale_by_receipt(self, receipt_number: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sales WHERE receipt_number = ?", (receipt_number.strip(),))
            sale_row = cursor.fetchone()
            if not sale_row:
                return None
            
            sale = dict(sale_row)
            cursor.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sale['id'],))
            sale['items'] = [dict(r) for r in cursor.fetchall()]
            return sale

    def process_sales_return(self, sale_id: str, item_id: str, return_qty: int, reason: str = "Customer Return") -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.datetime.now().isoformat()

            cursor.execute("SELECT * FROM sale_items WHERE id = ?", (item_id,))
            item = cursor.fetchone()
            if not item:
                raise ValueError("Sale item not found")
            item = dict(item)

            cursor.execute("SELECT * FROM sales WHERE id = ?", (sale_id,))
            sale = dict(cursor.fetchone())

            refund_amount = item['unit_price'] * return_qty
            refund_cost = item['unit_cost'] * return_qty
            product_id = item['product_id']

            if item['item_type'] == 'Hardware' and product_id:
                cursor.execute("""
                    UPDATE products SET stock_quantity = stock_quantity + ?, updated_at = ?
                    WHERE id = ?
                """, (return_qty, now, product_id))

            return_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO sales_returns (id, sale_id, receipt_number, product_id, product_name, returned_qty, refund_amount, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (return_id, sale_id, sale['receipt_number'], product_id, item['product_name'], return_qty, refund_amount, reason, now))

            new_total = max(0.0, sale['total_amount'] - refund_amount)
            new_profit = sale['total_profit'] - (refund_amount - refund_cost)

            if item['item_type'] == 'MediaService':
                new_media_rev = max(0.0, sale['media_service_revenue'] - refund_amount)
                cursor.execute("""
                    UPDATE sales SET total_amount = ?, media_service_revenue = ?, total_profit = ?, status = 'PartialRefund'
                    WHERE id = ?
                """, (new_total, new_media_rev, new_profit, sale_id))
            else:
                new_hw_rev = max(0.0, sale['hardware_revenue'] - refund_amount)
                cursor.execute("""
                    UPDATE sales SET total_amount = ?, hardware_revenue = ?, total_profit = ?, status = 'PartialRefund'
                    WHERE id = ?
                """, (new_total, new_hw_rev, new_profit, sale_id))

            conn.commit()
            return {
                "receipt_number": sale['receipt_number'],
                "product_name": item['product_name'],
                "returned_qty": return_qty,
                "refund_amount": refund_amount
            }

    # --- SYNC QUEUE ---
    def get_pending_sync_items(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sync_queue WHERE status = 'pending' ORDER BY id ASC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def mark_sync_item_completed(self, item_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE sync_queue SET status = 'synced' WHERE id = ?", (item_id,))
            conn.commit()

    # --- UDHAAR / CREDIT LEDGER CRUD ---
    def get_all_udhaar_records(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS udhaar_ledger (
                    id TEXT PRIMARY KEY,
                    party_name TEXT NOT NULL,
                    party_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    type TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("SELECT * FROM udhaar_ledger ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def add_udhaar_record(self, party_name: str, party_type: str, amount: float, entry_type: str, notes: str = "") -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            rec_id = str(uuid.uuid4())
            now = datetime.datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO udhaar_ledger (id, party_name, party_type, amount, type, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (rec_id, party_name.strip(), party_type.strip(), float(amount), entry_type.strip(), notes.strip(), now))

            payload = {
                "id": rec_id,
                "party_name": party_name.strip(),
                "party_type": party_type.strip(),
                "amount": float(amount),
                "type": entry_type.strip(),
                "notes": notes.strip(),
                "created_at": now
            }
            cursor.execute("""
                INSERT INTO sync_queue (table_name, action, payload, created_at)
                VALUES (?, ?, ?, ?)
            """, ("udhaar_ledger", "INSERT_UDHAAR", json.dumps(payload), now))

            conn.commit()
            return rec_id

    def delete_udhaar_record(self, record_id: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM udhaar_ledger WHERE id = ?", (record_id,))
            conn.commit()

    def get_udhaar_summary(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM udhaar_ledger")
            rows = [dict(r) for r in cursor.fetchall()]
            
            # Net customer udhaar = (Customer Given/Payable - Customer Received)
            customer_given = sum(r['amount'] for r in rows if r['party_type'] == 'Customer' and r['type'] == 'Given')
            customer_received = sum(r['amount'] for r in rows if r['party_type'] == 'Customer' and r['type'] == 'Received')
            net_customer_due = max(0.0, customer_given - customer_received)

            supplier_payable = sum(r['amount'] for r in rows if r['party_type'] == 'Supplier' and r['type'] == 'Payable')
            supplier_paid = sum(r['amount'] for r in rows if r['party_type'] == 'Supplier' and r['type'] == 'Paid')
            net_supplier_due = max(0.0, supplier_payable - supplier_paid)

            return {
                "customer_due": net_customer_due,
                "supplier_due": net_supplier_due,
                "total_records": len(rows)
            }

