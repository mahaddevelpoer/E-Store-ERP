import time
import json
import requests
from PySide6.QtCore import QThread, Signal
from ..database.db_manager import LocalDatabaseManager

class SupabaseSyncWorker(QThread):
    """
    Asynchronous Background Thread for Offline-First Data Synchronization with Supabase.
    Runs continuously without blocking the PySide6 main UI thread.
    """
    sync_status_signal = Signal(str, int) # (status_text, pending_count)
    sync_completed_signal = Signal(dict)

    def __init__(self, db_manager: LocalDatabaseManager, supabase_url: str = "", supabase_key: str = ""):
        super().__init__()
        self.db_manager = db_manager
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.is_running = True

    def run(self):
        while self.is_running:
            try:
                pending_items = self.db_manager.get_pending_sync_items(limit=20)
                count = len(pending_items)

                if count > 0 and self.supabase_url and self.supabase_key:
                    self.sync_status_signal.emit(f"Syncing {count} item(s)...", count)
                    
                    headers = {
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal"
                    }

                    for item in pending_items:
                        table = item['table_name']
                        action = item['action']
                        payload = json.loads(item['payload'])

                        success = False

                        if action == "UPSERT" and table == "products":
                            url = f"{self.supabase_url}/rest/v1/products"
                            res = requests.post(url, headers=headers, json=payload)
                            if res.status_code in [200, 201, 409]:
                                success = True

                        elif action == "INSERT_SALE" and table == "sales":
                            # Post sale record
                            sale_url = f"{self.supabase_url}/rest/v1/sales"
                            sale_res = requests.post(sale_url, headers=headers, json=payload['sale'])
                            
                            if sale_res.status_code in [200, 201]:
                                # Post sale items
                                items_url = f"{self.supabase_url}/rest/v1/sale_items"
                                requests.post(items_url, headers=headers, json=payload['items'])
                                success = True

                        if success:
                            self.db_manager.mark_sync_item_completed(item['id'])

                    remaining = len(self.db_manager.get_pending_sync_items(limit=20))
                    self.sync_status_signal.emit("Synced with Supabase Cloud", remaining)
                else:
                    self.sync_status_signal.emit("All changes synced (Offline Ready)", count)

            except Exception as e:
                self.sync_status_signal.emit(f"Offline Mode ({str(e)[:25]}...)", 0)

            # Sleep 5 seconds between sync checks
            time.sleep(5)

    def stop(self):
        self.is_running = False
        self.wait()
