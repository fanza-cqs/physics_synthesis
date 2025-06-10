# Create: src/utils/status_constants.py
"""
Status constants for the Physics Literature Synthesis Pipeline
Centralizes all status strings to avoid magic strings throughout the codebase
"""

from enum import Enum
from typing import Dict, Any


class ZoteroStatus(Enum):
    """Enumeration of possible Zotero connection states"""
    CONNECTED = "connected"
    NOT_CONFIGURED = "not_configured"
    FAILED = "failed"
    UNKNOWN = "unknown"
    CONNECTING = "connecting"


class ComponentStatus(Enum):
    """General component status states"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    LOADING = "loading"


# Display strings for UI components
ZOTERO_DISPLAY_STRINGS = {
    ZoteroStatus.CONNECTED: "✅ Connected",
    ZoteroStatus.NOT_CONFIGURED: "⚙️ Not configured", 
    ZoteroStatus.FAILED: "❌ Failed",
    ZoteroStatus.UNKNOWN: "❓ Unknown",
    ZoteroStatus.CONNECTING: "🔄 Connecting...",
}

ANTHROPIC_DISPLAY_STRINGS = {
    ComponentStatus.AVAILABLE: "✅ Available",
    ComponentStatus.UNAVAILABLE: "❌ Not configured",
    ComponentStatus.ERROR: "❌ Error",
    ComponentStatus.LOADING: "🔄 Testing...",
}


def get_zotero_display_string(status: ZoteroStatus) -> str:
    """Get the display string for a Zotero status"""
    return ZOTERO_DISPLAY_STRINGS.get(status, "❓ Unknown")


def parse_zotero_status(status_string: str) -> ZoteroStatus:
    """Parse a status string into a ZoteroStatus enum"""
    if not status_string:
        return ZoteroStatus.UNKNOWN
    
    status_lower = str(status_string).lower()
    
    if "connected" in status_lower or "✅" in status_string:
        return ZoteroStatus.CONNECTED
    elif "not_configured" in status_lower or "not configured" in status_lower:
        return ZoteroStatus.NOT_CONFIGURED
    elif "failed" in status_lower or "❌" in status_string:
        return ZoteroStatus.FAILED
    elif "connecting" in status_lower or "🔄" in status_string:
        return ZoteroStatus.CONNECTING
    else:
        return ZoteroStatus.UNKNOWN


def is_zotero_working(status: ZoteroStatus, manager_available: bool = True) -> bool:
    """Check if Zotero is in a working state"""
    return status == ZoteroStatus.CONNECTED and manager_available


# Status checker functions
def check_zotero_status(session_state: Dict[str, Any]) -> tuple[ZoteroStatus, str]:
    """
    Check Zotero status from session state
    
    Returns:
        tuple: (ZoteroStatus enum, display_string)
    """
    zotero_status_raw = session_state.get('zotero_status', 'unknown')
    zotero_manager = session_state.get('zotero_manager')
    
    # Parse the raw status
    status = parse_zotero_status(zotero_status_raw)
    
    # Double-check with manager availability
    if status == ZoteroStatus.CONNECTED and zotero_manager is None:
        status = ZoteroStatus.FAILED
    
    # Generate display string
    display_string = get_zotero_display_string(status)
    
    # Add collection count if connected
    if status == ZoteroStatus.CONNECTED:
        collections = session_state.get('zotero_collections', [])
        if collections:
            display_string += f" ({len(collections)})"
    
    return status, display_string


def set_zotero_status(session_state: Dict[str, Any], status: ZoteroStatus, error_msg: str = None):
    """
    Set Zotero status in session state using proper constants
    
    Args:
        session_state: Streamlit session state
        status: ZoteroStatus enum value
        error_msg: Optional error message for failed status
    """
    if status == ZoteroStatus.FAILED and error_msg:
        session_state['zotero_status'] = f"{get_zotero_display_string(status)}: {error_msg}"
    else:
        session_state['zotero_status'] = get_zotero_display_string(status)