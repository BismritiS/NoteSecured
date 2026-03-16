import json
import os
import socket
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from security import build_signature, current_timestamp, generate_request_id

HOST = "127.0.0.1"
PORT = 5001


class NoteSecuredApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NoteSecured")
        self.root.geometry("1000x650")
        self.root.configure(bg="#0f172a")

        self.current_user = None
        self.selected_note_id = None
        self.notes_cache = []

        self.build_login_screen()

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def send_request(self, action, payload):
        request = {
            "action": action,
            "timestamp": current_timestamp(),
            "request_id": generate_request_id(),
            "payload": payload,
        }

        signature_payload = {
            "action": request["action"],
            "timestamp": request["timestamp"],
            "request_id": request["request_id"],
            "payload": request["payload"],
        }
        request["signature"] = build_signature(signature_payload)

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((HOST, PORT))
            client.send(json.dumps(request).encode("utf-8"))
            response = client.recv(65536).decode("utf-8")
            client.close()
            return json.loads(response)
        except ConnectionRefusedError:
            return {"success": False, "message": "Could not connect to server. Start server.py first.", "data": {}}
        except Exception as e:
            return {"success": False, "message": str(e), "data": {}}

    def build_login_screen(self):
        self.clear_root()

        frame = tk.Frame(self.root, bg="#0f172a")
        frame.pack(expand=True)

        tk.Label(
            frame, text="NoteSecured",
            font=("Segoe UI", 24, "bold"),
            fg="white", bg="#0f172a"
        ).pack(pady=10)

        tk.Label(frame, text="Username", fg="white", bg="#0f172a").pack()
        self.username_entry = tk.Entry(frame, width=30)
        self.username_entry.pack(pady=5)

        tk.Label(frame, text="Password", fg="white", bg="#0f172a").pack()
        self.password_entry = tk.Entry(frame, width=30, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(frame, text="Login", width=20, command=self.login_user).pack(pady=10)
        tk.Button(frame, text="Register", width=20, command=self.register_user).pack(pady=5)

    def register_user(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        response = self.send_request("register", {
            "username": username,
            "password": password
        })
        messagebox.showinfo("Register", response["message"])

    def login_user(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        response = self.send_request("login", {
            "username": username,
            "password": password
        })

        if response["success"]:
            self.current_user = username
            self.build_main_screen()
            self.refresh_notes()
        else:
            messagebox.showerror("Login Failed", response["message"])

    def build_main_screen(self):
        self.clear_root()

        top_frame = tk.Frame(self.root, bg="#1e293b", height=50)
        top_frame.pack(fill="x")

        tk.Label(
            top_frame,
            text=f"Welcome, {self.current_user}",
            font=("Segoe UI", 14, "bold"),
            bg="#1e293b",
            fg="white"
        ).pack(side="left", padx=15, pady=10)

        tk.Button(top_frame, text="Logout", command=self.logout_user).pack(side="right", padx=10, pady=10)
        tk.Button(top_frame, text="Refresh", command=self.refresh_notes).pack(side="right", padx=10, pady=10)

        main_frame = tk.Frame(self.root, bg="#0f172a")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = tk.Frame(main_frame, bg="#111827")
        left_frame.pack(side="left", fill="y", padx=(0, 10))

        tk.Label(left_frame, text="Search", bg="#111827", fg="white").pack(pady=(10, 2))
        self.search_entry = tk.Entry(left_frame, width=30)
        self.search_entry.pack(padx=10)
        tk.Button(left_frame, text="Search Notes", command=self.refresh_notes).pack(pady=8)

        self.notes_listbox = tk.Listbox(left_frame, width=40, height=25)
        self.notes_listbox.pack(padx=10, pady=10)
        self.notes_listbox.bind("<<ListboxSelect>>", self.on_note_select)

        tk.Button(left_frame, text="New Note", width=25, command=self.clear_note_fields).pack(pady=3)
        tk.Button(left_frame, text="Delete Note", width=25, command=self.delete_note).pack(pady=3)
        tk.Button(left_frame, text="Pin/Unpin", width=25, command=self.toggle_pin).pack(pady=3)
        tk.Button(left_frame, text="Lock Note", width=25, command=self.lock_note).pack(pady=3)
        tk.Button(left_frame, text="Unlock Note", width=25, command=self.unlock_note).pack(pady=3)
        tk.Button(left_frame, text="Export Note", width=25, command=self.export_note).pack(pady=3)

        right_frame = tk.Frame(main_frame, bg="#0f172a")
        right_frame.pack(side="right", fill="both", expand=True)

        tk.Label(right_frame, text="Title", bg="#0f172a", fg="white").pack(anchor="w")
        self.title_entry = tk.Entry(right_frame, font=("Segoe UI", 12))
        self.title_entry.pack(fill="x", pady=(0, 10))

        tk.Label(right_frame, text="Content", bg="#0f172a", fg="white").pack(anchor="w")
        self.content_text = tk.Text(right_frame, wrap="word", font=("Segoe UI", 11), height=20)
        self.content_text.pack(fill="both", expand=True)

        self.status_label = tk.Label(right_frame, text="Ready", bg="#0f172a", fg="#cbd5e1")
        self.status_label.pack(anchor="w", pady=8)

        button_frame = tk.Frame(right_frame, bg="#0f172a")
        button_frame.pack(fill="x")

        tk.Button(button_frame, text="Save Note", width=16, command=self.save_note).pack(side="left", padx=5)
        tk.Button(button_frame, text="Update Note", width=16, command=self.update_note).pack(side="left", padx=5)
        tk.Button(button_frame, text="Clear", width=16, command=self.clear_note_fields).pack(side="left", padx=5)

    def logout_user(self):
        self.current_user = None
        self.selected_note_id = None
        self.notes_cache = []
        self.build_login_screen()

    def refresh_notes(self):
        keyword = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""

        response = self.send_request("get_notes", {
            "username": self.current_user,
            "keyword": keyword
        })

        if response["success"]:
            self.notes_cache = response["data"]
            self.notes_listbox.delete(0, tk.END)

            for note in self.notes_cache:
                pin_marker = "📌 " if note["pinned"] else ""
                lock_marker = f"🔒({note['locked_by']}) " if note["locked"] else ""
                self.notes_listbox.insert(
                    tk.END,
                    f"{pin_marker}{lock_marker}{note['title']} | {note['modified_at']}"
                )
            self.status_label.config(text=response["message"])
        else:
            messagebox.showerror("Error", response["message"])

    def on_note_select(self, event):
        selection = self.notes_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        note = self.notes_cache[index]
        self.selected_note_id = note["id"]

        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, note["title"])

        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", note["content"])

        self.status_label.config(
            text=f"Selected note | Created: {note['created_at']} | Modified: {note['modified_at']}"
        )

    def clear_note_fields(self):
        self.selected_note_id = None
        self.title_entry.delete(0, tk.END)
        self.content_text.delete("1.0", tk.END)
        self.status_label.config(text="New note mode")

    def save_note(self):
        title = self.title_entry.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()

        response = self.send_request("create_note", {
            "username": self.current_user,
            "title": title,
            "content": content
        })

        if response["success"]:
            messagebox.showinfo("Success", response["message"])
            self.clear_note_fields()
            self.refresh_notes()
        else:
            messagebox.showerror("Error", response["message"])

    def update_note(self):
        if not self.selected_note_id:
            messagebox.showwarning("Warning", "Select a note first.")
            return

        title = self.title_entry.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()

        response = self.send_request("update_note", {
            "username": self.current_user,
            "note_id": self.selected_note_id,
            "title": title,
            "content": content
        })

        if response["success"]:
            messagebox.showinfo("Updated", response["message"])
            self.refresh_notes()
        else:
            messagebox.showerror("Error", response["message"])

    def delete_note(self):
        if not self.selected_note_id:
            messagebox.showwarning("Warning", "Select a note first.")
            return

        response = self.send_request("delete_note", {
            "username": self.current_user,
            "note_id": self.selected_note_id
        })

        if response["success"]:
            messagebox.showinfo("Deleted", response["message"])
            self.clear_note_fields()
            self.refresh_notes()
        else:
            messagebox.showerror("Error", response["message"])

    def toggle_pin(self):
        if not self.selected_note_id:
            messagebox.showwarning("Warning", "Select a note first.")
            return

        response = self.send_request("toggle_pin", {
            "username": self.current_user,
            "note_id": self.selected_note_id
        })

        if response["success"]:
            self.refresh_notes()
        else:
            messagebox.showerror("Error", response["message"])

    def lock_note(self):
        if not self.selected_note_id:
            messagebox.showwarning("Warning", "Select a note first.")
            return

        response = self.send_request("lock_note", {
            "username": self.current_user,
            "note_id": self.selected_note_id
        })

        if response["success"]:
            messagebox.showinfo("Locked", response["message"])
            self.refresh_notes()
        else:
            messagebox.showerror("Error", response["message"])

    def unlock_note(self):
        if not self.selected_note_id:
            messagebox.showwarning("Warning", "Select a note first.")
            return

        response = self.send_request("unlock_note", {
            "username": self.current_user,
            "note_id": self.selected_note_id
        })

        if response["success"]:
            messagebox.showinfo("Unlocked", response["message"])
            self.refresh_notes()
        else:
            messagebox.showerror("Error", response["message"])

    def export_note(self):
        if not self.selected_note_id:
            messagebox.showwarning("Warning", "Select a note first.")
            return

        note = None
        for n in self.notes_cache:
            if n["id"] == self.selected_note_id:
                note = n
                break

        if not note:
            messagebox.showerror("Error", "Note not found.")
            return

        os.makedirs("exports", exist_ok=True)
        default_name = f"{note['title'].replace(' ', '_')}.txt"

        file_path = filedialog.asksaveasfilename(
            initialdir="exports",
            initialfile=default_name,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")]
        )

        if not file_path:
            return

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Title: {note['title']}\n")
            f.write(f"Created: {note['created_at']}\n")
            f.write(f"Modified: {note['modified_at']}\n")
            f.write(f"Pinned: {note['pinned']}\n")
            f.write(f"Locked: {note['locked']}\n")
            f.write("\nContent:\n")
            f.write(note["content"])

        messagebox.showinfo("Export", "Note exported successfully.")


if __name__ == "__main__":
    root = tk.Tk()
    app = NoteSecuredApp(root)
    root.mainloop()