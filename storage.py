import json
import os
from typing import Dict, List, Optional


USERS_FILE = "users.json"
NOTES_FILE = "notes.json"


def _ensure_file_exists(file_path: str, default_data):
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4)


def load_users() -> Dict:
    _ensure_file_exists(USERS_FILE, {})
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users: Dict) -> None:
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)


def load_notes() -> List[Dict]:
    _ensure_file_exists(NOTES_FILE, [])
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_notes(notes: List[Dict]) -> None:
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=4)


def find_user(username: str) -> Optional[Dict]:
    users = load_users()
    return users.get(username)


def add_user(username: str, password_record: Dict) -> bool:
    users = load_users()
    if username in users:
        return False
    users[username] = password_record
    save_users(users)
    return True


def get_notes_by_owner(username: str) -> List[Dict]:
    notes = load_notes()
    return [note for note in notes if note["owner"] == username]


def add_note(note: Dict) -> None:
    notes = load_notes()
    notes.append(note)
    save_notes(notes)


def update_note(note_id: str, username: str, updated_fields: Dict) -> bool:
    notes = load_notes()
    updated = False

    for note in notes:
        if note["id"] == note_id and note["owner"] == username:
            note.update(updated_fields)
            updated = True
            break

    if updated:
        save_notes(notes)
    return updated


def delete_note(note_id: str, username: str) -> bool:
    notes = load_notes()
    original_len = len(notes)
    notes = [note for note in notes if not (note["id"] == note_id and note["owner"] == username)]

    if len(notes) != original_len:
        save_notes(notes)
        return True
    return False


def search_notes(username: str, keyword: str) -> List[Dict]:
    keyword = keyword.lower().strip()
    notes = get_notes_by_owner(username)
    if not keyword:
        return notes

    results = []
    for note in notes:
        if keyword in note["title"].lower() or keyword in note["content"].lower():
            results.append(note)
    return results


def get_note_by_id(note_id: str, username: str) -> Optional[Dict]:
    notes = load_notes()
    for note in notes:
        if note["id"] == note_id and note["owner"] == username:
            return note
    return None
