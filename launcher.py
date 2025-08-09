import tkinter as tk
from PIL import Image, ImageTk
import subprocess
import os
import sys
import pygame
import threading

# Initialize Pygame mixer
pygame.mixer.init()

# --- Sound Functions ---
def play_music():
    try:
        pygame.mixer.music.load("assets/arcade_music.mp3")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)  # Loop forever
    except Exception as e:
        print(f"Music error: {e}")

def play_click_sound():
    try:
        pygame.mixer.Sound("assets/click.wav").play()
    except:
        pass

def play_hover_sound():
    try:
        pygame.mixer.Sound("assets/hover.wav").play()
    except:
        pass

def play_error_sound():
    try:
        pygame.mixer.Sound("assets/error.wav").play()
    except:
        pass


class RetroArcadeLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("🕹️ CORTEX Retro Arcade Launcher")
        self.root.state('zoomed')  # Maximize window (Windows)
        self.root.attributes("-fullscreen", True)
        self.set_background("assets/bg.jpg")
        tk.Label(root, text="CORTEX RETRO ARCADE", font=("Press Start 2P", 20), fg="#00FF00", bg="black").pack(pady=20)
        self.game_buttons()
        self.add_control_buttons()
        play_music()

    def set_background(self, image_path):
        try:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            bg_img = Image.open(image_path).resize((screen_width, screen_height), Image.ANTIALIAS)
            self.bg_photo = ImageTk.PhotoImage(bg_img)
            tk.Label(self.root, image=self.bg_photo).place(x=0, y=0, relwidth=1, relheight=1)
        except:
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

    def return_to_holo_mat(self):
        play_click_sound()
        print("Returning to Holo Mat...")

    def exit_app(self):
        play_click_sound()
        pygame.mixer.music.stop()
        self.root.destroy()

    def game_buttons(self):
        frame = tk.Frame(self.root, bg="#000000")
        frame.pack(pady=40)

        # Path to launcher folder
        base_dir = os.path.dirname(os.path.abspath(__file__))

        games = [
            {"name": "Space Invaders", "img": "assets/spaceinvaderslogo.jpg", "py": os.path.join(base_dir, "Space-Invaders", "space_invaders.py")},
            {"name": "Brick Breaker", "img": "assets/brickbreakerlogo.jpg", "py": os.path.join(base_dir, "Brick-Breaker", "brick_breaker.py")},
            {"name": "Snake Rush", "img": "assets/snake_rush.png", "py": os.path.join(base_dir, "Snake-Rush", "snake_rush.py")},
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
                
                btn = tk.Button(border_canvas, image=photo, command=lambda py=game["py"]: self.launch_game(py),
                                bd=0, bg="black", activebackground="black", highlightthickness=0, relief='flat')
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
        # Cancel any running animation
        if hasattr(button, "hover_after_ids"):
            for after_id in button.hover_after_ids:
                button.border_canvas.after_cancel(after_id)
            button.hover_after_ids.clear()
        button.border_canvas.itemconfig(button.border_id, outline="")

    def animate_border_glow(self, button):
        canvas = button.border_canvas
        border_id = button.border_id
        colors = ["#FF0000", "#FF3300", "#FF6600", "#FF9900", "#FFCC00", "#FFFF00"]

        button.hover_after_ids = []  # Store all scheduled IDs so they can be canceled

        for i, color in enumerate(colors):
            after_id = canvas.after(i * 50, lambda col=color: canvas.itemconfig(border_id, outline=col))
            button.hover_after_ids.append(after_id)

        final_id = canvas.after(len(colors) * 50, lambda: canvas.itemconfig(border_id, outline="#00FF00"))
        button.hover_after_ids.append(final_id)

    

    def launch_game(self, py_path):
        play_click_sound()
        if os.path.exists(py_path):
            try:
                # Stop BGM before starting the game
                pygame.mixer.music.stop()

                def run_game():
                    try:
                        # Start the game process and wait for it to finish
                        process = subprocess.Popen([sys.executable, py_path])
                        process.wait()  # Wait until the game closes
                    finally:
                        # Resume BGM when game exits
                        play_music()

                # Run the game in a separate thread so UI stays responsive
                threading.Thread(target=run_game, daemon=True).start()

            except Exception as e:
                play_error_sound()
                self.show_error(f"Error launching {py_path}: {e}")
        else:
            play_error_sound()
            self.show_error(f"File not found: {py_path}")



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
