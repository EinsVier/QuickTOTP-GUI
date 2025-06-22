import json
import os
import sys
import time
import tkinter as tk
from tkinter import messagebox

import keyboard
import pyotp


def load_config():
    """
    Lädt die Konfigurationsdatei und gibt ein Konfigurationsdokument zurück.
    Beendet das Programm mit einer Fehlermeldung, falls die Datei nicht gefunden wird
    oder ungültig ist.
    """
    config_path = "config.json"
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Die Konfigurationsdatei '{config_path}' wurde nicht gefunden."
        )

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Fehler beim Lesen der Konfigurationsdatei: {e}")

    # Überprüfen, ob alle erforderlichen Schlüssel vorhanden sind
    required_keys = ["SECRET", "HOTKEY", "HINT_TEXT"]
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Der Schlüssel '{key}' fehlt in der Konfigurationsdatei.")

    return config


def show_error_and_exit(message: str) -> None:
    """Zeigt eine Fehlermeldung an und beendet das Programm."""
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Fehler", message)
    root.destroy()
    sys.exit(1)


class QuickTOTPApp:
    def __init__(self, root, config):
        self.root = root
        self.config = config

        self.secret = config["SECRET"]
        self.hotkey = config["HOTKEY"]
        self.hint_text = config["HINT_TEXT"].replace("{HOTKEY}", self.hotkey)

        self.totp = pyotp.TOTP(self.secret)

        self.create_widgets()
        self.update_totp()

        # Registriere den Hotkey
        try:
            keyboard.add_hotkey(self.hotkey, self.insert_totp_code)
        except Exception as e:
            messagebox.showerror(
                "Fehler",
                f"Der Hotkey '{self.hotkey}' konnte nicht registriert werden.\n{e}",
            )

    def create_widgets(self):
        """Erstellt die GUI-Elemente."""
        self.root.title("QuickTOTP")
        self.root.geometry("300x200")
        self.root.resizable(False, False)

        self.frame = tk.Frame(self.root)
        self.frame.pack(expand=True)

        self.code_label = tk.Label(self.frame, text="", font=("Helvetica", 24), pady=10)
        self.code_label.pack()

        self.countdown_label = tk.Label(self.frame, text="", font=("Helvetica", 14))
        self.countdown_label.pack()

        self.hint_label = tk.Label(
            self.frame,
            text=self.hint_text,
            font=("Helvetica", 10),
            wraplength=280,
            justify="center",
            pady=10,
        )
        self.hint_label.pack()

    def update_totp(self):
        """Aktualisiert den TOTP-Code und den Countdown."""
        current_code = self.totp.now()
        time_remaining = self.totp.interval - int(time.time()) % self.totp.interval

        # Aktualisiere den Code
        self.code_label.config(text=current_code)

        # Ändere die Farbe basierend auf der verbleibenden Zeit
        if time_remaining > 7:
            self.code_label.config(fg="green")
        else:
            self.code_label.config(fg="yellow")

        # Aktualisiere den Countdown
        self.countdown_label.config(text=f"Verbleibende Zeit: {time_remaining}s")

        # Plane die nächste Aktualisierung
        self.root.after(1000, self.update_totp)

    def insert_totp_code(self):
        """Fügt den aktuellen TOTP-Code in die aktive Anwendung ein."""
        current_code = self.totp.now()
        keyboard.write(current_code)

    def on_closing(self):
        """Bereinigt Ressourcen beim Schließen der Anwendung."""
        keyboard.remove_hotkey(self.hotkey)
        self.root.destroy()


def main():
    try:
        config = load_config()
    except Exception as e:
        # Zeige eine Fehlermeldung an und beende das Programm
        show_error_and_exit(str(e))

    root = tk.Tk()
    app = QuickTOTPApp(root, config)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
