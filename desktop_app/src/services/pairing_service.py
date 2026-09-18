import random
import datetime
import uuid
import hashlib
import requests
from typing import Optional, Dict, Any
from ..database.db_manager import LocalDatabaseManager

class DevicePairingService:
    """
    Manages 6-Digit Device Pairing Code Generation, Hardware Machine Binding,
    and Cloud-Coupled Verification.
    """
    def __init__(self, db_manager: LocalDatabaseManager):
        self.db_manager = db_manager
        self._device_uuid = self._compute_device_uuid()

    def _compute_device_uuid(self) -> str:
        """
        Derives a persistent, immutable hardware machine fingerprint.
        """
        node = uuid.getnode()
        return 'pc_' + hashlib.sha256(str(node).encode()).hexdigest()[:16]

    @property
    def device_uuid(self) -> str:
        return self._device_uuid

    def generate_pair_code(self) -> str:
        """
        Generates a 6-digit numeric OTP code valid for 15 minutes,
        records it locally and immediately pushes to Supabase cloud.
        """
        code = f"{random.randint(100000, 999999)}"
        now = datetime.datetime.now()
        now_iso = now.isoformat()
        expires_at = (now + datetime.timedelta(minutes=15)).isoformat()
        
        # 1. Local SQLite record
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO device_pairings (pair_code, status, created_at)
                VALUES (?, 'pending', ?)
            """, (code, expires_at))
            conn.commit()

        # 2. Cloud Supabase record (with device_uuid binding)
        try:
            settings = self.db_manager.get_shop_settings()
            s_url = settings.get('supabase_url', '').strip()
            s_key = settings.get('supabase_key', '').strip()

            if s_url and s_key:
                headers = {
                    "apikey": s_key,
                    "Authorization": f"Bearer {s_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                }
                payload = {
                    "pair_code": code,
                    "device_uuid": self._device_uuid,
                    "device_name": settings.get('shop_name', 'E-Store POS Desktop'),
                    "status": "pending",
                    "expires_at": expires_at,
                    "created_at": now_iso
                }
                # Upsert into cloud device_pairings
                requests.post(f"{s_url}/rest/v1/device_pairings", headers=headers, json=payload, timeout=4)
        except Exception:
            pass

        return code
