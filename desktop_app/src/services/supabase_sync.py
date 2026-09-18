import time
import json
import requests
import threading
from ..database.db_manager import LocalDatabaseManager

class SupabaseSyncWorker(threading.Thread):
    """
    Asynchronous Background Thread for Offline-First Data Synchronization with Supabase.
    Runs continuously in daemon mode without blocking the main UI or dependent on PySide.
    """
    def __init__(self, db_manager: LocalDatabaseManager, supabase_url: str = "", supabase_key: str = "", device_uuid: str = "default_pc"):
        super().__init__(daemon=True)
        self.db_manager = db_manager
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.device_uuid = device_uuid
        self.is_running = True
        self._trigger_event = threading.Event()

    def trigger_immediate_sync(self):
        """Wakes up the sync loop immediately on local write for zero data loss."""
        self._trigger_event.set()

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
                            payload['device_uuid'] = self.device_uuid
                            res = requests.post(url, headers=headers, json=payload, timeout=5)
                            if res.status_code in [200, 201, 409]:
                                success = True

                        elif action == "INSERT_SALE" and table == "sales":
                            sale_url = f"{self.supabase_url}/rest/v1/sales"
                            sale_payload = payload['sale']
                            sale_payload['device_uuid'] = self.device_uuid
                            sale_res = requests.post(sale_url, headers=headers, json=sale_payload, timeout=5)
                            
                            if sale_res.status_code in [200, 201]:
                                items_url = f"{self.supabase_url}/rest/v1/sale_items"
                                requests.post(items_url, headers=headers, json=payload['items'], timeout=5)
                                success = True

                        elif action == "INSERT_UDHAAR" and table == "udhaar_ledger":
                            u_url = f"{self.supabase_url}/rest/v1/udhaar_ledger"
                            payload['device_uuid'] = self.device_uuid
                            res = requests.post(u_url, headers=headers, json=payload, timeout=5)
                            if res.status_code in [200, 201, 409]:
                                success = True

                        if success:
                            self.db_manager.mark_sync_item_completed(item['id'])

            except Exception:
                pass

            # Zero-latency trigger wait: wakes up immediately on write or checks every 3s
            self._trigger_event.wait(timeout=3)
            self._trigger_event.clear()

    def stop(self):
        self.is_running = False
        self._trigger_event.set()
