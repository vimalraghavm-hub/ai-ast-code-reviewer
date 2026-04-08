import reflex as rx
import uuid
import json
from .models import DeviceProfile, HistoryEntry
from datetime import datetime

class DeviceState(rx.State):
    """
    Handles device identification via a persistent cookie.
    Ensures zero-latency identification and session isolation across reloads.
    """
    device_id: str = rx.Cookie("", name="nc_device_id", max_age=31536000)  # 1 year
    is_identified: bool = False

    @rx.var
    def safe_uuid(self) -> str:
        """Returns the persistent device ID, or session token as ultimate fallback."""
        if self.device_id:
            return self.device_id
        return self.router.session.client_token

    def check_or_create_id(self):
        """Called on page load. Ensures a UUID cookie exists and updates the DB."""
        if not self.device_id:
            new_id = str(uuid.uuid4())
            self.device_id = new_id
            self.is_identified = True
            
            with rx.session() as session:
                session.add(DeviceProfile(
                    device_uuid=new_id,
                    user_agent="Cookie-based ID",
                    screen_res="Unknown",
                    timezone="Unknown",
                    metadata_json=json.dumps({"method": "cookie", "generated": True}),
                ))
                session.commit()
        else:
            self.is_identified = True
            with rx.session() as session:
                device = session.query(DeviceProfile).filter(DeviceProfile.device_uuid == self.device_id).first()
                if device:
                    device.last_active = datetime.now()
                    session.commit()

def fingerprint_logic():
    """Returns an empty fragment since we rely on `on_load` events now."""
    return rx.fragment()
