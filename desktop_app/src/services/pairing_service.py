import random
import datetime
from typing import Optional, Dict, Any
from ..database.db_manager import LocalDatabaseManager

class DevicePairingService:
    """
    Manages 6-Digit Device Pairing Code Generation and Device Coupling state.
    """
    def __init__(self, db_manager: LocalDatabaseManager):
        self.db_manager = db_manager

    def generate_pair_code(self) -> str:
        """
        Generates a 6-digit numeric OTP code valid for 15 minutes.
        """
        code = f"{random.randint(100000, 999999)}"
        expires_at = (datetime.datetime.now() + datetime.timedelta(minutes=15)).isoformat()
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO device_pairings (pair_code, status, created_at)
                VALUES (?, 'pending', ?)
            """, (code, expires_at))
            conn.commit()

        return code
