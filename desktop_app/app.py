import webview
import os
import sys
from src.database.db_manager import LocalDatabaseManager
from src.services.pairing_service import DevicePairingService
from src.services.supabase_sync import SupabaseSyncWorker

class EStoreJSAPI:
    """
    Python Native API Engine exposed to Microsoft Store Fluent Desktop UI.
    0-millisecond latency for SQLite operations, financial calculations, and cloud sync.
    """
    def __init__(self, db: LocalDatabaseManager, pairing: DevicePairingService, sync_worker: SupabaseSyncWorker):
        self.db = db
        self.pairing = pairing
        self.sync_worker = sync_worker

    def get_dashboard_metrics(self):
        return self.db.get_overview_dashboard_metrics()

    def get_categories(self):
        return self.db.get_categories()

    def add_category(self, name):
        return self.db.add_category(name)

    def delete_category(self, cat_id):
        return self.db.delete_category(cat_id)

    def get_all_products(self):
        return self.db.get_all_products()

    def search_products(self, query="", category="All"):
        return self.db.search_products(query, category)

    def add_or_update_product(self, product):
        res = self.db.add_or_update_product(product)
        if self.sync_worker:
            self.sync_worker.trigger_immediate_sync()
        return res

    def delete_product(self, product_id):
        return self.db.delete_product(product_id)

    def process_sale(self, cart_items, payment_method="Cash", discount=0.0):
        res = self.db.process_pos_sale(cart_items, payment_method, float(discount))
        if self.sync_worker:
            self.sync_worker.trigger_immediate_sync()
        return res

    def get_sale_by_receipt(self, receipt_number):
        return self.db.get_sale_by_receipt(receipt_number)

    def process_sales_return(self, sale_id, item_id, return_qty, reason="Customer Return"):
        return self.db.process_sales_return(sale_id, item_id, int(return_qty), reason)

    def get_shop_settings(self):
        return self.db.get_shop_settings()

    def save_shop_settings(self, settings):
        res = self.db.save_shop_settings(settings)
        if self.sync_worker and isinstance(settings, dict):
            url = settings.get('supabase_url', '')
            key = settings.get('supabase_key', '')
            self.sync_worker.update_credentials(url, key)
        return res

    def generate_pair_code(self):
        return self.pairing.generate_pair_code()

    def get_all_udhaar_records(self):
        return self.db.get_all_udhaar_records()

    def add_udhaar_record(self, party_name, party_type, amount, entry_type, notes=""):
        res = self.db.add_udhaar_record(party_name, party_type, float(amount), entry_type, notes)
        if self.sync_worker:
            self.sync_worker.trigger_immediate_sync()
        return res

    def delete_udhaar_record(self, record_id):
        return self.db.delete_udhaar_record(record_id)

    def get_udhaar_summary(self):
        return self.db.get_udhaar_summary()

def main():
    db = LocalDatabaseManager()
    pairing = DevicePairingService(db)
    
    # Initialize and start background silent sync worker with verified Supabase URL & Key
    settings = db.get_shop_settings()
    sync_worker = SupabaseSyncWorker(
        db_manager=db,
        supabase_url=settings.get('supabase_url', ''),
        supabase_key=settings.get('supabase_key', ''),
        device_uuid=pairing.device_uuid
    )
    sync_worker.start()

    api = EStoreJSAPI(db, pairing, sync_worker)

    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    html_path = os.path.join(base_path, "src", "web", "index.html")

    window = webview.create_window(
        title="E-Store POS & Management System",
        url=html_path,
        js_api=api,
        width=1340,
        height=840,
        min_size=(1024, 700),
        resizable=True
    )

    webview.start(debug=False)

if __name__ == "__main__":
    main()
