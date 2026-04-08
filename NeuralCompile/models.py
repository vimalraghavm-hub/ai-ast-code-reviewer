import reflex as rx
from datetime import datetime
from typing import Optional
from sqlmodel import Field

class DeviceProfile(rx.Model, table=True):
    """Stores unique device fingerprints and metadata."""
    id: Optional[int] = Field(default=None, primary_key=True)
    device_uuid: str = Field(unique=True, index=True)
    user_agent: str = ""
    screen_res: str = ""
    timezone: str = ""
    last_active: datetime = Field(default_factory=datetime.now)
    metadata_json: str = "{}"

class HistoryEntry(rx.Model, table=True):
    """Stores execution and analysis history partitioned by device."""
    id: Optional[int] = Field(default=None, primary_key=True)
    device_uuid: str = Field(index=True, default="")
    title: str = ""
    code: str = ""
    result: str = ""
    language: str = "python"
    category: str = "execution"
    timestamp: datetime = Field(default_factory=datetime.now)
