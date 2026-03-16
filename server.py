import json
import socket
import threading
import uuid
from datetime import datetime

from auth import create_password_record, verify_password
from storage import (
    add_note,
    add_user,
    delete_note,
    find_user,
    get_note_by_id,
    get_notes_by_owner,
    search_notes,
    update_note,
)
from security import build_signature, validate_request_id, validate_timestamp

HOST = "127.0.0.1"
PORT = 5001


def make_response(success: bool, message: str, data=None) -> dict:
    return {
        "success": success,
        "message": message,
        "data": data if data is not None else {}
    }


def verify_request(request: dict) -> tuple[bool, str]:
    required_keys = {"action", "timestamp", "request_id", "signature", "payload"}
    if not required_keys.issubset(request.keys()):
        return False, "Malformed request."

    signature = request["signature"]
    payload_for_signature = {
        "action": request["action"],
        "timestamp": request["timestamp"],
        "request_id": request["request_id"],
        "payload": request["payload"],
    }

    expected_signature = build_signature(payload_for_signature)
    if signature != expected_signature:
        return False, "Request integrity check failed."

    if not validate_timestamp(request["timestamp"]):
        return False, "Expired or invalid timestamp."

    if not validate_request_id(request["request_id"]):
        return False, "Replay attack detected: duplicate request."

    return True, "Valid request."


def handle_register(payload: dict) -> dict:
    username = payload.get("username", "").strip()
    password = payload.get("password", "").strip()

    if not username or not password:
        return make_response(False, "Username and password are required.")

    if len(password) < 6:
        return make_response(False, "Password should be at least 6 characters long.")

    password_record = create_password_record(password)
    created = add_user(username, password_record)

    if not created:
        return make_response(False, "Username already exists.")

    return make_response(True, "Registration successful.")


def handle_login(payload: dict) -> dict:
    username = payload.get("username", "").strip()
    password = payload.get("password", "").strip()

    user = find_user(username)
    if not user:
        return make_response(False, "User not found.")

    if not verify_password(password, user["salt"], user["password_hash"]):
        return make_response(False, "Invalid credentials.")

    return make_response(True, "Login successful.")


def handle_create_note(payload: dict) -> dict:
    username = payload.get("username", "").strip()
    title = payload.get("title", "").strip()
    content = payload.get("content", "").strip()

    if not username or not title or not content:
        return make_response(False, "Username, title, and content are required.")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    note = {
        "id": str(uuid.uuid4()),
        "owner": username,
        "title": title,
        "content": content,
        "pinned": False,
        "locked": False,
        "locked_by": "",
        "created_at": now,
        "modified_at": now,
    }

    add_note(note)
    return make_response(True, "Note created successfully.", note)


def handle_get_notes(payload: dict) -> dict:
    username = payload.get("username", "").strip()
    keyword = payload.get("keyword", "").strip()

    if keyword:
        notes = search_notes(username, keyword)
    else:
        notes = get_notes_by_owner(username)

    notes = sorted(notes, key=lambda n: (not n["pinned"], n["modified_at"]), reverse=False)
    return make_response(True, "Notes fetched successfully.", notes)


def handle_update_note(payload: dict) -> dict:
    username = payload.get("username", "").strip()
    note_id = payload.get("note_id", "").strip()
    title = payload.get("title", "").strip()
    content = payload.get("content", "").strip()

    note = get_note_by_id(note_id, username)
    if not note:
        return make_response(False, "Note not found.")

    if note["locked"] and note["locked_by"] != username:
        return make_response(False, "Note is locked by another user.")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updated = update_note(note_id, username, {
        "title": title or note["title"],
        "content": content or note["content"],
        "modified_at": now,
        "locked": False,
        "locked_by": ""
    })

    if not updated:
        return make_response(False, "Failed to update note.")

    return make_response(True, "Note updated successfully.")


def handle_delete_note(payload: dict) -> dict:
    username = payload.get("username", "").strip()
    note_id = payload.get("note_id", "").strip()

    note = get_note_by_id(note_id, username)
    if not note:
        return make_response(False, "Note not found.")

    if note["locked"] and note["locked_by"] != username:
        return make_response(False, "Cannot delete. Note is locked by another user.")

    deleted = delete_note(note_id, username)
    if not deleted:
        return make_response(False, "Failed to delete note.")

    return make_response(True, "Note deleted successfully.")


def handle_toggle_pin(payload: dict) -> dict:
    username = payload.get("username", "").strip()
    note_id = payload.get("note_id", "").strip()

    note = get_note_by_id(note_id, username)
    if not note:
        return make_response(False, "Note not found.")

    updated = update_note(note_id, username, {
        "pinned": not note["pinned"],
        "modified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    if not updated:
        return make_response(False, "Could not update pin status.")

    return make_response(True, "Pin status updated.")


def handle_lock_note(payload: dict) -> dict:
    username = payload.get("username", "").strip()
    note_id = payload.get("note_id", "").strip()

    note = get_note_by_id(note_id, username)
    if not note:
        return make_response(False, "Note not found.")

    if note["locked"] and note["locked_by"] != username:
        return make_response(False, f"Note already locked by {note['locked_by']}.")

    updated = update_note(note_id, username, {
        "locked": True,
        "locked_by": username
    })

    if not updated:
        return make_response(False, "Failed to lock note.")

    return make_response(True, "Note locked for editing.")


def handle_unlock_note(payload: dict) -> dict:
    username = payload.get("username", "").strip()
    note_id = payload.get("note_id", "").strip()

    note = get_note_by_id(note_id, username)
    if not note:
        return make_response(False, "Note not found.")

    if note["locked_by"] != username:
        return make_response(False, "Only the locking user can unlock this note.")

    updated = update_note(note_id, username, {
        "locked": False,
        "locked_by": ""
    })

    if not updated:
        return make_response(False, "Failed to unlock note.")

    return make_response(True, "Note unlocked.")


ACTION_MAP = {
    "register": handle_register,
    "login": handle_login,
    "create_note": handle_create_note,
    "get_notes": handle_get_notes,
    "update_note": handle_update_note,
    "delete_note": handle_delete_note,
    "toggle_pin": handle_toggle_pin,
    "lock_note": handle_lock_note,
    "unlock_note": handle_unlock_note,
}


def process_request(request: dict) -> dict:
    is_valid, validation_message = verify_request(request)
    if not is_valid:
        return make_response(False, validation_message)

    action = request["action"]
    payload = request["payload"]

    handler = ACTION_MAP.get(action)
    if not handler:
        return make_response(False, "Unknown action.")

    return handler(payload)


def handle_client(client_socket: socket.socket):
    try:
        data = client_socket.recv(65536).decode("utf-8")
        request = json.loads(data)
        response = process_request(request)
    except json.JSONDecodeError:
        response = make_response(False, "Invalid JSON data received.")
    except Exception as e:
        response = make_response(False, f"Server error: {str(e)}")

    client_socket.send(json.dumps(response).encode("utf-8"))
    client_socket.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"NoteSecured server running on {HOST}:{PORT}")

    while True:
        client_socket, address = server.accept()
        print(f"Connection from {address}")
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.daemon = True
        thread.start()


if __name__ == "__main__":
    start_server()