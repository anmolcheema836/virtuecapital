import tkinter as tk
from tkinter import messagebox
import threading
import time
import json
import os
import sys
from datetime import datetime
from pynput import mouse, keyboard
import pystray
from PIL import Image, ImageDraw

# Windows-specific sound library
if sys.platform == "win32":
    import winsound

# --- Configuration ---
CONFIG_FILE = "eye_care_config.json"
DEFAULT_CONFIG = {
    "work_duration": 20,    # minutes (Can be 0.1 for 6-second testing)
    "break_duration": 20,   # seconds
    "activity_timeout": 5   # minutes
}

EYE_TIPS = [
    "Blink your eyes rapidly for a few seconds.",
    "Roll your eyes slowly in a circle.",
    "Look at a distant object and focus on it.",
    "Sit up straight and relax your shoulders.",
    "Take a deep breath and hydrate.",
    "Rub your palms together and place them over your eyes."
]

class EyeCareApp:
    def __init__(self):
        self.config = DEFAULT_CONFIG
        self.paused = False
        self.last_activity = datetime.now()
        self.root = tk.Tk()
        self.root.withdraw()  
        self.overlay = None
        
        # Activity Listeners
        self.mouse_listener = mouse.Listener(on_move=self.reset_activity)
        self.kb_listener = keyboard.Listener(on_press=self.reset_activity)
        self.mouse_listener.start()
        self.kb_listener.start()

        # Start background timer
        self.timer_thread = threading.Thread(target=self.run_timer_loop, daemon=True)
        self.timer_thread.start()

    def play_chime(self, frequency=440, duration=500):
        if sys.platform == "win32":
            try:
                winsound.Beep(frequency, duration)
            except Exception:
                pass
        else:
            try:
                self.root.bell()
            except Exception:
                pass

    def reset_activity(self, *args):
        self.last_activity = datetime.now()

    def is_user_idle(self):
        idle_time = (datetime.now() - self.last_activity).total_seconds() / 60
        return idle_time > self.config["activity_timeout"]

    def run_timer_loop(self):
        """Background thread that manages the wait cycle."""
        while True:
            # FIXED: Using time.sleep directly on the calculated seconds.
            # This handles floats (like 0.1) perfectly.
            wait_seconds = float(self.config["work_duration"]) * 60
            time.sleep(wait_seconds)
            
            # Only trigger if not paused and user is active
            if not self.paused and not self.is_user_idle():
                self.root.after(0, self.show_overlay)

    def emergency_stop(self, event=None):
        """Forcefully kills the entire application."""
        if hasattr(self, 'icon'):
            self.icon.stop()
        self.root.destroy()
        sys.exit(0)

    def show_overlay(self):
        if self.overlay: return

        self.play_chime(600, 300)
        self.overlay = tk.Toplevel(self.root)
        self.overlay.attributes("-fullscreen", True)
        self.overlay.attributes("-topmost", True)
        self.overlay.configure(bg="#1a1a1a")
        
        # Binding: Ctrl + F4 will kill the app completely
        self.overlay.bind("<Control-F4>", self.emergency_stop)
        self.overlay.protocol("WM_DELETE_WINDOW", lambda: None)

        content = tk.Frame(self.overlay, bg="#1a1a1a")
        content.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(content, text="EYE REST PERIOD", fg="#4a90e2", bg="#1a1a1a", 
                 font=("Segoe UI", 30, "bold")).pack()
        
        tk.Label(content, text="Look 20 feet away for 20 seconds", fg="white", bg="#1a1a1a", 
                 font=("Segoe UI", 16)).pack(pady=10)

        self.timer_var = tk.StringVar(value=str(int(self.config["break_duration"])))
        tk.Label(content, textvariable=self.timer_var, fg="#e74c3c", bg="#1a1a1a", 
                 font=("Consolas", 80, "bold")).pack()

        tip = EYE_TIPS[int(time.time()) % len(EYE_TIPS)]
        tk.Label(content, text=f"Health Tip: {tip}", fg="#aaaaaa", bg="#1a1a1a", 
                 font=("Segoe UI", 12, "italic")).pack(pady=20)

        # Skip Button
        skip_btn = tk.Button(
            content, text="Skip Break", command=self.close_overlay,
            bg="#333333", fg="#dddddd", activebackground="#444444", 
            activeforeground="white", bd=0, padx=20, pady=10,
            font=("Segoe UI", 10, "bold"), cursor="hand2"
        )
        skip_btn.pack(pady=10)

        tk.Label(content, text="Press Ctrl+F4 to completely close app", 
                 fg="#444444", bg="#1a1a1a", font=("Segoe UI", 9)).pack(pady=10)

        self.overlay.focus_force()
        self.countdown(int(self.config["break_duration"]))

    def countdown(self, seconds):
        if self.overlay and seconds > 0:
            self.timer_var.set(str(seconds))
            self.root.after(1000, lambda: self.countdown(seconds - 1))
        elif self.overlay:
            self.close_overlay()

    def close_overlay(self):
        if self.overlay:
            self.play_chime(400, 200)
            self.overlay.destroy()
            self.overlay = None

    def create_tray(self):
        image = Image.new('RGB', (64, 64), color=(74, 144, 226))
        d = ImageDraw.Draw(image)
        d.rectangle([16, 16, 48, 48], fill=(255, 255, 255))

        menu_items = [
            pystray.MenuItem("Pause Reminders", self.toggle_pause, checked=lambda item: self.paused),
            pystray.MenuItem("Exit Completely", self.emergency_stop)
        ]
        
        self.icon = pystray.Icon("EyeCare", image, "Eye Care Assistant", menu=pystray.Menu(*menu_items))
        self.icon.run_detached()

    def toggle_pause(self, icon, item):
        self.paused = not self.paused

    def run(self):
        self.create_tray()
        self.root.mainloop()

if __name__ == "__main__":
    app = EyeCareApp()
    app.run()