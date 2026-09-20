import uuid
from datetime import datetime, timezone
from typing import Any, Dict

def create_audit_log(
    inspection_id: str,
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    changes: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Creates an immutable audit log entry representing an action taken by a user.
    """
    return {
        "id": str(uuid.uuid4()),
        "inspection_id": inspection_id,
        "user_id": user_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "changes": changes,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
