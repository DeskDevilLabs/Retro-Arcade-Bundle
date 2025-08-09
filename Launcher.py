import tkinter as tk
from PIL import Image, ImageTk
import subprocess
import os
import sys
import pygame
import threading

# Initialize Pygame mixer
pygame.mixer.init()

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    This assumes assets/ is next to the launcher file and games are in the same folder as launcher.
    """
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Sound Functions ---
def play_music():
    try:
        pygame.mixer.music.load(resource_path("assets/arcade_music.mp3"))
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)  # Loop forever
    except Exception as e:
        print(f"Music error: {e}")

def play_click_sound():
    try:
        pygame.mixer.Sound(resource_path("assets/click.wav")).play()
    except:
        pass

def play_hover_sound():
    try:
        pygame.mixer.Sound(resource_path("assets/hover.wav")).play()
    except:
        pass

def play_error_sound():
    try:
        pygame.mixer.Sound(resource_path("assets/error.wav")).play()
    except:
        pass


class RetroArcadeLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("🕹️ CORTEX Retro Arcade Launcher")
        self.root.state('zoomed')
        self.root.attributes("-fullscreen", True)
        self.set_background(resource_path("assets/bg.jpg"))
        tk.Label(root, text="CORTEX RETRO ARCADE", font=("Press Start 2P", 20), fg="#00FF00", bg="black").pack(pady=20)
        self.game_buttons()
        self.add_control_buttons()
        play_music()

    def set_background(self, image_path):
        try:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            bg_img = Image.open(image_path).resize((screen_width, screen_height), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(bg_img)
            tk.Label(self.root, image=self.bg_photo).place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"Background error: {e}")
            self.root.configure(bg='black')

    def add_control_buttons(self):
        control_frame = tk.Frame(self.root, bg="black")
        control_frame.pack(side=tk.BOTTOM, pady=20)
        tk.Button(
            control_frame,
            text="EXIT",
            command=self.exit_app,
            font=("Press Start 2P", 14), fg="white", bg="red",
            activeforeground="white", activebackground="darkred",
            bd=0, padx=20, pady=10, highlightthickness=2, highlightbackground="yellow"
        ).pack(side=tk.LEFT, padx=20)

    def exit_app(self):
        play_click_sound()
        pygame.mixer.music.stop()
        self.root.destroy()

    def game_buttons(self):
        frame = tk.Frame(self.root, bg="#000000")
        frame.pack(pady=40)

        # Games in the same folder as launcher.exe
        games = [
            {"name": "Space Invaders", "img": resource_path("assets/spaceinvaderslogo.jpg"), "exe": resource_path("space_invaders.exe")},
            {"name": "Brick Breaker", "img": resource_path("assets/brickbreakerlogo.jpg"), "exe": resource_path("brick_breaker.exe")},
            {"name": "Snake Rush", "img": resource_path("assets/snake_rush.png"), "exe": resource_path("snake_rush.exe")},
        ]

        for i, game in enumerate(games):
            try:
                btn_frame = tk.Frame(frame, bg="black", width=220, height=220)
                btn_frame.grid(row=i // 2, column=i % 2, padx=30, pady=20)
                btn_frame.pack_propagate(False)

                img = Image.open(game["img"]).resize((200, 200))
                photo = ImageTk.PhotoImage(img)
                bright_photo = ImageTk.PhotoImage(img.point(lambda p: min(int(p * 1.3), 255)))

                border_canvas = tk.Canvas(btn_frame, bg="black", highlightthickness=0, width=210, height=210)
                border_canvas.pack(expand=True)
                border_id = border_canvas.create_rectangle(5, 5, 205, 205, outline="", width=4)

                btn = tk.Button(
                    border_canvas, image=photo, command=lambda exe=game["exe"]: self.launch_game(exe),
                    bd=0, bg="black", activebackground="black", highlightthickness=0, relief='flat'
                )
                btn.image = photo
                btn.bright_image = bright_photo
                btn.border_canvas = border_canvas
                btn.border_id = border_id
                border_canvas.create_window(105, 105, window=btn, width=200, height=200)

                btn.bind("<Enter>", lambda e, b=btn: self.on_hover_enter(b))
                btn.bind("<Leave>", lambda e, b=btn: self.on_hover_leave(b))

            except Exception as e:
                print(f"Error loading {game['name']}: {e}")
                self.show_error(f"Image missing for {game['name']}")

    def on_hover_enter(self, button):
        button.config(image=button.bright_image)
        self.animate_border_glow(button)
        play_hover_sound()

    def on_hover_leave(self, button):
        button.config(image=button.image)
        if hasattr(button, "hover_after_ids"):
            for after_id in button.hover_after_ids:
                button.border_canvas.after_cancel(after_id)
            button.hover_after_ids.clear()
        button.border_canvas.itemconfig(button.border_id, outline="")

    def animate_border_glow(self, button):
        canvas = button.border_canvas
        border_id = button.border_id
        colors = ["#FF0000", "#FF3300", "#FF6600", "#FF9900", "#FFCC00", "#FFFF00"]
        button.hover_after_ids = []
        for i, color in enumerate(colors):
            after_id = canvas.after(i * 50, lambda col=color: canvas.itemconfig(border_id, outline=col))
            button.hover_after_ids.append(after_id)
        final_id = canvas.after(len(colors) * 50, lambda: canvas.itemconfig(border_id, outline="#00FF00"))
        button.hover_after_ids.append(final_id)

    def launch_game(self, exe_path):
        play_click_sound()
        if os.path.exists(exe_path):
            try:
                pygame.mixer.music.stop()
                def run_game():
                    try:
                        subprocess.Popen([exe_path], shell=True)
                    finally:
                        play_music()
                threading.Thread(target=run_game, daemon=True).start()
            except Exception as e:
                play_error_sound()
                self.show_error(f"Error launching {exe_path}: {e}")
        else:
            play_error_sound()
            self.show_error(f"File not found: {exe_path}")

    def show_error(self, message):
        error = tk.Toplevel(self.root)
        error.title("⚠️ Error")
        error.geometry("400x200")
        error.configure(bg='black')
        tk.Label(error, text="Error", font=("Press Start 2P", 16), fg="red", bg="black").pack(pady=10)
        tk.Label(error, text=message, font=("Courier", 10), fg="white", bg="black", wraplength=360).pack(pady=10)
        tk.Button(error, text="CONTINUE", command=error.destroy, font=('Courier', 12),
                  fg='black', bg='#FFD700').pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = RetroArcadeLauncher(root)
    root.mainloop()
