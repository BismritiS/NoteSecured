import hashlib
import json
import time
import uuid
from typing import Dict


USED_REQUEST_IDS = set()
MAX_TIME_DRIFT_SECONDS = 60


def generate_request_id() -> str:
    return str(uuid.uuid4())


def current_timestamp() -> int:
    return int(time.time())


def build_signature(payload: Dict, secret: str = "NoteSecuredSecret") -> str:
    payload_copy = dict(payload)
    payload_string = json.dumps(payload_copy, sort_keys=True)
    return hashlib.sha256((payload_string + secret).encode("utf-8")).hexdigest()


def validate_timestamp(timestamp: int) -> bool:
    now = current_timestamp()
    return abs(now - timestamp) <= MAX_TIME_DRIFT_SECONDS


def validate_request_id(request_id: str) -> bool:
    if request_id in USED_REQUEST_IDS:
        return False
    USED_REQUEST_IDS.add(request_id)
    return True
