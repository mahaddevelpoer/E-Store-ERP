import time
import json
import requests
import threading
from typing import Optional
from ..database.db_manager import LocalDatabaseManager

DEFAULT_SUPABASE_URL = "https://vdaqzfyijonojuwzwpyb.supabase.co"
DEFAULT_SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZkYXF6Znlpam9ub2p1d3p3cHliIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk2MjAzNjIsImV4cCI6MjEwNTE5NjM2Mn0.8be3HTOvti0FnOy5lX08gW5JnuyDFeq2OoeW5Lf0p9s"

class SupabaseSyncWorker(threading.Thread):
    """
    Asynchronous Background Thread for Real-Time Zero-Loss Cloud Sync with Supabase.
    Runs continuously in daemon mode without blocking the main UI.
    """
    def __init__(self, db_manager: LocalDatabaseManager, supabase_url: str = "", supabase_key: str = "", device_uuid: str = "default_pc"):
        super().__init__(daemon=True)
        self.db_manager = db_manager
        self.supabase_url = supabase_url.strip() or DEFAULT_SUPABASE_URL
        self.supabase_key = supabase_key.strip() or DEFAULT_SUPABASE_KEY
        self.device_uuid = device_uuid
        self.is_running = True
        self._trigger_event = threading.Event()

    def update_credentials(self, url: str, key: str):
        if url and url.strip():
            self.supabase_url = url.strip()
        if key and key.strip():
            self.supabase_key = key.strip()
        self.trigger_immediate_sync()

    def trigger_immediate_sync(self):
        """Wakes up the sync loop immediately on local write for zero data loss."""
        self._trigger_event.set()

    def run(self):
        print(f"[SyncWorker] Background sync thread active for device {self.device_uuid}")
        while self.is_running:
            try:
                target_url = self.supabase_url or DEFAULT_SUPABASE_URL
                target_key = self.supabase_key or DEFAULT_SUPABASE_KEY

                if target_url and target_key:
                    pending_items = self.db_manager.get_pending_sync_items(limit=30)
                    count = len(pending_items)

                    if count > 0:
                        print(f"[SyncWorker] Processing {count} pending cloud sync items...")
                        headers = {
                            "apikey": target_key,
                            "Authorization": f"Bearer {target_key}",
                            "Content-Type": "application/json",
                            "Prefer": "resolution=merge-duplicates,return=minimal"
                        }

                        for item in pending_items:
                            table = item['table_name']
                            action = item['action']
                            payload = json.loads(item['payload'])
                            success = False

                            if action == "UPSERT" and table == "products":
                                url = f"{target_url.rstrip('/')}/rest/v1/products"
                                payload['device_uuid'] = self.device_uuid
                                res = requests.post(url, headers=headers, json=payload, timeout=6)
                                if res.status_code in [200, 201, 204, 409]:
                                    success = True
                                else:
                                    print(f"[SyncWorker] Product sync failed: {res.status_code} {res.text}")

                            elif action == "INSERT_SALE" and table == "sales":
                                sale_url = f"{target_url.rstrip('/')}/rest/v1/sales"
                                sale_payload = payload['sale']
                                sale_payload['device_uuid'] = self.device_uuid
                                sale_res = requests.post(sale_url, headers=headers, json=sale_payload, timeout=6)
                                
                                if sale_res.status_code in [200, 201, 204]:
                                    items_url = f"{target_url.rstrip('/')}/rest/v1/sale_items"
                                    requests.post(items_url, headers=headers, json=payload['items'], timeout=6)
                                    success = True
                                else:
                                    print(f"[SyncWorker] Sale sync failed: {sale_res.status_code} {sale_res.text}")

                            elif action == "INSERT_UDHAAR" and table == "udhaar_ledger":
                                u_url = f"{target_url.rstrip('/')}/rest/v1/udhaar_ledger"
                                payload['device_uuid'] = self.device_uuid
                                res = requests.post(u_url, headers=headers, json=payload, timeout=6)
                                if res.status_code in [200, 201, 204, 409]:
                                    success = True
                                else:
                                    print(f"[SyncWorker] Udhaar sync failed: {res.status_code} {res.text}")

                            if success:
                                self.db_manager.mark_sync_item_completed(item['id'])

            except Exception as e:
                print(f"[SyncWorker] Sync loop exception: {e}")

            # Zero-latency trigger wait: wakes up immediately on write or checks every 3s
            self._trigger_event.wait(timeout=3)
            self._trigger_event.clear()

    def stop(self):
        self.is_running = False
        self._trigger_event.set()
