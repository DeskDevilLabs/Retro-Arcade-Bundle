import pygame
import sys
import random
from datetime import datetime
from pygame import mixer
import json
import os
import platform

# Initialize pygame early for sound/mixer
pygame.init()
pygame.mixer.init()

# Determine the correct paths for data files
def get_data_path(filename):
    # If we're running as a PyInstaller bundle
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, filename)

def get_writable_path(filename):
    # Get appropriate writable location based on OS
    if platform.system() == "Windows":
        appdata = os.getenv('APPDATA')
        save_dir = os.path.join(appdata, 'BrickBreaker')
    else:  # Linux/Mac
        home = os.path.expanduser("~")
        save_dir = os.path.join(home, '.brickbreaker')
    
    os.makedirs(save_dir, exist_ok=True)
    return os.path.join(save_dir, filename)

# Sound files
try:
    bounce_sound = pygame.mixer.Sound(get_data_path("bounce.wav"))
    explosion_sound = pygame.mixer.Sound(get_data_path("explosion.wav"))
    powerup_sound = pygame.mixer.Sound(get_data_path("powerup.wav"))
    intro_sound = pygame.mixer.Sound(get_data_path("intro_music.wav"))
    bgm_sound = pygame.mixer.Sound(get_data_path("brick_breaker_bgm.wav"))
except:
    # Fallback if sound files aren't found
    class DummySound:
        def play(self): pass
        def stop(self): pass
        def set_volume(self, vol): pass
    
    bounce_sound = DummySound()
    explosion_sound = DummySound()
    powerup_sound = DummySound()
    intro_sound = DummySound()
    bgm_sound = DummySound()

# Leaderboard file path
LEADERBOARD_FILE = get_writable_path("brick_breaker_leaderboard.json")

# Initialize Pygame with a maximized window
info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE | pygame.SCALED)
# On Windows, you can use this to maximize:
if sys.platform == 'win32':
    import ctypes
    hwnd = pygame.display.get_wm_info()['window']
    ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE = 3
pygame.display.set_caption('Brick Breaker')

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (200, 200, 200)

# Game settings
FPS = 60
clock = pygame.time.Clock()

class LeaderBoard:
    def __init__(self):
        self.scores = []
        self.load_scores()
    
    def load_scores(self):
        try:
            if os.path.exists(LEADERBOARD_FILE):
                with open(LEADERBOARD_FILE, 'r') as f:
                    # Load scores and remove duplicates
                    loaded_scores = json.load(f)
                    
                    # Create a set to track unique scores
                    seen_scores = set()
                    unique_scores = []
                    
                    for score in loaded_scores:
                        # Create a tuple of the score data that should be unique
                        score_key = (score['score'], score['level'], score['date'])
                        
                        if score_key not in seen_scores:
                            seen_scores.add(score_key)
                            unique_scores.append(score)
                    
                    # Sort and keep top 10
                    unique_scores.sort(key=lambda x: x['score'], reverse=True)
                    self.scores = unique_scores[:10]
            else:
                # Create file if it doesn't exist
                self.save_scores()
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading leaderboard: {e}")
            self.scores = []
    
    def save_scores(self):
        try:
            with open(LEADERBOARD_FILE, 'w') as f:
                json.dump(self.scores, f, indent=4)
        except IOError as e:
            print(f"Error saving leaderboard: {e}")
    
    def add_score(self, score, level):
        if score > 0:
            new_entry = {
                'score': score,
                'level': level,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            
            # Add the new score to the list
            self.scores.append(new_entry)
            
            # Remove duplicates
            seen_scores = set()
            unique_scores = []
            
            for score_entry in self.scores:
                score_key = (score_entry['score'], score_entry['level'], score_entry['date'])
                if score_key not in seen_scores:
                    seen_scores.add(score_key)
                    unique_scores.append(score_entry)
            
            # Sort by score in descending order
            unique_scores.sort(key=lambda x: x['score'], reverse=True)
            
            # Keep only top 10 scores
            self.scores = unique_scores[:10]
            
            # Save to file
            self.save_scores()
    
    def get_top_scores(self, limit=10):
        return self.scores[:limit]
    
    def get_high_score(self):
        return self.scores[0]['score'] if self.scores else 0
    
    def reset_scores(self):
        self.scores = []
        self.save_scores()

class OptionsMenu:
    def __init__(self):
        self.selected_option = 0
        self.options = ["Back"]
        self.option_rects = []
        self.bgm_volume = 0.5  # Default volume
        self.sfx_volume = 0.5  # Default volume
        self.muted = False
        self.slider_width = 200
        self.slider_height = 10
        self.handle_width = 20
        self.handle_height = 20
        self.bgm_slider_x = SCREEN_WIDTH // 2 - self.slider_width // 2
        self.sfx_slider_x = SCREEN_WIDTH // 2 - self.slider_width // 2
        self.slider_y = SCREEN_HEIGHT // 2 - 50
        self.dragging_bgm = False
        self.dragging_sfx = False
        self.reset_confirm = False

        # Slider track rectangles for easier collision detection
        self.bgm_slider_rect = pygame.Rect(
            self.bgm_slider_x,
            self.slider_y,
            self.slider_width,
            self.slider_height
        )
        self.sfx_slider_rect = pygame.Rect(
            self.sfx_slider_x,
            self.slider_y + 50,
            self.slider_width,
            self.slider_height
        )

    def reset_confirmation(self):
        self.reset_confirm = False
    
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.selected_option = (self.selected_option - 1) % len(self.options)
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.selected_option = (self.selected_option + 1) % len(self.options)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return self.options[self.selected_option].lower()
            elif event.key == pygame.K_ESCAPE:
                return "back"
            elif event.key == pygame.K_m:
                return self.toggle_mute()
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                mouse_pos = event.pos
                
                # Check if clicking on back button
                for i, rect in enumerate(self.option_rects):
                    if rect.collidepoint(mouse_pos):
                        return self.options[i].lower()
                
                # Check if clicking on BGM slider area or handle
                bgm_handle_x = self.bgm_slider_x + int(self.bgm_volume * self.slider_width)
                bgm_handle_rect = pygame.Rect(
                    bgm_handle_x - self.handle_width // 2,
                    self.slider_y - self.handle_height // 2,
                    self.handle_width,
                    self.handle_height
                )
                if self.bgm_slider_rect.collidepoint(mouse_pos) or bgm_handle_rect.collidepoint(mouse_pos):
                    self.dragging_bgm = True
                    # Update volume immediately to where user clicked
                    self.bgm_volume = max(0, min(1, (mouse_pos[0] - self.bgm_slider_x) / self.slider_width))
                    return "update_volume"
                
                # Check if clicking on SFX slider area or handle
                sfx_handle_x = self.sfx_slider_x + int(self.sfx_volume * self.slider_width)
                sfx_handle_rect = pygame.Rect(
                    sfx_handle_x - self.handle_width // 2,
                    self.slider_y + 50 - self.handle_height // 2,
                    self.handle_width,
                    self.handle_height
                )
                if self.sfx_slider_rect.collidepoint(mouse_pos) or sfx_handle_rect.collidepoint(mouse_pos):
                    self.dragging_sfx = True
                    # Update volume immediately to where user clicked
                    self.sfx_volume = max(0, min(1, (mouse_pos[0] - self.sfx_slider_x) / self.slider_width))
                    return "update_volume"
                
                # Check if clicking on mute button
                mute_rect = pygame.Rect(
                    SCREEN_WIDTH // 2 - 50,
                    self.slider_y + 100,
                    100,
                    30
                )
                if mute_rect.collidepoint(mouse_pos):
                    return self.toggle_mute()
                
                # Check if clicking on reset scores button
                reset_rect = pygame.Rect(
                    SCREEN_WIDTH // 2 - 100,
                    self.slider_y + 150,
                    200,
                    30
                )
                if reset_rect.collidepoint(mouse_pos):
                    if self.reset_confirm:
                        return "reset_scores"
                    else:
                        self.reset_confirm = True
                        return None
                
                # Check if clicking on confirm reset button
                if self.reset_confirm:
                    confirm_rect = pygame.Rect(
                        SCREEN_WIDTH // 2 - 100,
                        self.slider_y + 190,
                        200,
                        30
                    )
                    if confirm_rect.collidepoint(mouse_pos):
                        self.reset_confirmation()
                        return "reset_scores"
                    cancel_rect = pygame.Rect(
                        SCREEN_WIDTH // 2 - 100,
                        self.slider_y + 230,
                        200,
                        30
                    )
                    if cancel_rect.collidepoint(mouse_pos):
                        self.reset_confirm = False
                        return None
                        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging_bgm = False
                self.dragging_sfx = False
                
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_bgm:
                mouse_x = event.pos[0]
                self.bgm_volume = max(0, min(1, (mouse_x - self.bgm_slider_x) / self.slider_width))
                return "update_volume"
            elif self.dragging_sfx:
                mouse_x = event.pos[0]
                self.sfx_volume = max(0, min(1, (mouse_x - self.sfx_slider_x) / self.slider_width))
                return "update_volume"
                
        return None
    
    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            pygame.mixer.music.set_volume(0)
            bounce_sound.set_volume(0)
            explosion_sound.set_volume(0)
            powerup_sound.set_volume(0)
        else:
            pygame.mixer.music.set_volume(self.bgm_volume)
            bounce_sound.set_volume(self.sfx_volume)
            explosion_sound.set_volume(self.sfx_volume)
            powerup_sound.set_volume(self.sfx_volume)
        return "update_volume"
    
    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        surface.blit(overlay, (0, 0))
        
        menu_width = 400
        menu_height = 400
        menu_x = (SCREEN_WIDTH - menu_width) // 2
        menu_y = (SCREEN_HEIGHT - menu_height) // 2
        
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        pygame.draw.rect(surface, DARK_GRAY, menu_rect)
        pygame.draw.rect(surface, WHITE, menu_rect, 3)
        
        title_font = pygame.font.Font(None, 48)
        title_text = title_font.render("OPTIONS", True, YELLOW)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, menu_y + 40))
        surface.blit(title_text, title_rect)
        
        # Draw volume controls
        option_font = pygame.font.Font(None, 36)
        
        # BGM Volume
        bgm_text = option_font.render("BGM Volume:", True, WHITE)
        surface.blit(bgm_text, (self.bgm_slider_x, self.slider_y - 30))
        
        # Draw BGM slider track
        pygame.draw.rect(surface, GRAY, self.bgm_slider_rect)
        pygame.draw.rect(surface, WHITE, self.bgm_slider_rect, 1)
        
        # Draw BGM slider handle
        bgm_handle_x = self.bgm_slider_x + int(self.bgm_volume * self.slider_width)
        pygame.draw.rect(surface, YELLOW, (
            bgm_handle_x - self.handle_width // 2,
            self.slider_y - self.handle_height // 2,
            self.handle_width,
            self.handle_height
        ))
        
        # SFX Volume
        sfx_text = option_font.render("SFX Volume:", True, WHITE)
        surface.blit(sfx_text, (self.sfx_slider_x, self.slider_y + 20))
        
        # Draw SFX slider track
        pygame.draw.rect(surface, GRAY, self.sfx_slider_rect)
        pygame.draw.rect(surface, WHITE, self.sfx_slider_rect, 1)
        
        # Draw SFX slider handle
        sfx_handle_x = self.sfx_slider_x + int(self.sfx_volume * self.slider_width)
        pygame.draw.rect(surface, YELLOW, (
            sfx_handle_x - self.handle_width // 2,
            self.slider_y + 50 - self.handle_height // 2,
            self.handle_width,
            self.handle_height
        ))
        
        # Mute button
        mute_color = RED if self.muted else GREEN
        mute_text = "Unmute" if self.muted else "Mute"
        mute_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - 50,
            self.slider_y + 100,
            100,
            30
        )
        pygame.draw.rect(surface, mute_color, mute_rect)
        pygame.draw.rect(surface, WHITE, mute_rect, 2)
        mute_label = option_font.render(mute_text, True, WHITE)
        mute_label_rect = mute_label.get_rect(center=mute_rect.center)
        surface.blit(mute_label, mute_label_rect)
        
        # Reset scores button
        reset_color = ORANGE
        reset_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - 100,
            self.slider_y + 150,
            200,
            30
        )
        pygame.draw.rect(surface, reset_color, reset_rect)
        pygame.draw.rect(surface, WHITE, reset_rect, 2)
        reset_text = "Reset Scores" if not self.reset_confirm else "Confirm Reset?"
        reset_label = option_font.render(reset_text, True, BLACK)
        reset_label_rect = reset_label.get_rect(center=reset_rect.center)
        surface.blit(reset_label, reset_label_rect)
        
        if self.reset_confirm:
            # Confirm reset button
            confirm_rect = pygame.Rect(
                SCREEN_WIDTH // 2 - 100,
                self.slider_y + 190,
                200,
                30
            )
            pygame.draw.rect(surface, RED, confirm_rect)
            pygame.draw.rect(surface, WHITE, confirm_rect, 2)
            confirm_label = option_font.render("YES - Reset All", True, WHITE)
            confirm_label_rect = confirm_label.get_rect(center=confirm_rect.center)
            surface.blit(confirm_label, confirm_label_rect)
            
            # Cancel button
            cancel_rect = pygame.Rect(
                SCREEN_WIDTH // 2 - 100,
                self.slider_y + 230,
                200,
                30
            )
            pygame.draw.rect(surface, GREEN, cancel_rect)
            pygame.draw.rect(surface, WHITE, cancel_rect, 2)
            cancel_label = option_font.render("NO - Cancel", True, WHITE)
            cancel_label_rect = cancel_label.get_rect(center=cancel_rect.center)
            surface.blit(cancel_label, cancel_label_rect)
        
        # Back button
        back_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - 50,
            self.slider_y + 280,
            100,
            30
        )
        pygame.draw.rect(surface, BLUE, back_rect)
        pygame.draw.rect(surface, WHITE, back_rect, 2)
        back_label = option_font.render("Back", True, WHITE)
        back_label_rect = back_label.get_rect(center=back_rect.center)
        surface.blit(back_label, back_label_rect)
        self.option_rects = [back_rect]
        
        # Instructions
        instruction_font = pygame.font.Font(None, 24)
        instructions = [
            "Drag sliders to adjust volume",
            "Press M to toggle mute",
            "ESC to go back"
        ]
        for i, instruction in enumerate(instructions):
            text = instruction_font.render(instruction, True, LIGHT_GRAY)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 80 + (i * 20)))
            surface.blit(text, text_rect)

class Paddle:
    def __init__(self):
        self.width = 100
        self.height = 15
        self.x = (SCREEN_WIDTH - self.width) // 2
        self.y = SCREEN_HEIGHT - 50
        self.base_speed = 10  # Store base speed
        self.speed = self.base_speed  # Current speed
        self.color = WHITE
    
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(surface, CYAN, (self.x, self.y, self.width, self.height), 2)
    
    def move(self, direction):
        if direction == "left" and self.x > 0:
            self.x -= self.speed
        if direction == "right" and self.x < SCREEN_WIDTH - self.width:
            self.x += self.speed

    def set_speed(self, new_speed):
        self.speed = new_speed

class Ball:
    def __init__(self, game):
        self.game = game  # Store reference to game instance
        self.radius = 8
        self.reset()
        self.color = WHITE
        self.manual_control = False  # Added for manual control
        self.speed_increase_factor = 1.0  # Current speed multiplier (1.0 = normal speed)
        self.max_speed_multiplier = 3.0  # Maximum speed increase
        self.speed_increment = 0.05  # How much speed increases per event
    
    def reset(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.dx = random.choice([-4, -3, 3, 4])
        self.dy = -4
        self.active = False
        self.manual_control = False  # Reset manual control
        self.speed_increase_factor = 1.0  # Reset speed to normal
    
    def increase_speed(self):
        """Increase the ball's speed gradually, but keep it capped."""
        if self.speed_increase_factor < self.max_speed_multiplier:
            self.speed_increase_factor = min(
                self.max_speed_multiplier,
                self.speed_increase_factor + self.speed_increment
            )
            # Normalize current direction
            direction_x = 1 if self.dx > 0 else -1
            direction_y = 1 if self.dy > 0 else -1
            base_speed = 4  # your normal starting speed per axis
            self.dx = direction_x * base_speed * self.speed_increase_factor
            self.dy = direction_y * base_speed * self.speed_increase_factor

    
    def draw(self, surface):
        color = RED if self.manual_control else WHITE  # Change color when in manual mode
        pygame.draw.circle(surface, color, (self.x, self.y), self.radius)
        pygame.draw.circle(surface, CYAN, (self.x, self.y), self.radius, 1)
    
    def move(self, game):
        if not self.active:
            return False
            
        if self.manual_control:
            # Handle manual movement with arrow keys
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.x = max(self.radius, self.x - 5)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.x = min(SCREEN_WIDTH - self.radius, self.x + 5)
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.y = max(self.radius, self.y - 5)
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.y = min(SCREEN_HEIGHT - self.radius, self.y + 5)
        else:
            # Normal ball movement with speed factor applied
            self.x += self.dx * self.speed_increase_factor
            self.y += self.dy * self.speed_increase_factor
            
            # Wall collisions with sound
            if self.x <= self.radius or self.x >= SCREEN_WIDTH - self.radius:
                self.dx *= -1
                bounce_sound.play()
                
            if self.y <= self.radius:
                self.dy *= -1
                bounce_sound.play()
                
        # Check if ball fell below paddle
        if self.y >= SCREEN_HEIGHT + self.radius:
            return True  # Ball lost
        return False
    
    def collide_paddle(self, paddle):
        if (self.y + self.radius >= paddle.y and 
            self.y - self.radius <= paddle.y + paddle.height and
            self.x + self.radius >= paddle.x and 
            self.x - self.radius <= paddle.x + paddle.width):
            
            # Calculate bounce angle based on where ball hits paddle
            relative_x = (self.x - (paddle.x + paddle.width / 2)) / (paddle.width / 2)
            self.dx = relative_x * 5 * self.speed_increase_factor  # Apply speed factor
            self.dy *= -1   
            return True
        return False
    
    def collide_brick(self, brick):
        if not brick.active:
            return False
            
        if (self.x + self.radius >= brick.x and 
            self.x - self.radius <= brick.x + brick.width and
            self.y + self.radius >= brick.y and 
            self.y - self.radius <= brick.y + brick.height):
            
            # Determine side of collision
            if (self.x < brick.x or self.x > brick.x + brick.width):
                self.dx *= -1
            else:
                self.dy *= -1
            
            brick.active = False
            explosion_sound.play()

            # Increase speed when hitting a brick
            self.increase_speed()

            # Set respawn timer for levels 7-10 (only during first minute)
            if 7 <= self.game.level <= 10:
                current_time = pygame.time.get_ticks()
                level_elapsed = current_time - self.game.level_start_time
                
                if level_elapsed <= 60000:  # Only if in first minute
                    respawn_time = {
                        7: 50000,  
                        8: 30000,  
                        9: 20000,  
                        10: 15000  
                    }[self.game.level]
                    self.game.brick_respawn_timers[id(brick)] = current_time + respawn_time
            
            # 20% chance to spawn power-up
            if random.random() < 0.2:
                powerup_type = random.randint(1, 3)
                self.game.powerups.append(
                    PowerUp(brick.x + brick.width//2 - 15, brick.y, powerup_type)
                )
    
            return True
        return False

class Brick:
    def __init__(self, x, y, width, height, color, points):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.points = points
        self.active = True
    
    def draw(self, surface):
        if self.active:
            pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))
            pygame.draw.rect(surface, BLACK, (self.x, self.y, self.width, self.height), 2)

class PowerUp:
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 15
        self.type = type  # 1: extra life, 2: paddle expand, 3: ball speed down
        self.speed = 3
        self.active = True
        
        if self.type == 1:
            self.color = GREEN
        elif self.type == 2:
            self.color = YELLOW
        else:
            self.color = BLUE
    
    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.active = False
    
    def draw(self, surface):
        if self.active:
            pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))
            pygame.draw.rect(surface, BLACK, (self.x, self.y, self.width, self.height), 2)
            
            # Draw symbol based on type
            if self.type == 1:  # Heart for extra life
                points = [
                    (self.x + self.width//2, self.y + 3),
                    (self.x + self.width - 3, self.y + self.height//2),
                    (self.x + self.width//2, self.y + self.height - 3),
                    (self.x + 3, self.y + self.height//2)
                ]
                pygame.draw.polygon(surface, BLACK, points)
            elif self.type == 2:  # Arrows for paddle expand
                pygame.draw.rect(surface, BLACK, (self.x + 5, self.y + self.height//2 - 1, self.width - 10, 2))
                pygame.draw.polygon(surface, BLACK, [
                    (self.x + self.width - 5, self.y + self.height//2 - 4),
                    (self.x + self.width - 5, self.y + self.height//2 + 4),
                    (self.x + self.width, self.y + self.height//2)
                ])
                pygame.draw.polygon(surface, BLACK, [
                    (self.x + 5, self.y + self.height//2 - 4),
                    (self.x + 5, self.y + self.height//2 + 4),
                    (self.x, self.y + self.height//2)
                ])
            else:  # Minus for ball speed down
                pygame.draw.rect(surface, BLACK, (self.x + 5, self.y + self.height//2 - 1, self.width - 10, 2))

class PauseMenu:
    def __init__(self):
        self.selected_option = 0
        self.options = ["Resume", "Leaderboard", "Options", "Restart", "Exit"]  # Added Options
        self.option_rects = []
        self.showing_leaderboard = False
        self.showing_options = False  # Added for options menu
        self.cheat_buffer = []
        self.cheat_code = "cheat"
        self.cheat_activated = False
        self.options_menu = OptionsMenu()  # Create options menu instance

    def draw_leaderboard(self, surface, leaderboard):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        surface.blit(overlay, (0, 0))
        
        menu_width = 600
        menu_height = 500
        menu_x = (SCREEN_WIDTH - menu_width) // 2
        menu_y = (SCREEN_HEIGHT - menu_height) // 2
        
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        pygame.draw.rect(surface, DARK_GRAY, menu_rect)
        pygame.draw.rect(surface, WHITE, menu_rect, 3)
        
        title_font = pygame.font.Font(None, 48)
        title_text = title_font.render("LEADERBOARD", True, YELLOW)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, menu_y + 40))
        surface.blit(title_text, title_rect)
        
        header_font = pygame.font.Font(None, 36)
        score_font = pygame.font.Font(None, 32)
        
        # Column headers
        headers = ["Rank", "Score", "Level", "Date"]
        header_y = menu_y + 80
        col_positions = [menu_x + 50, menu_x + 150, menu_x + 300, menu_x + 400]
        
        for i, header in enumerate(headers):
            header_text = header_font.render(header, True, CYAN)
            surface.blit(header_text, (col_positions[i], header_y))
        
        # Draw scores
        top_scores = leaderboard.get_top_scores()
        if not top_scores:
            no_scores = header_font.render("No scores yet!", True, WHITE)
            surface.blit(no_scores, no_scores.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))
        else:
            for i, score in enumerate(top_scores):
                y_pos = header_y + 40 + (i * 30)
                
                # Rank
                rank_text = score_font.render(f"{i+1}.", True, WHITE)
                surface.blit(rank_text, (col_positions[0], y_pos))
                
                # Score
                score_text = score_font.render(str(score['score']), True, WHITE)
                surface.blit(score_text, (col_positions[1], y_pos))
                
                # Level
                level_text = score_font.render(str(score['level']), True, WHITE)
                surface.blit(level_text, (col_positions[2], y_pos))
                
                # Date
                date_text = score_font.render(score['date'], True, WHITE)
                surface.blit(date_text, (col_positions[3], y_pos))
        
        # Instructions
        instruction_font = pygame.font.Font(None, 24)
        instructions = ["ESC or Backspace to go back"]
        for i, instruction in enumerate(instructions):
            text = instruction_font.render(instruction, True, LIGHT_GRAY)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
            surface.blit(text, text_rect)
    
    def handle_input(self, event, game=None):
        if self.showing_options:
            action = self.options_menu.handle_input(event)
            if action == "back":
                self.showing_options = False
            elif action == "reset_scores":
                # Handle score reset
                self.showing_options = False
                return "reset_scores"
            elif action == "update_volume": 
                # Update volumes in game
                if game:  # Only update if game instance was provided
                    game.bgm_volume = self.options_menu.bgm_volume
                    game.sfx_volume = self.options_menu.sfx_volume
                    game.muted = self.options_menu.muted
                    
                    # Apply volume changes immediately
                    if game.bgm:
                        game.bgm.set_volume(0 if game.muted else game.bgm_volume)
                
                # Update SFX volumes regardless of game instance
                bounce_sound.set_volume(0 if self.options_menu.muted else self.options_menu.sfx_volume)
                explosion_sound.set_volume(0 if self.options_menu.muted else self.options_menu.sfx_volume)
                return "update_volume"
            return None
        
        if event.type == pygame.KEYDOWN:
            if not self.showing_leaderboard:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.selected_option = (self.selected_option - 1) % len(self.options)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.selected_option = (self.selected_option + 1) % len(self.options)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if self.options[self.selected_option] == "Options":
                        self.showing_options = True
                        return None
                    return self.options[self.selected_option].lower()
                
                # Cheat code detection
                if event.unicode:
                    self.cheat_buffer.append(event.unicode.lower())
                    if len(self.cheat_buffer) > len(self.cheat_code):
                        self.cheat_buffer.pop(0)
                    
                    if "".join(self.cheat_buffer) == self.cheat_code:
                        self.cheat_activated = True
                        return "cheat"
            else:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                    self.showing_leaderboard = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if not self.showing_leaderboard and not self.showing_options:
                    for i, rect in enumerate(self.option_rects):
                        if rect.collidepoint(event.pos):
                            if self.options[i] == "Options":
                                self.showing_options = True
                                return None
                            return self.options[i].lower()
                elif self.showing_leaderboard:
                    self.showing_leaderboard = False
        return None
    
    def draw(self, surface, leaderboard, game=None):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        surface.blit(overlay, (0, 0))
        
        if self.showing_options:
            self.options_menu.draw(surface)
            if game:
                # Update game volumes if provided
                game.bgm_volume = self.options_menu.bgm_volume
                game.sfx_volume = self.options_menu.sfx_volume
                game.muted = self.options_menu.muted
        elif self.showing_leaderboard:
            self.draw_leaderboard(surface, leaderboard)
        else:
            self.draw_main_menu(surface)
    
    def draw_main_menu(self, surface):
        menu_width = 300
        menu_height = 300  # Increased height for additional option
        menu_x = (SCREEN_WIDTH - menu_width) // 2
        menu_y = (SCREEN_HEIGHT - menu_height) // 2
        
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        pygame.draw.rect(surface, DARK_GRAY, menu_rect)
        pygame.draw.rect(surface, WHITE, menu_rect, 3)
        
        title_font = pygame.font.Font(None, 48)
        title_text = title_font.render("PAUSED", True, YELLOW)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, menu_y + 40))
        surface.blit(title_text, title_rect)
        
        option_font = pygame.font.Font(None, 36)
        self.option_rects = []
        for i, option in enumerate(self.options):
            color = YELLOW if i == self.selected_option else WHITE
            option_text = option_font.render(option, True, color)
            option_y = menu_y + 80 + (i * 40)
            option_rect = option_text.get_rect(center=(SCREEN_WIDTH//2, option_y))
            surface.blit(option_text, option_rect)
            self.option_rects.append(pygame.Rect(
                option_rect.x - 10, option_rect.y - 5,
                option_rect.width + 20, option_rect.height + 10
            ))
            
            if i == self.selected_option:
                pygame.draw.rect(surface, YELLOW, self.option_rects[i], 2)
        
        instruction_font = pygame.font.Font(None, 24)
        instructions = ["↑↓ or Click to Select", "Enter/Space to Confirm", "ESC to Close"]
        for i, instruction in enumerate(instructions):
            text = instruction_font.render(instruction, True, LIGHT_GRAY)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 80 + (i * 20)))
            surface.blit(text, text_rect)

class LogoScreen:
    def __init__(self):
        self.logos = []
        self.current_logo = 0
        self.logo_duration = 4000  # 4 seconds per logo set
        self.fade_duration = 1000  # 1 second fade in/out
        self.start_time = pygame.time.get_ticks()
        self.load_logos()
        self.fade_state = "in"  # "in", "hold", or "out"
        self.next_logo_time = self.start_time + self.fade_duration
        self.paired_logos = []  # Store pairs of logos to display together

        # Keys that should trigger skipping the logos
        self.skip_keys = {
            pygame.K_TAB, pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE
        }
        # Add all alphabet and number keys
        self.skip_keys.update(range(pygame.K_a, pygame.K_z + 1))  # a-z
        self.skip_keys.update(range(pygame.K_0, pygame.K_9 + 1))  # 0-9

    def load_logos(self):
        # Try to load multiple logo images
        logo_paths = [
            get_data_path("DD Lab1.png"),
            (get_data_path("logo1.png"), get_data_path("logo2.jpg")),
            get_data_path("brick_breaker.jpg")
        ]
        
        for item in logo_paths:
            try:
                # Handle single logos
                if isinstance(item, str):
                    logo = pygame.image.load(item)
                    # Scale logo if needed
                    max_width = SCREEN_WIDTH * 0.9
                    max_height = SCREEN_HEIGHT * 0.8
                    logo_width, logo_height = logo.get_size()
                    scale = min(max_width / logo_width, max_height / logo_height)
                    if scale < 1:
                        logo = pygame.transform.scale(
                            logo, 
                            (int(logo_width * scale), int(logo_height * scale)))
                    self.logos.append([logo])  # Store as single-item list
                
                # Handle logo pairs
                elif isinstance(item, tuple) and len(item) == 2:
                    logo_pair = []
                    for path in item:
                        logo = pygame.image.load(path)
                        # Scale each logo to fit half the screen
                        max_width = SCREEN_WIDTH * 0.45
                        max_height = SCREEN_HEIGHT * 0.8
                        logo_width, logo_height = logo.get_size()
                        scale = min(max_width / logo_width, max_height / logo_height)
                        if scale < 1:
                            logo = pygame.transform.scale(
                                logo, 
                                (int(logo_width * scale), int(logo_height * scale)))
                        logo_pair.append(logo)
                    self.logos.append(logo_pair)
            
            except Exception as e:
                pass
        
        # If no logos loaded, create text-based ones
        if not self.logos:
            font = pygame.font.Font(None, 72)
            for i in range(3):
                surf = pygame.Surface((400, 200), pygame.SRCALPHA)
                text = font.render(f"Desk Devil Labs", True, WHITE)
                text_rect = text.get_rect(center=(200, 100))
                surf.blit(text, text_rect)
                pygame.draw.rect(surf, WHITE, (0, 0, 400, 200), 2)
                self.logos.append([surf])
    
    def update(self):
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time

        # Check for key presses to skip
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                # Skip only if it's one of our allowed keys
                if event.key in self.skip_keys:
                    return True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Also allow skipping with mouse clicks
                return True
        
        # Update fade state
        if self.fade_state == "in" and current_time >= self.next_logo_time:
            self.fade_state = "hold"
            self.next_logo_time = current_time + (self.logo_duration - 2 * self.fade_duration)
        elif self.fade_state == "hold" and current_time >= self.next_logo_time:
            self.fade_state = "out"
            self.next_logo_time = current_time + self.fade_duration
        elif self.fade_state == "out" and current_time >= self.next_logo_time:
            self.current_logo += 1
            if self.current_logo >= len(self.logos):
                return True
            self.start_time = current_time
            self.fade_state = "in"
            self.next_logo_time = current_time + self.fade_duration
        
        return False
    
    def draw(self, surface):
        surface.fill(BLACK)
        
        if self.current_logo < len(self.logos):
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.start_time
            
            # Calculate alpha based on fade state
            if self.fade_state == "in":
                alpha = min(255, int(255 * (elapsed / self.fade_duration)))
            elif self.fade_state == "out":
                alpha = max(0, 255 - int(255 * ((current_time - (self.next_logo_time - self.fade_duration)) / self.fade_duration)))
            else:  # hold
                alpha = 255
            
            # Get current logo(s) - could be single or pair
            current_logos = self.logos[self.current_logo]
            
            # Create a composite surface if multiple logos
            if len(current_logos) > 1:
                # Calculate total width and max height
                total_width = sum(logo.get_width() for logo in current_logos) + 20 * (len(current_logos) - 1)
                max_height = max(logo.get_height() for logo in current_logos)
                
                # Create a temporary surface for the composite
                composite = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
                x_offset = 0
                for logo in current_logos:
                    composite.blit(logo, (x_offset, (max_height - logo.get_height()) // 2))
                    x_offset += logo.get_width() + 20
                
                # Apply alpha to the composite
                composite.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
                composite_rect = composite.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                surface.blit(composite, composite_rect)
            
            else:  # Single logo
                logo = current_logos[0]
                temp_surface = pygame.Surface((logo.get_width(), logo.get_height()), pygame.SRCALPHA)
                temp_surface.blit(logo, (0, 0))
                temp_surface.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
                logo_rect = temp_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                surface.blit(temp_surface, logo_rect)

class TitleScreen:
    def __init__(self, leaderboard):
        self.show_title = True
        self.ball = Ball(self) 
        self.title_font = pygame.font.Font(None, 72)
        self.instruction_font = pygame.font.Font(None, 36)
        self.leaderboard = leaderboard
        self.start_button = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT*2//3, 200, 50)
        self.exit_button = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT*2//3 + 70, 200, 50)
        
        # Initialize ball position and velocity
        self.ball.x = SCREEN_WIDTH // 2
        self.ball.y = SCREEN_HEIGHT // 3
        self.ball.dx = 4
        self.ball.dy = 4
        self.ball.active = True  # Make the ball active in title screen
        
        # Initialize paddle
        self.paddle = Paddle()
        self.paddle.width = 100 
        self.paddle.x = SCREEN_WIDTH // 2 - self.paddle.width // 2
        self.paddle.y = SCREEN_HEIGHT // 2 + 100
        
        
        # Create demo bricks
        self.bricks = []
        self.brick_respawn_timers = {}  # Dictionary to track respawn timers
        self.setup_bricks()

        # otr
        self.sfx_volume = 0.2 
    def set_sound_volumes(self):
        """Set reduced volumes for title screen sounds"""
        bounce_sound.set_volume(self.sfx_volume)
        explosion_sound.set_volume(self.sfx_volume)

    def get_hardcoded_high_score(self):
        return {
            "score": 10320,
            "level": 10,
            "date": "On 01-07-2025 1:45 AM"
        }
        
    def setup_bricks(self):
        self.bricks = []
        brick_colors = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE]
        brick_points = [10, 20, 30, 40, 50, 60]
        
        # Calculate brick layout to center them
        brick_width = 150
        brick_height = 25
        cols = 8
        gap = 10
        
        # Calculate total width including gaps
        total_width = cols * brick_width + (cols - 1) * gap
        start_x = (SCREEN_WIDTH - total_width) // 2
        
        for row in range(3):
            for col in range(cols):
                brick_x = start_x + col * (brick_width + gap)
                brick_y = 50 + row * (brick_height + gap)
                self.bricks.append(
                    Brick(brick_x, brick_y, brick_width, brick_height, brick_colors[row], brick_points[row]))
    
    def update(self):
        # Update brick respawn timers
        self.set_sound_volumes()
        current_time = pygame.time.get_ticks()
        bricks_to_respawn = []
        
        for brick_id, respawn_time in list(self.brick_respawn_timers.items()):
            if current_time >= respawn_time:
                bricks_to_respawn.append(brick_id)
        
        for brick_id in bricks_to_respawn:
            del self.brick_respawn_timers[brick_id]
            for brick in self.bricks:
                if id(brick) == brick_id:
                    brick.active = True
                    break
        
        # Update ball position
        self.ball.x += self.ball.dx
        self.ball.y += self.ball.dy
        
        # Wall collisions with bouncing
        if self.ball.x <= self.ball.radius or self.ball.x >= SCREEN_WIDTH - self.ball.radius:
            self.ball.dx *= -1
            bounce_sound.play()
            
        if self.ball.y <= self.ball.radius or self.ball.y >= SCREEN_HEIGHT - self.ball.radius:
            self.ball.dy *= -1
            bounce_sound.play()
        
        # Paddle collision
        if (self.ball.y + self.ball.radius >= self.paddle.y and 
            self.ball.y - self.ball.radius <= self.paddle.y + self.paddle.height and
            self.ball.x + self.ball.radius >= self.paddle.x and 
            self.ball.x - self.ball.radius <= self.paddle.x + self.paddle.width):
            
            # Calculate bounce angle based on where ball hits paddle
            relative_x = (self.ball.x - (self.paddle.x + self.paddle.width / 2)) / (self.paddle.width / 2)
            self.ball.dx = relative_x * 30  # Max horizontal speed
            self.ball.dy *= -1
            bounce_sound.play()
        
        # Brick collisions
        for brick in self.bricks:
            if brick.active and (self.ball.x + self.ball.radius >= brick.x and 
                self.ball.x - self.ball.radius <= brick.x + brick.width and
                self.ball.y + self.ball.radius >= brick.y and 
                self.ball.y - self.ball.radius <= brick.y + brick.height):
                
                # Determine side of collision
                if (self.ball.x < brick.x or self.ball.x > brick.x + brick.width):
                    self.ball.dx *= -1
                else:
                    self.ball.dy *= -1
                
                explosion_sound.play()
                brick.active = False
                # Set respawn timer (3 seconds from now)
                self.brick_respawn_timers[id(brick)] = pygame.time.get_ticks() + 10000
                break  # Only collide with one brick per frame
        
        # Paddle follows ball's x-position directly
        target_x = self.ball.x - self.paddle.width // 2  # Center paddle under ball
        
        # Ensure paddle stays within screen bounds
        target_x = max(0, min(target_x, SCREEN_WIDTH - self.paddle.width))
        
        # Move paddle smoothly towards target position
        if abs(self.paddle.x - target_x) > self.paddle.speed:
            if self.paddle.x < target_x:
                self.paddle.x += self.paddle.speed
            else:
                self.paddle.x -= self.paddle.speed
        else:
            self.paddle.x = target_x  # Snap to position when close enough
    
    def draw(self, surface):
        surface.fill(BLACK)
        
        # Draw game elements
        self.paddle.draw(surface)
        self.ball.draw(surface)
        
        # Draw bricks
        for brick in self.bricks:
            brick.draw(surface)
        
        title_text = self.title_font.render("BRICK BREAKER", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
        surface.blit(title_text, title_rect)
        
        # Draw start button
        pygame.draw.rect(surface, GREEN, self.start_button)
        pygame.draw.rect(surface, BLACK, self.start_button, 2)
        start_text = self.instruction_font.render("START GAME", True, BLACK)
        start_rect = start_text.get_rect(center=self.start_button.center)
        surface.blit(start_text, start_rect)
        
        # Draw exit button
        pygame.draw.rect(surface, RED, self.exit_button)
        pygame.draw.rect(surface, BLACK, self.exit_button, 2)
        exit_text = self.instruction_font.render("EXIT", True, BLACK)
        exit_rect = exit_text.get_rect(center=self.exit_button.center)
        surface.blit(exit_text, exit_rect)
        
        # Show high score on title screen
        high_score = self.leaderboard.get_high_score()
        if high_score > 0:
            hs_text = self.instruction_font.render(f"Current High Score: {high_score}", True, YELLOW)
            hs_rect = hs_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3 + 50))
            surface.blit(hs_text, hs_rect)
        
        # ==== Display the hardcoded high score ====
        hardcoded_score = self.get_hardcoded_high_score()
        hs_text = self.instruction_font.render(
            f"Maximum High Score: {hardcoded_score['score']} (Level {hardcoded_score['level']}, {hardcoded_score['date']})", 
            True, GREEN
        )
        hs_rect = hs_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3 + 110))
        surface.blit(hs_text, hs_rect)
        
        controls = [
            "In Game Controls:",
            "Left/Right Arrow or A/D to Move Paddle",
            "SPACE to Launch Ball",
            "P to Pause",
            "ESC for Menu",
            "R to Restart"
        ]
        for i, control in enumerate(controls):
            text = self.instruction_font.render(control, True, LIGHT_GRAY)
            surface.blit(text, (50, SCREEN_HEIGHT - 200 + i * 30))
    
    def handle_events(self, event):
        self.set_sound_volumes()
        if event.type == pygame.QUIT:
            show_exit_credits()  # Show credits before quitting
            return False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.show_title = False
                return True
            elif event.key == pygame.K_ESCAPE:
                return False
            elif event.key == pygame.K_o:  # Shortcut for options
                self.showing_options = True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.start_button.collidepoint(event.pos):
                    self.show_title = False
                    return True
                elif self.exit_button.collidepoint(event.pos):
                    show_exit_credits()  # Show credits before quitting
                    return False
        return None        

class Game:
    def __init__(self):
        self.paddle = Paddle()
        self.ball = Ball(self)
        self.bricks = []
        self.powerups = []
        self.score = 0
        self.lives = 5
        self.level = 1
        self.game_over = False
        self.level_complete = False
        self.paused = False
        self.show_pause_menu = False
        self.leaderboard = LeaderBoard()
        self.pause_menu = PauseMenu()
        self.brick_respawn_timers = {}
        self.level_start_time = 0 
        
        # Audio settings
        self.bgm_volume = 0.5
        self.sfx_volume = 0.5
        self.muted = False
        
        # Initialize BGM-related attributes first
        self.bgm = None
        self.bgm_playing = False
        self.setup_audio()
        self.start_bgm()

        self.setup_level(self.level)

        # Cheat activation 
        self.mute_press_time = 0
        self.cheat_enabled = False
        self.cheat_activation_time = 0
        self.cheat_message_end_time = 60

    def update(self):
        if pygame.time.get_ticks() % 1000 == 0:  # Every second
            self.ball.increase_speed()
        # Skip update if game is paused
        if self.paused or self.show_pause_menu:
            return
        
        # Only respawn bricks during first minute of levels 7-10
        if 7 <= self.level <= 10:
            current_time = pygame.time.get_ticks()
            level_elapsed = current_time - self.level_start_time
            
            # Only respawn if we're in the first minute (60000 ms)
            if level_elapsed <= 60000:
                bricks_to_respawn = []
                
                for brick_id, respawn_time in list(self.brick_respawn_timers.items()):
                    if current_time >= respawn_time:
                        bricks_to_respawn.append(brick_id)
                
                for brick_id in bricks_to_respawn:
                    del self.brick_respawn_timers[brick_id]
                    for brick in self.bricks:
                        if id(brick) == brick_id:
                            brick.active = True
                            break
        
        # Update power-ups
        for powerup in self.powerups[:]:
            powerup.update()
            
            # Check if powerup hit paddle
            if (powerup.y + powerup.height >= self.paddle.y and
                powerup.x + powerup.width >= self.paddle.x and
                powerup.x <= self.paddle.x + self.paddle.width):
                
                self.apply_powerup(powerup.type)
                self.powerups.remove(powerup)
                powerup_sound.play()
                
            # Remove if off screen
            elif powerup.y > SCREEN_HEIGHT:
                self.powerups.remove(powerup)
        
        # Update ball movement if active
        if self.ball.active:
            ball_lost = self.ball.move(self)  # Pass self (the game instance) to move()
            if ball_lost:
                self.lives -= 1
                if self.lives <= 0:
                    self.game_over = True
                    # Save score when game is over
                    self.leaderboard.add_score(self.score, self.level)
                self.ball.reset()  # Always reset the ball after losing a life
        
        # Check for paddle collision
        if self.ball.active:
            if self.ball.collide_paddle(self.paddle):
                bounce_sound.play()
        
        # Check for brick collisions
        bricks_active = False
        for brick in self.bricks:
            if brick.active:
                bricks_active = True
                if self.ball.active and self.ball.collide_brick(brick):
                    self.score += brick.points
                    break  # Only collide with one brick per frame
        
        # Check if all bricks are destroyed (level complete)
        if not bricks_active and not self.level_complete and not self.game_over:
            self.level_complete = True
            self.ball.active = False
            # If this was the last level, save the score
            if self.level == 10:
                self.game_over = True
                self.leaderboard.add_score(self.score, self.level)

    def apply_powerup(self, type):
        # Play powerup sound (respect mute settings)
        powerup_sound.set_volume(0 if self.muted else self.sfx_volume)
        powerup_sound.play()
        if type == 1:  # Extra life
            self.lives += 1
        elif type == 2:  # Paddle expand
            self.paddle.width = min(200, self.paddle.width + 20)
        elif type == 3:  # Ball speed down
            self.ball.dx = max(-6, min(6, self.ball.dx * 0.8))
            self.ball.dy = max(-6, min(6, self.ball.dy * 0.8))
    
    def next_level(self):
        self.stop_bgm()  # Stop BGM between levels
        if self.level < 10:
            self.level += 1
            self.setup_level(self.level)
            self.level_complete = False
            self.ball.dx = random.choice([-4, -3, 3, 4])
            self.ball.dy = -4
            self.ball.manual_control = False  # Reset manual control for new level
            self.start_bgm()  # Start again if gameplay begins
            self.ball.reset()

            # Increase paddle speed after level 7
            if self.level >= 7:
                self.paddle.set_speed(self.paddle.base_speed * 1.7)  # 50% faster
            else:
                self.paddle.set_speed(self.paddle.base_speed)  # Reset to normal speed
        else:
            # Game is won completely - just set flags, don't show credits yet
            self.game_over = True
            self.level_complete = True
            return "game_won"  # Signal that game was won
        
    def setup_level(self, level):
        self.bricks = []
        self.powerups = []
        self.brick_respawn_timers = {}  # Clear respawn timers
        self.level_start_time = pygame.time.get_ticks()  # Record level start time
        
        # Calculate brick layout based on level
        rows = min(3 + level // 3, 8)  # More rows as levels progress
        cols = 8
        brick_width = 80
        brick_height = 25
        
        # Add gaps for higher levels
        if level == 1:
            col_gap = 10
            row_gap = col_gap // 2
        elif level == 2:
            col_gap = 10
            row_gap = 10
        elif level == 3:
            col_gap = 20  # Column gap size
            row_gap = 13  # Row gap is half of column gap
        elif level == 4:
            col_gap = 30  # Column gap size
            row_gap = col_gap // 2  # Row gap is half of column gap
        elif level == 5:
            col_gap = 40  # Column gap size
            row_gap = col_gap // 2  # Row gap is half of column gap
        elif level == 6:
            col_gap = 50  # Column gap size
            row_gap = col_gap // 2  # Row gap is half of column gap
        else:
            col_gap = 10  # Default padding
            row_gap = 10

        # Calculate total width of all bricks including gaps
        total_bricks_width = cols * brick_width + (cols - 1) * col_gap
        # Calculate starting x position to center the bricks
        start_x = (SCREEN_WIDTH - total_bricks_width) // 2
        
        colors = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE]
        points = [10, 20, 30, 40, 50, 60]  # Points per row
        
        for row in range(rows):
            for col in range(cols):
                # 10% chance for special brick in higher levels
                special = (level > 3) and (random.random() < 0.1)
                
                brick_x = start_x + col * (brick_width + col_gap)
                brick_y = 50 + row * (brick_height + row_gap)
                
                color = colors[row % len(colors)]
                point_value = points[row % len(points)]
                
                self.bricks.append(Brick(brick_x, brick_y, brick_width, brick_height, color, point_value))

    def setup_audio(self):
        # Initialize mixer if not already done
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()

        # Load BGM if not already loaded
        try:
            # Load BGM if not already loaded
            if not hasattr(self, 'bgm') or self.bgm is None:
                self.bgm = pygame.mixer.Sound(bgm_sound)
            self.bgm.set_volume(0 if self.muted else self.bgm_volume)

        except Exception as e:
            self.bgm = None
        
        # Set SFX volumes
        bounce_sound.set_volume(0 if self.muted else self.sfx_volume)
        explosion_sound.set_volume(0 if self.muted else self.sfx_volume)
        powerup_sound.set_volume(0 if self.muted else self.sfx_volume)
    
    def start_bgm(self):
        if not self.bgm_playing and self.bgm:
            # Stop any currently playing music first
            pygame.mixer.stop()
            # Play the BGM with loops
            self.bgm.play(loops=-1)  # -1 means loop indefinitely
            self.bgm_playing = True
            # Set volume again in case it was changed
            self.bgm.set_volume(0 if self.muted else self.bgm_volume)
    
    def stop_bgm(self):
        if self.bgm_playing:
            self.bgm.stop()
            self.bgm_playing = False
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.stop_bgm()  # Stop BGM when quitting
                show_exit_credits()  # Show credits before quitting
                return False
            elif event.type == pygame.KEYDOWN:
                if self.show_pause_menu:
                    menu_action = self.pause_menu.handle_input(event, self)
                    if menu_action == "resume":
                        self.show_pause_menu = False
                        self.paused = False
                    elif menu_action == "leaderboard":
                        self.pause_menu.showing_leaderboard = True
                    elif menu_action == "options":
                        # Initialize options menu with current settings
                        self.pause_menu.options_menu.bgm_volume = self.bgm_volume
                        self.pause_menu.options_menu.sfx_volume = self.sfx_volume
                        self.pause_menu.options_menu.muted = self.muted
                        self.pause_menu.showing_options = True
                    elif menu_action == "restart":
                        self.__init__()  # Reset the game
                        self.show_pause_menu = False
                        self.paused = False
                    elif menu_action == "exit":
                        show_exit_credits()  # Show credits before quitting
                        return False
                    elif menu_action == "cheat":
                        self.ball.manual_control = True
                    elif menu_action == "reset_scores":
                        self.leaderboard.scores = []
                        self.leaderboard.save_scores()
                        self.pause_menu.options_menu.reset_confirmation() 
                    elif menu_action == "update_volume":
                        # Update volumes from options menu
                        self.bgm_volume = self.pause_menu.options_menu.bgm_volume
                        self.sfx_volume = self.pause_menu.options_menu.sfx_volume
                        self.muted = self.pause_menu.options_menu.muted
                        
                        # Apply volume changes immediately
                        if self.bgm:
                            self.bgm.set_volume(0 if self.muted else self.bgm_volume)
                        bounce_sound.set_volume(0 if self.muted else self.sfx_volume)
                        explosion_sound.set_volume(0 if self.muted else self.sfx_volume)
                elif self.game_over:
                    
                    if event.key == pygame.K_r or event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if self.level == 10 and self.level_complete:
                            show_exit_credits()  # Only show credits when R is pressed after winning
                            return "main_menu"  # Signal to return to main menu
                        else:
                            self.__init__()  # Restart game
                    elif event.key == pygame.K_ESCAPE:
                        self.show_pause_menu = True
                        self.paused = True
                elif not self.paused and not self.game_over and not self.show_pause_menu:  # Added condition for not paused
                    if event.key == pygame.K_SPACE and not self.ball.active:
                        self.ball.active = True
                
                if event.key == pygame.K_ESCAPE:
                    if not self.game_over:
                        if self.pause_menu.showing_leaderboard or self.pause_menu.showing_options:
                            self.pause_menu.showing_leaderboard = False
                            self.pause_menu.showing_options = False
                        elif self.show_pause_menu:
                            self.show_pause_menu = False
                            self.paused = False
                        else:
                            self.show_pause_menu = True
                            self.paused = True
                    else:
                        self.show_pause_menu = True
                        self.paused = True
                elif event.key == pygame.K_p and not self.game_over and not self.show_pause_menu:
                    self.paused = not self.paused
                elif event.key == pygame.K_r and not self.show_pause_menu:
                    self.__init__()  # Restart game
                    # Explicitly reset paddle speed (though __init__ already does this)
                    self.paddle.set_speed(self.paddle.base_speed)
                elif event.key == pygame.K_o and not self.show_pause_menu:  # Options shortcut
                    self.show_pause_menu = True
                    self.paused = True
                    self.pause_menu.showing_options = True
                    # Initialize options menu with current settings
                    self.pause_menu.options_menu.bgm_volume = self.bgm_volume
                    self.pause_menu.options_menu.sfx_volume = self.sfx_volume
                    self.pause_menu.options_menu.muted = self.muted

                # Cheat Activation
                elif event.key == pygame.K_m:
                    # Start tracking mute press time
                    self.mute_press_time = pygame.time.get_ticks()
                    # Toggle mute state
                    self.muted = not self.muted
                    if self.bgm:
                        self.bgm.set_volume(0 if self.muted else self.bgm_volume)
                    bounce_sound.set_volume(0 if self.muted else self.sfx_volume)
                    explosion_sound.set_volume(0 if self.muted else self.sfx_volume)
                    powerup_sound.set_volume(0 if self.muted else self.sfx_volume)
                
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_m:
                        # Reset mute press time when M key is released
                        self.mute_press_time = 0
                        

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.show_pause_menu:
                    menu_action = self.pause_menu.handle_input(event)
                    if menu_action == "resume":
                        self.show_pause_menu = False
                        self.paused = False
                    elif menu_action == "leaderboard":
                        self.pause_menu.showing_leaderboard = True
                    elif menu_action == "options":
                        # Initialize options menu with current settings
                        self.pause_menu.options_menu.bgm_volume = self.bgm_volume
                        self.pause_menu.options_menu.sfx_volume = self.sfx_volume
                        self.pause_menu.options_menu.muted = self.muted
                        self.pause_menu.showing_options = True
                    elif menu_action == "restart":
                        self.__init__()  # Reset the game
                        self.show_pause_menu = False
                        self.paused = False
                    elif menu_action == "exit":
                        show_exit_credits()  # Show credits before quitting
                        return False
                    elif menu_action == "reset_scores":
                        self.leaderboard.scores = []
                        self.leaderboard.save_scores()
                        self.pause_menu.options_menu.reset_confirmation()
                    elif menu_action == "update_volume":
                        # Update volumes from options menu
                        self.bgm_volume = self.pause_menu.options_menu.bgm_volume
                        self.sfx_volume = self.pause_menu.options_menu.sfx_volume
                        self.muted = self.pause_menu.options_menu.muted
                        
                        # Apply volume changes immediately
                        self.bgm.set_volume(0 if self.muted else self.bgm_volume)
                        bounce_sound.set_volume(0 if self.muted else self.sfx_volume)
                        explosion_sound.set_volume(0 if self.muted else self.sfx_volume)

                elif self.game_over and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    restart_text_rect = pygame.Rect(
                        SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 60, 300, 30
                    )
                    if restart_text_rect.collidepoint(mouse_pos):
                        self.__init__()  # Restart game
        
        # Handle cheat activation/deactivation
        current_time = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()

        # Check if M key is being held down for 5 seconds
        if self.mute_press_time > 0 and (current_time - self.mute_press_time) >= 5000:
            # Toggle cheat state
            self.cheat_enabled = not self.cheat_enabled
            self.cheat_activation_time = current_time
            self.cheat_message_end_time = current_time + 2000  # Show message for 2 seconds
            self.mute_press_time = 0  # Reset to prevent repeated toggling

        # Only allow CTRL manual control if cheat is currently enabled
        if self.cheat_enabled:
            if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                self.ball.manual_control = True
            else:
                self.ball.manual_control = False
        else:
            self.ball.manual_control = False
        
        return True
    
    def draw(self, surface):
        surface.fill(BLACK)
        
        # Draw game elements
        self.paddle.draw(surface)
        self.ball.draw(surface)
        
        for brick in self.bricks:
            brick.draw(surface)
        
        for powerup in self.powerups:
            powerup.draw(surface)
        
        # Draw UI
        font = pygame.font.Font(None, 36)
        score_text = font.render(f'Score: {self.score}', True, WHITE)
        lives_text = font.render(f'Lives: {self.lives}', True, WHITE)
        level_text = font.render(f'Level: {self.level}/10', True, WHITE)
        high_score = self.leaderboard.get_high_score()
        high_score_text = font.render(f'High Score: {high_score}', True, YELLOW)
        
        surface.blit(score_text, (10, 10))
        surface.blit(lives_text, (10, 50))
        surface.blit(level_text, (10, 90))
        surface.blit(high_score_text, (10, 130))
        
        # Draw powerup legend
        legend_font = pygame.font.Font(None, 20)
        legends = [
            ("Green: Extra Life", GREEN),
            ("Yellow: Paddle Expand", YELLOW),
            ("Blue: Ball Slow Down", BLUE)
        ]
        for i, (text, color) in enumerate(legends):
            legend_text = legend_font.render(text, True, color)
            surface.blit(legend_text, (10, 180 + i * 22))
        
        # Draw controls reminder
        controls_font = pygame.font.Font(None, 24)
        controls = [
            "Movement- Left/Right:A/D",
            "SPACE: Launch Ball",
            "P: Pause",
            "ESC: Menu",
            "R: Restart",
            "O: Options"
        ]
        for i, control in enumerate(controls):
            text = controls_font.render(control, True, WHITE)
            surface.blit(text, (SCREEN_WIDTH - 220, 10 + i * 25))
        
        if self.show_pause_menu:
            self.pause_menu.draw(surface, self.leaderboard, self)
        elif self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            surface.blit(overlay, (0, 0))
            
            big_font = pygame.font.Font(None, 72)
            small_font = pygame.font.Font(None, 36)
            
            # Show different message if all levels completed
            if self.level == 10 and self.level_complete:
                game_over_text = big_font.render('Victory secured — you dominated the game!', True, GREEN)
            else:
                game_over_text = big_font.render('GAME OVER', True, RED)
                
            score_text = small_font.render(f'Final Score: {self.score}', True, WHITE)
            level_text = small_font.render(f'Level Reached: {self.level}', True, WHITE)
            
            if self.score == self.leaderboard.get_high_score() and self.score > 0:
                new_record_text = small_font.render('NEW HIGH SCORE!', True, YELLOW)
                surface.blit(new_record_text, new_record_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80)))
            
            restart_text = small_font.render('Press Space to Continue', True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70))
            surface.blit(restart_text, restart_rect)
            
            surface.blit(game_over_text, game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40)))
            surface.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))
            surface.blit(level_text, level_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30)))
        elif self.level_complete:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            surface.blit(overlay, (0, 0))
            
            big_font = pygame.font.Font(None, 72)
            small_font = pygame.font.Font(None, 36)
            
            level_complete_text = big_font.render(f'LEVEL {self.level} COMPLETE!', True, GREEN)
            next_text = small_font.render('Press SPACE to continue to next level', True, WHITE)
            
            surface.blit(level_complete_text, level_complete_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40)))
            surface.blit(next_text, next_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 190)))
        elif self.paused and not self.show_pause_menu:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            surface.blit(overlay, (0, 0))
            
            big_font = pygame.font.Font(None, 72)
            small_font = pygame.font.Font(None, 36)
            
            pause_text = big_font.render('PAUSED', True, YELLOW)
            resume_text = small_font.render('Press P to resume or ESC for menu', True, WHITE)
            
            surface.blit(pause_text, pause_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40)))
            surface.blit(resume_text, resume_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20)))
        
        # Draw launch prompt if ball is inactive
        if not self.ball.active and not self.game_over and not self.level_complete and not self.paused:
            small_font = pygame.font.Font(None, 36)
            launch_text = small_font.render('Press SPACE to launch ball', True, WHITE)
            surface.blit(launch_text, launch_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 190)))

        current_time = pygame.time.get_ticks()
        if current_time < self.cheat_message_end_time:
            if self.cheat_enabled:
                cheat_text = font.render('CHEAT ACTIVATED', True, GREEN)
            else:
                cheat_text = font.render('CHEAT DEACTIVATED', True, RED)
            surface.blit(cheat_text, (SCREEN_WIDTH//2 - 110, SCREEN_HEIGHT - 100))

def show_exit_credits():
    """Display exit credits sequence with scrolling credits and dedicated outro music"""
    # Stop any currently playing sounds
    pygame.mixer.stop()
    
    # Load outro music
    outro_music_path = get_data_path("outro_music.wav")
    try:
        outro_music = pygame.mixer.Sound(outro_music_path)
        outro_music.set_volume(0.7)
        outro_music.play(loops=-1)
    except:
        outro_music = None
    
    # Initialize parameters
    rolling_text_y = SCREEN_HEIGHT  # Start below screen
    rolling_text_speed = 2  # Pixels per frame
    total_duration = 14000  # 14 seconds total
    start_time = pygame.time.get_ticks()
    
    # Define credits content
    credit_font = pygame.font.Font(None, 32)
    credits = [
        "BRICK BREAKER",
        "",
        "Game Developed By",
        "Desk Devil Studios",
        "",
        "Programming",
        "Aryan Bhatt",
        "",
        "Artwork",
        "Aryan Bhatt",
        "",
        "Sound Design",
        "Aryan Bhatt in association with Pixabay",
        "",
        "Special Thanks To",
        "Python",
        "",
        "Pygame Library",
        "",
        "Pixabay for Sound Effects",
        "",
        "© 2025 Desk Devil Studios",
        "All Rights Reserved",
        ""
    ]
    
    # Keys that should trigger skipping the credits
    skip_keys = {
        pygame.K_TAB, pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE
    }
    # Add all alphabet and number keys
    skip_keys.update(range(pygame.K_a, pygame.K_z + 1))  # a-z
    skip_keys.update(range(pygame.K_0, pygame.K_9 + 1))  # 0-9
    
    # Main loop
    running = True
    while running:
        current_time = pygame.time.get_ticks()
        elapsed = current_time - start_time
        
        # Check if total duration has been reached
        if elapsed >= total_duration:
            if outro_music:
                outro_music.stop()
            return "main_menu"
        
        # Handle events (allow skipping only for specific keys)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if outro_music:
                    outro_music.stop()
                return "quit"
            elif event.type == pygame.KEYDOWN:
                # Skip only if it's one of our allowed keys
                if event.key in skip_keys:
                    if outro_music:
                        outro_music.stop()
                    return "main_menu"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Also allow skipping with mouse clicks
                if outro_music:
                    outro_music.stop()
                return "main_menu"
        
        # Update credits scrolling
        rolling_text_y -= rolling_text_speed
        if rolling_text_y < -2000:  # End when credits scroll past
            if outro_music:
                outro_music.stop()
            return "main_menu"
        
        # Draw everything
        screen.fill(BLACK)
        
        # Draw scrolling credits
        y_pos = rolling_text_y
        for credit in credits:
            if credit:
                text = credit_font.render(credit, True, WHITE)
                text_rect = text.get_rect(center=(SCREEN_WIDTH//2, y_pos))
                screen.blit(text, text_rect)
            y_pos += 40
        
        pygame.display.flip()
        clock.tick(FPS)
    
    # Clean up music if we exit early
    if outro_music:
        outro_music.stop()

def main():
    try:
        # Initialize sound system
        pygame.mixer.init()
        
        # Stop any currently playing sounds
        pygame.mixer.stop()
        
        # Load and play intro music
        try:
            intro_music = pygame.mixer.Sound(get_data_path("intro_music.wav"))
            intro_music.set_volume(1.0)
            intro_music.play(loops=-1)
        except:
            intro_music = None
        
        leaderboard = LeaderBoard()
        
        # First show logo screen with credits
        logo_screen = LogoScreen()
        logo_start_time = pygame.time.get_ticks()
        logo_duration = 15000  # 26 seconds for credits
        
        while True:
            current_time = pygame.time.get_ticks()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if intro_music:
                        intro_music.stop()
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    # Allow skipping the logo screen
                    logo_screen.show_credits = True
                    logo_start_time = current_time - logo_duration  # Force completion
            
            # Update logo screen
            if logo_screen.update():
                break
            
            # Check if 26 seconds have passed
            if current_time - logo_start_time >= logo_duration:
                break
            
            # Draw logo screen
            logo_screen.draw(screen)
            pygame.display.flip()
            clock.tick(FPS)
        
        # Then show title screen
        title_screen = TitleScreen(leaderboard)
        
        while title_screen.show_title:
            for event in pygame.event.get():
                result = title_screen.handle_events(event)
                if result is False:
                    if intro_music:
                        intro_music.stop()
                    pygame.quit()
                    sys.exit()
                elif result is True:
                    # Stop intro music when game starts
                    if intro_music:
                        intro_music.stop()
                    title_screen.show_title = False
                    break
            
            title_screen.update()
            title_screen.draw(screen)
            pygame.display.flip()
            clock.tick(FPS)
        
        # Finally start the game
        game = Game()
        game.leaderboard = leaderboard
        
        while True:
            # Handle game events
            result = game.handle_events()
            if result == "main_menu":
                # Show title screen again
                title_screen = TitleScreen(leaderboard)
                title_screen.show_title = True
                # Stop any game music and play intro music again
                game.stop_bgm()
                try:
                    intro_music = pygame.mixer.Sound(get_data_path("intro_music.wav"))
                    intro_music.set_volume(0.7)
                    intro_music.play(loops=-1)
                except:
                    pass
                
                # Show title screen
                while title_screen.show_title:
                    for event in pygame.event.get():
                        result = title_screen.handle_events(event)
                        if result is False:
                            if intro_music:
                                intro_music.stop()
                            pygame.quit()
                            sys.exit()
                        elif result is True:
                            # Stop intro music when game starts
                            if intro_music:
                                intro_music.stop()
                            title_screen.show_title = False
                            break
                    
                    title_screen.update()
                    title_screen.draw(screen)
                    pygame.display.flip()
                    clock.tick(FPS)
                
                # Start a new game
                game = Game()
                game.leaderboard = leaderboard
                continue
            elif result is False:
                break
            
            # Handle game updates
            if not game.paused and not game.show_pause_menu:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    game.paddle.move("left")
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    game.paddle.move("right")
            
            if game.level_complete and pygame.key.get_pressed()[pygame.K_SPACE]:
                level_result = game.next_level()
                if level_result == "game_won":
                    # Wait for R key to be pressed to show credits
                    pass
            
            game.update()
            game.draw(screen)
            pygame.display.flip()
            clock.tick(FPS)
        
        game.stop_bgm()
        pygame.quit()
        sys.exit()

    except Exception as e:
        print(f"Error: {e}")
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    main()