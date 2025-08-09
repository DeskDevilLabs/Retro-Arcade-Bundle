import pygame
import sys
import random
import json
import math
import os
from datetime import datetime


pygame.mixer.init()

def resource_path(filename):
    """Get absolute path to resource, works for dev and for PyInstaller exe"""
    if getattr(sys, 'frozen', False):  # Running as compiled .exe
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)

laser_soundpath = resource_path("laser.wav")
laser_sound = pygame.mixer.Sound(laser_soundpath)
laser_sound.set_volume(0.8)

explosion_soundpath = resource_path("explosion.wav")
explosion_sound = pygame.mixer.Sound(explosion_soundpath)
explosion_sound.set_volume(0.8)

game_over_soundpath = resource_path("game_over.wav")
game_over_sound = pygame.mixer.Sound(game_over_soundpath)
game_over_sound.set_volume(1)  # Set volume

# Game BGM
game_bg_soundpath = resource_path("space_invader_bgm.wav")
game_bg = pygame.mixer.Sound(game_bg_soundpath)
game_bg.set_volume(0.4)  # Set volume
game_bg_playing = False  # Track BGM state

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 1366
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Space Invaders')

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 100, 255)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50)

# Game settings
FPS = 60
clock = pygame.time.Clock()


def is_new_high_score(self):
    """Check if the current score is the highest in the leaderboard"""
    if not self.leaderboard_manager.scores:
        return True  # No scores yet, so this is automatically the highest
    
    top_score = max(entry['score'] for entry in self.leaderboard_manager.scores)
    return self.score > top_score


class LeaderboardManager:
    def __init__(self):
        self._determine_file_path()
        self.scores = self.load_scores()

    def _determine_file_path(self):
        """Determine the appropriate path for the leaderboard file"""
        try:
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                if os.name == 'nt':  # Windows
                    appdata = os.getenv('APPDATA')
                    save_dir = os.path.join(appdata, 'SpaceInvaders')
                else:  # Mac/Linux
                    home = os.path.expanduser('~')
                    save_dir = os.path.join(home, '.spaceinvaders')
                
                # Create directory if it doesn't exist
                os.makedirs(save_dir, exist_ok=True)
                self.leaderboard_file = os.path.join(save_dir, "leaderboard.json")
            else:
                # Running in development
                base_dir = os.path.dirname(os.path.abspath(__file__))
                self.leaderboard_file = os.path.join(base_dir, "space_invaders_leaderboard.json")
                
            
        except Exception as e:
            self.leaderboard_file = "leaderboard_fallback.json"

    def load_scores(self):
        """Load scores from the leaderboard file"""
        try:
            if os.path.exists(self.leaderboard_file):
                with open(self.leaderboard_file, 'r') as f:
                    try:
                        scores = json.load(f)
                        
                        return scores
                    except json.JSONDecodeError as je:
                        
                        return self._handle_corrupt_file()
            else:
                
                return []
        except Exception as e:
            return []

    def _handle_corrupt_file(self):
        """Handle cases where the leaderboard file is corrupt"""
        try:
            # Try to rename the corrupt file for debugging
            corrupt_path = f"{self.leaderboard_file}.corrupt"
            if os.path.exists(corrupt_path):
                os.remove(corrupt_path)
            os.rename(self.leaderboard_file, corrupt_path)
            
        except Exception as e:
            pass
        
        return []

    def save_scores(self):
        """Save scores to the leaderboard file"""
        try:
            # First try saving to primary location
            self._save_to_file(self.leaderboard_file)
        except Exception as primary_error:
            pass
            
            # Try saving to fallback location
            fallback_path = os.path.join(os.path.expanduser('~'), 'space_invaders_leaderboard_fallback.json')
            try:
                self._save_to_file(fallback_path)
                
            except Exception as fallback_error:
                
                raise RuntimeError("Could not save leaderboard to any location")

    def _save_to_file(self, file_path):
        """Internal method to handle actual file saving"""
        temp_path = f"{file_path}.tmp"
        
        # Write to temporary file first
        with open(temp_path, 'w') as f:
            json.dump(self.scores, f, indent=2)
        
        # Then rename to final file (atomic operation)
        if os.path.exists(file_path):
            os.remove(file_path)
        os.rename(temp_path, file_path)
        
        

    def add_score(self, score, level):
        """Add a new score to the leaderboard"""
        if not isinstance(score, int) or not isinstance(level, int):
            return False
        
        entry = {
            'score': score,
            'level': level,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.scores.append(entry)
        # Sort by score (descending) then by level (descending)
        self.scores.sort(key=lambda x: (-x['score'], -x['level']))
        # Keep only top 10
        self.scores = self.scores[:10]
        
        try:
            self.save_scores()
            
            return True
        except Exception as e:
            
            return False
    
    def get_top_scores(self, limit=10):
        """Get the top scores from the leaderboard"""
        return self.scores[:limit]
    
    def is_high_score(self, score):
        """Check if a score would qualify for the leaderboard"""
        if not self.scores:  # If no scores exist yet
            return True
        
        # Check if score is higher than the lowest score in top 10
        min_score = min(entry['score'] for entry in self.scores)
        return len(self.scores) < 10 or score > min_score
        
    def reset_scores(self):
        """Reset all scores in the leaderboard"""
        self.scores = []
        try:
            self.save_scores()
            
            return True
        except Exception as e:
            
            return False

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.font = pygame.font.Font(None, 36)
        
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)
        
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

class ToggleButton(Button):
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=WHITE, is_on=False):
        super().__init__(x, y, width, height, text, color, hover_color, text_color)
        self.is_on = is_on
        
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)
        
        status = "ON" if self.is_on else "OFF"
        full_text = f"{self.text}: {status}"
        text_surf = self.font.render(full_text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def toggle(self):
        self.is_on = not self.is_on
        return self.is_on

class Player:
    def __init__(self):
        self.width = 60
        self.height = 40
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT - self.height - 20
        self.speed = 8
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.is_hit = False  # Track if player is currently in hit state
        self.hit_timer = 0   # Timer for hit animation
        self.hit_duration = 30  # Duration of hit animation (in frames)
        self.is_invincible = False  # Track invincibility state
        self.death_animation_timer = 0  # New: Timer for death animation
        self.is_dying = False  # New: Track if player is in death animation
        self.death_particles = []  # New: For particle effects
        self.death_stage = 0  # New: Track which stage of death animation we're in
        
    def update(self, can_move=True):
        if not can_move or self.is_dying:  # Modified: Don't move during death animation
            return
            
        # Update hit animation timer
        if self.is_hit:
            self.hit_timer -= 1
            if self.hit_timer <= 0:
                self.is_hit = False
                
        # Check for Shift key to toggle invincibility
        keys = pygame.key.get_pressed()
        self.is_invincible = keys[pygame.K_RSHIFT]
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
            
        # Keep player on screen
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        self.rect.x = self.x
        
    def draw(self, screen):
        if self.is_dying:
            # Update death animation
            self.death_animation_timer -= 1
            
            # Update particles
            for particle in self.death_particles[:]:
                particle['x'] += particle['dx']
                particle['y'] += particle['dy']
                particle['lifetime'] -= 1
                if particle['lifetime'] <= 0:
                    self.death_particles.remove(particle)
            
            # Draw particles
            for particle in self.death_particles:
                pygame.draw.circle(
                    screen, 
                    particle['color'],
                    (int(particle['x']), int(particle['y'])),
                    particle['size']
                )
            
            # Draw different stages of explosion
            if self.death_animation_timer > 40:  # Initial flash
                radius = int((60 - self.death_animation_timer) * 3)
                pygame.draw.circle(screen, WHITE, 
                                (self.x + self.width//2, self.y + self.height//2), 
                                radius)
            elif self.death_animation_timer > 20:  # Main explosion
                radius = int((40 - self.death_animation_timer) * 4)
                pygame.draw.circle(screen, ORANGE, 
                                (self.x + self.width//2, self.y + self.height//2), 
                                radius)
                pygame.draw.circle(screen, YELLOW, 
                                (self.x + self.width//2, self.y + self.height//2), 
                                radius - 10)
            else:  # Fading out
                alpha = int(255 * (self.death_animation_timer / 20))
                s = pygame.Surface((100, 100), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 165, 0, alpha), (50, 50), 30)
                screen.blit(s, (self.x + self.width//2 - 50, self.y + self.height//2 - 50))
            
            # Add new particles throughout the animation
            if random.random() < 0.3 and self.death_animation_timer > 10:
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(0.5, 3)
                size = random.randint(1, 4)
                lifetime = random.randint(10, 30)
                self.death_particles.append({
                    'x': self.x + self.width//2,
                    'y': self.y + self.height//2,
                    'dx': math.cos(angle) * speed,
                    'dy': math.sin(angle) * speed,
                    'size': size,
                    'lifetime': lifetime,
                    'color': random.choice([RED, ORANGE, YELLOW])
                })
            
            return
            
        # Flash between red and normal colors during hit
        if self.is_hit and self.hit_timer % 10 < 5:  # Flash every 5 frames
            base_color = RED
        else:
            base_color = GREEN
            
        # Draw invincibility effect
        if self.is_invincible:
            # Create a pulsing effect for invincibility
            pulse = int((pygame.time.get_ticks() % 1000) / 1000 * 255)
            invincible_color = (min(255, pulse), min(255, 255 - pulse), 0)
            pygame.draw.rect(screen, invincible_color, self.rect.inflate(10, 10), 2)
            
        pygame.draw.rect(screen, base_color, self.rect)
        # Draw a simple spaceship shape
        pygame.draw.polygon(screen, WHITE, [
            (self.x + self.width//2, self.y),
            (self.x + 10, self.y + self.height),
            (self.x + self.width - 10, self.y + self.height)
        ])
        
    def trigger_hit(self):
        """Start the hit animation"""
        self.is_hit = True
        self.hit_timer = self.hit_duration
        
    def trigger_death(self):
        """Start the death animation"""
        self.is_dying = True
        self.death_animation_timer = 60  # 1 second at 60 FPS
        self.death_stage = 0
        self.death_particles = []  # Clear any old particles
        
        # Create initial explosion particles
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 5)
            size = random.randint(2, 6)
            lifetime = random.randint(30, 60)
            self.death_particles.append({
                'x': self.x + self.width//2,
                'y': self.y + self.height//2,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'size': size,
                'lifetime': lifetime,
                'color': random.choice([RED, ORANGE, YELLOW, WHITE])
            })

class Bullet:
    def __init__(self, x, y, speed, color=WHITE):
        self.x = x
        self.y = y
        self.speed = speed
        self.width = 4
        self.height = 10
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = color
        
    def update(self):
        self.y += self.speed
        self.rect.y = self.y
        
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

class Invader:
    def __init__(self, x, y, invader_type=1):
        self.width = 40
        self.height = 30
        self.x = x
        self.y = y
        self.type = invader_type
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.health = 1 if invader_type <= 2 else 2 if invader_type <= 4 else 3
        self.max_health = self.health
        self.points = 10 * invader_type
        self.is_hit = False  # Track if invader is currently in hit state
        self.hit_timer = 0   # Timer for hit animation
        self.hit_duration = 15  # Duration of hit animation (shorter than player's)
        
    def update(self, dx, dy):
        self.x += dx
        self.y += dy
        self.rect.x = self.x
        self.rect.y = self.y
        
        # Update hit animation timer
        if self.is_hit:
            self.hit_timer -= 1
            if self.hit_timer <= 0:
                self.is_hit = False
                
    def hit(self):
        """Start the hit animation and reduce health"""
        self.is_hit = True
        self.hit_timer = self.hit_duration
        self.health -= 1
        return self.health <= 0
        
    def draw(self, screen):
        colors = [RED, YELLOW, BLUE, PURPLE, ORANGE]
        color = colors[min(self.type - 1, 4)]
        
        # Draw invader with health indication
        if self.health < self.max_health:
            # Damaged invader - darker color
            color = tuple(c // 2 for c in color)
            
        # Flash white when hit
        if self.is_hit and self.hit_timer % 5 < 3:  # Faster flash than player
            color = WHITE
            
        pygame.draw.rect(screen, color, self.rect)
        
        # Draw simple invader shape based on type
        if self.type == 1:
            pygame.draw.rect(screen, BLACK if self.is_hit else WHITE, (self.x + 8, self.y + 5, 24, 10))
            pygame.draw.rect(screen, BLACK if self.is_hit else WHITE, (self.x + 5, self.y + 15, 10, 8))
            pygame.draw.rect(screen, BLACK if self.is_hit else WHITE, (self.x + 25, self.y + 15, 10, 8))
        elif self.type == 2:
            pygame.draw.rect(screen, BLACK if self.is_hit else WHITE, (self.x + 5, self.y + 5, 30, 15))
            pygame.draw.rect(screen, BLACK if self.is_hit else WHITE, (self.x + 10, self.y + 20, 20, 5))
        elif self.type == 3:
            pygame.draw.rect(screen, BLACK if self.is_hit else WHITE, (self.x + 3, self.y + 3, 34, 20))
            pygame.draw.rect(screen, BLACK if self.is_hit else WHITE, (self.x + 8, self.y + 23, 8, 4))
            pygame.draw.rect(screen, BLACK if self.is_hit else WHITE, (self.x + 24, self.y + 23, 8, 4))
        elif self.type == 4:
            pygame.draw.ellipse(screen, BLACK if self.is_hit else WHITE, (self.x + 5, self.y + 5, 30, 20))
            pygame.draw.rect(screen, BLACK if self.is_hit else WHITE, (self.x + 15, self.y + 25, 10, 3))
        else:  # Boss type
            pygame.draw.ellipse(screen, BLACK if self.is_hit else WHITE, (self.x + 2, self.y + 2, 36, 26))
            pygame.draw.rect(screen, BLACK if self.is_hit else WHITE, (self.x + 5, self.y + 10, 8, 8))
            pygame.draw.rect(screen, BLACK if self.is_hit else WHITE, (self.x + 27, self.y + 10, 8, 8))

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
            pygame.K_RETURN, pygame.K_ESCAPE
        }

    def load_logos(self):
        # Try to load multiple logo images
        logo_paths = [
            resource_path("DD Lab1.png"),
            (resource_path("logo1.png"), resource_path("logo2.jpg")),
            resource_path("space_invaders.jpg")
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

class Game:
    def __init__(self):
        self.player = Player()
        self.player_bullets = []
        self.invader_bullets = []
        self.invaders = []
        self.score = 0
        self.lives = 10
        self.level = 1
        self.max_level = 10
        self.game_over = False
        self.won = False
        self.level_complete = False
        self.invader_speed_x = 2
        self.invader_speed_y = 40
        self.invader_direction = 1
        self.last_invader_shot = 0
        self.invader_shoot_delay = 60
        self.level_start_time = 0
        self.show_level_text = False
        self.level_text_timer = 180  # 3 seconds at 60 FPS
        self.paused = False
        self.show_leaderboard = False
        self.show_options = False
        self.mute_sounds = False
        self.mute_bgm = False
        self.leaderboard_manager = LeaderboardManager()
        self.score_submitted = False
        self.title_screen = True
        self.fullscreen = True
        self.show_confirmation = False
        self.confirmation_buttons = []
        self.show_exit_confirmation = False
        self.death_delay = 120  # 1 second delay at 60 FPS
        self.death_timer = 0
        

    # Level configurations
        self.level_configs = {
            1: {
                'rows': 4, 'cols': 8, 'types': [1, 1], 'speed': 1, 'shoot_chance': 0.02,
                'name': 'LEVEL 1: Basic Formation',
                'bullets_per_shot': 1
            },
            2: {
                'rows': 5, 'cols': 9, 'types': [1, 1, 2], 'speed': 2, 'shoot_chance': 0.02,
                'name': 'LEVEL 2: Mixed Forces',
                'bullets_per_shot': 1
            },
            3: {
                'rows': 5, 'cols': 10, 'types': [1, 2, 2, 3], 'speed': 3, 'shoot_chance': 0.025,
                'name': 'LEVEL 3: Heavy Resistance',
                'bullets_per_shot': 1
            },
            4: {
                'rows': 6, 'cols': 10, 'types': [2, 2, 3, 3, 4], 'speed': 3, 'shoot_chance': 0.025,
                'name': 'LEVEL 4: Elite Squadron',
                'bullets_per_shot': 1
            },
            5: {
                'rows': 6, 'cols': 12, 'types': [3, 3, 4, 4, 5, 5], 'speed': 3.5, 'shoot_chance': 0.025,
                'name': 'LEVEL 5: BOSS WAVE',
                'bullets_per_shot': 2
            },
            6: {
                'rows': 7, 'cols': 12, 'types': [3, 3, 4, 4, 5, 5], 'speed': 3.7, 'shoot_chance': 0.029,
                'name': 'LEVEL 6: ARMADA APPROACHES',
                'bullets_per_shot': 3
            },
            7: {
                'rows': 7, 'cols': 12, 'types': [3, 4, 4, 4, 5, 5], 'speed': 3.7, 'shoot_chance': 0.030,
                'name': 'LEVEL 7: DANGER ZONE',
                'bullets_per_shot': 3
            },
            8: {
                'rows': 8, 'cols': 13, 'types': [4, 4, 4, 4, 4, 5], 'speed': 3.9, 'shoot_chance': 0.031,
                'name': 'LEVEL 8: ARMAGEDDON',
                'bullets_per_shot': 4
            },
            9: {
                'rows': 8, 'cols': 13, 'types': [4, 4, 4, 4, 5, 5], 'speed': 4.1, 'shoot_chance': 0.032,
                'name': 'LEVEL 9: FINAL DEFENSE',
                'bullets_per_shot': 4
            },
            10: {
                'rows': 9, 'cols': 13, 'types': [4, 4, 4, 5, 5, 5], 'speed': 4.4, 'shoot_chance': 0.035,
                'name': 'LEVEL 10: GALACTIC SHOWDOWN',
                'bullets_per_shot': 5
            }
        }
        
        # Initialize UI elements
        self.init_ui()  

    def init_ui(self):
        button_width = 200
        button_height = 50
        center_x = SCREEN_WIDTH // 2 - button_width // 2
        button_spacing = 70
        start_y = SCREEN_HEIGHT // 2 - 120
        
        # Pause menu buttons
        self.resume_button = Button(center_x, start_y, button_width, button_height, 
                                   "Resume", GRAY, LIGHT_GRAY)
        self.leaderboard_button = Button(center_x, start_y + button_spacing, button_width, button_height, 
                                        "Leaderboard", BLUE, CYAN)
        self.options_button = Button(center_x, start_y + button_spacing * 2, button_width, button_height,
                                   "Options", PURPLE, (200, 100, 200))
        self.restart_button = Button(center_x, start_y + button_spacing * 3, button_width, button_height, 
                                    "Restart", ORANGE, YELLOW)
        self.quit_button = Button(center_x, start_y + button_spacing * 4, button_width, button_height, 
                                 "Main Menu", RED, (255, 100, 100))
        
        # Leaderboard buttons
        self.back_button = Button(center_x, SCREEN_HEIGHT - 60, button_width, button_height,
                                "Back", GRAY, LIGHT_GRAY)
        
        # Options menu buttons
        self.mute_sounds_button = ToggleButton(center_x, start_y + button_spacing, button_width, button_height,
                                               "Sounds", GRAY, LIGHT_GRAY, is_on=not self.mute_sounds)
        self.mute_bgm_button = ToggleButton(center_x, start_y + button_spacing * 2, button_width, button_height,
                                            "BGM", GRAY, LIGHT_GRAY, is_on=not self.mute_bgm)
        self.fullscreen_button = ToggleButton(center_x, start_y + button_spacing * 3, button_width, button_height,
                                              "Fullscreen", GRAY, LIGHT_GRAY, is_on=self.fullscreen)
        
        self.reset_scores_button = Button(center_x, start_y + button_spacing * 4, button_width, button_height,
                                          "Reset Scores", RED, (255, 100, 100))

        self.options_back_button = Button(center_x, start_y + button_spacing * 5, button_width, button_height,
                                          "Back", GRAY, LIGHT_GRAY)
        
        # Title screen buttons
        self.start_button = Button(center_x, SCREEN_HEIGHT // 2 + 50, button_width, button_height,
                                   "Start Game", GREEN, (100, 255, 100))
        self.title_leaderboard_button = Button(center_x, SCREEN_HEIGHT // 2 + 50 + button_spacing, 
                                               button_width, button_height, "Leaderboard", BLUE, CYAN)
        self.title_options_button = Button(center_x, SCREEN_HEIGHT // 2 + 50 + button_spacing * 2,
                                            button_width, button_height, "Options", PURPLE, (200, 100, 200))
        self.title_quit_button = Button(center_x, SCREEN_HEIGHT // 2 + 50 + button_spacing * 3,
                                        button_width, button_height, "Quit", RED, (255, 100, 100))

        # Confirmation dialog buttons
        self.yes_button = Button(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 60, 120, 50, 
                               "YES", RED, (255, 100, 100))
        self.no_button = Button(SCREEN_WIDTH//2 + 30, SCREEN_HEIGHT//2 + 60, 120, 50,
                              "NO", GREEN, (100, 255, 100))
        
        self.create_invaders()

    def toggle_fullscreen(self):
        global screen, SCREEN_WIDTH, SCREEN_HEIGHT
        self.fullscreen = not self.fullscreen
        
        if self.fullscreen:
            info = pygame.display.Info()
            screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        else:
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        
        SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
        self.reposition_ui()

    def create_invaders(self):
        self.invaders = []
        config = self.level_configs[self.level]
        
        for row in range(config['rows']):
            for col in range(config['cols']):
                x = 100 + col * 70
                y = 80 + row * 50
                
                type_index = min(row, len(config['types']) - 1)
                invader_type = config['types'][type_index]
                
                self.invaders.append(Invader(x, y, invader_type))
        
        self.invader_speed_x = config['speed']
        self.invader_shoot_chance = config['shoot_chance']

    def reposition_ui(self):
        button_width = 200
        button_height = 50
        center_x = SCREEN_WIDTH // 2 - button_width // 2
        button_spacing = 70
        start_y = SCREEN_HEIGHT // 2 - 120
        
        # Reposition all buttons
        self.resume_button.rect = pygame.Rect(center_x, start_y, button_width, button_height)
        self.leaderboard_button.rect = pygame.Rect(center_x, start_y + button_spacing, button_width, button_height)
        self.options_button.rect = pygame.Rect(center_x, start_y + button_spacing * 2, button_width, button_height)
        self.restart_button.rect = pygame.Rect(center_x, start_y + button_spacing * 3, button_width, button_height)
        self.quit_button.rect = pygame.Rect(center_x, start_y + button_spacing * 4, button_width, button_height)
                
        self.back_button.rect = pygame.Rect(center_x, SCREEN_HEIGHT - 60, button_width, button_height)
        
        # Add the reset scores button to options position
        self.reset_scores_button.rect = pygame.Rect(center_x, start_y + button_spacing * 4, button_width, button_height)
        self.options_back_button.rect = pygame.Rect(center_x, start_y + button_spacing * 5, button_width, button_height)
        
        self.start_button.rect = pygame.Rect(center_x, SCREEN_HEIGHT // 2 + 50, button_width, button_height)
        self.title_leaderboard_button.rect = pygame.Rect(center_x, SCREEN_HEIGHT // 2 + 50 + button_spacing, 
                                                         button_width, button_height)
        self.title_options_button.rect = pygame.Rect(center_x, SCREEN_HEIGHT // 2 + 50 + button_spacing * 2,
                                                     button_width, button_height)
        self.title_quit_button.rect = pygame.Rect(center_x, SCREEN_HEIGHT // 2 + 50 + button_spacing * 3,
                                                  button_width, button_height)
        
        self.yes_button.rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 60, 120, 50)
        self.no_button.rect = pygame.Rect(SCREEN_WIDTH//2 + 30, SCREEN_HEIGHT//2 + 60, 120, 50)

    def handle_events(self):
        global game_bg_playing, SCREEN_WIDTH, SCREEN_HEIGHT, screen
        ctrl_pressed = pygame.key.get_pressed()[pygame.K_RCTRL]
        alt_pressed = pygame.key.get_pressed()[pygame.K_RALT]
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Pause the game
                self.paused = True
                self.show_exit_confirmation = True

            elif event.type == pygame.VIDEORESIZE:
                if not self.fullscreen:
                    SCREEN_WIDTH, SCREEN_HEIGHT = event.size
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                    self.reposition_ui()
                            
            elif event.type == pygame.KEYDOWN:
                if self.title_screen:
                    if (event.key == pygame.K_RETURN or event.key == pygame.K_SPACE) and not (self.show_leaderboard or self.show_options):
                        self.title_screen = False
                        self.level_start_time = 0
                        self.show_level_text = True
                        self.level_text_timer = 180
                    elif event.key == pygame.K_ESCAPE:
                        if self.show_leaderboard or self.show_options:
                            self.show_leaderboard = False
                            self.show_options = False
                else:
                    if (event.key == pygame.K_SPACE and not self.game_over and not self.level_complete 
                        and not self.paused and not self.show_level_text and not self.show_leaderboard 
                        and not self.show_options):
                        if ctrl_pressed:
                            # Rapid fire cheat code
                            for offset in range(-100, 101, 10):
                                bullet_x = self.player.x + self.player.width // 2 - 2 + offset
                                bullet_y = self.player.y
                                self.player_bullets.append(Bullet(bullet_x, bullet_y, -12))
                            if not self.mute_sounds:
                                laser_sound.play()
                        else:
                            self.shoot_player_bullet()
                    elif event.key == pygame.K_r and (self.game_over or self.won):
                        self.restart_game()
                    elif event.key == pygame.K_RETURN and self.level_complete and not self.won:
                        self.next_level()
                    elif event.key == pygame.K_ESCAPE:
                        if self.show_options:
                            self.show_options = False
                        elif self.show_leaderboard:
                            self.show_leaderboard = False
                        elif self.paused:
                            self.paused = False
                        elif not (self.game_over or self.won or self.level_complete or self.show_level_text):
                            self.paused = True
                        elif self.game_over or self.won:
                            self.__init__()
                            self.title_screen = True
                        elif self.game_over or self.won:
                            self.__init__()
                            self.title_screen = True
                        elif (event.key == pygame.K_RETURN or event.key == pygame.K_SPACE) and self.won:
                            # Return to main menu when won
                            self.__init__()
                            self.title_screen = True
            
            # Handle mouse button down events
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button only
                mouse_pos = pygame.mouse.get_pos()
                
                # Handle confirmation dialog first if active
                if self.show_confirmation:
                    if self.yes_button.rect.collidepoint(mouse_pos):
                        self.leaderboard_manager.reset_scores()
                        self.show_confirmation = False
                        continue  # Skip other checks after confirmation
                    elif self.no_button.rect.collidepoint(mouse_pos):
                        self.show_confirmation = False
                    continue  # Skip other checks after confirmation
                
                # Handle exit confirmation first if active
                if self.show_exit_confirmation:
                    if self.yes_button.rect.collidepoint(mouse_pos):
                        game_bg.stop()
                        self.exit_confirmed = True
                        self.exit_time = pygame.time.get_ticks()
                    elif self.no_button.rect.collidepoint(mouse_pos):
                        self.show_exit_confirmation = False
                    continue  # Skip other checks after confirmation

                # Handle options menu buttons
                if self.show_options:
                    if self.mute_sounds_button.rect.collidepoint(mouse_pos):
                        self.mute_sounds = not self.mute_sounds_button.toggle()
                        if self.mute_sounds:
                            laser_sound.set_volume(0)
                            explosion_sound.set_volume(0)
                            game_over_sound.set_volume(0)
                        else:
                            laser_sound.set_volume(0.7)
                            explosion_sound.set_volume(0.8)
                            game_over_sound.set_volume(0.7)
                    elif self.mute_bgm_button.rect.collidepoint(mouse_pos):
                        self.mute_bgm = not self.mute_bgm_button.toggle()
                        if self.mute_bgm:
                            game_bg.set_volume(0)
                        else:
                            game_bg.set_volume(0.3)
                            if not game_bg_playing and not self.title_screen:
                                game_bg.play(-1)
                                game_bg_playing = True
                    elif self.fullscreen_button.rect.collidepoint(mouse_pos):
                        self.toggle_fullscreen()
                        self.fullscreen_button.toggle()
                    elif self.reset_scores_button.rect.collidepoint(mouse_pos):
                        self.show_confirmation = True
                    elif self.options_back_button.rect.collidepoint(mouse_pos):
                        self.show_options = False
                    continue

                # Handle pause menu buttons if game is paused
                if self.paused and not (self.show_leaderboard or self.show_options):
                    if self.resume_button.rect.collidepoint(mouse_pos):
                        self.paused = False
                    elif self.leaderboard_button.rect.collidepoint(mouse_pos):
                        self.show_leaderboard = True
                        self.show_options = False
                    elif self.options_button.rect.collidepoint(mouse_pos):
                        self.show_options = True
                        self.show_leaderboard = False
                    elif self.restart_button.rect.collidepoint(mouse_pos):
                        self.restart_game(current_level_only=True)
                        self.paused = False
                    elif self.quit_button.rect.collidepoint(mouse_pos):
                        mute_sounds = self.mute_sounds
                        mute_bgm = self.mute_bgm
                        self.__init__()
                        self.mute_sounds = mute_sounds
                        self.mute_bgm = mute_bgm
                        self.title_screen = True
                        self.paused = False
                        # Stop the BGM when returning to main menu
                        game_bg.stop()
                        game_bg_playing = False
                    continue
                
                # Handle title screen buttons
                if self.title_screen:
                    if not (self.show_leaderboard or self.show_options):
                        if self.start_button.rect.collidepoint(mouse_pos):
                            self.title_screen = False
                            self.show_level_text = True
                            self.level_text_timer = 180
                        elif self.title_leaderboard_button.rect.collidepoint(mouse_pos):
                            self.show_leaderboard = True
                            self.show_options = False
                        elif self.title_options_button.rect.collidepoint(mouse_pos):
                            self.show_options = True
                            self.show_leaderboard = False
                        elif self.title_quit_button.rect.collidepoint(mouse_pos):
                            self.show_exit_confirmation = True
                    elif self.show_leaderboard and self.back_button.rect.collidepoint(mouse_pos):
                        self.show_leaderboard = False
                    continue
                
                # Handle leaderboard back button
                if self.show_leaderboard and self.back_button.rect.collidepoint(mouse_pos):
                    self.show_leaderboard = False
                    continue
        
        return True
        
    def shoot_player_bullet(self):
        bullets_per_shot = self.level_configs[self.level]['bullets_per_shot']
        
        if bullets_per_shot == 1:
            # Single bullet (default behavior)
            bullet_x = self.player.x + self.player.width // 2 - 2
            bullet_y = self.player.y
            self.player_bullets.append(Bullet(bullet_x, bullet_y, -12))
        else:
            # Multiple bullets with spread pattern
            spread_angle = 15  # degrees between bullets
            center_x = self.player.x + self.player.width // 2
            
            for i in range(bullets_per_shot):
                # Calculate offset for each bullet
                offset = (i - (bullets_per_shot - 1) / 2) * 15  # Spread bullets horizontally
                bullet_x = center_x + offset - 2  # -2 to center the bullet
                
                # Create bullet with slight angle if more than one
                if bullets_per_shot > 1:
                    angle = (i - (bullets_per_shot - 1) / 2) * (spread_angle * 3.14159 / 180)
                    speed_x = -12 * math.sin(angle)  # Small horizontal component
                    speed_y = -12 * math.cos(angle)  # Main vertical component
                else:
                    speed_x = 0
                    speed_y = -12
                    
                self.player_bullets.append(Bullet(bullet_x, self.player.y, speed_y))
        
        if not self.mute_sounds:
            laser_sound.play()

    def shoot_invader_bullet(self):
        if self.invaders and random.random() < self.invader_shoot_chance and not self.show_level_text:
            invader = random.choice(self.invaders)
            bullet_x = invader.x + invader.width // 2 - 2
            bullet_y = invader.y + invader.height
            
            bullet_speed = 6 + self.level
            bullet_color = RED if invader.type <= 2 else PURPLE if invader.type <= 4 else ORANGE
            
            self.invader_bullets.append(Bullet(bullet_x, bullet_y, bullet_speed, bullet_color))
            
    def next_level(self):
        if self.level < self.max_level:
            self.level += 1
            self.level_complete = False
            self.player_bullets = []
            self.invader_bullets = []
            self.create_invaders()
            self.show_level_text = True
            self.level_text_timer = 180
            self.score += 100 * self.level
        else:
            self.won = True
            self.game_over = True
            
    def update(self):
        global game_bg_playing
        if self.title_screen or self.game_over or self.level_complete or self.paused or self.show_leaderboard or self.show_options:
            if self.game_over and not self.score_submitted:
                if self.leaderboard_manager.is_high_score(self.score):
                    self.leaderboard_manager.add_score(self.score, self.level)
                self.score_submitted = True
                # Stop BGM when game is over
                game_bg.stop()
                game_bg_playing = False
            return
            
        alt_pressed = pygame.key.get_pressed()[pygame.K_RALT]

        # Handle death animation
        if self.player.is_dying:
            self.player.death_animation_timer -= 1
            if self.player.death_animation_timer <= 0:
                self.death_timer = self.death_delay
                self.player.is_dying = False
                # Add final explosion particles when animation ends
                for _ in range(50):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(1, 8)
                    size = random.randint(1, 4)
                    lifetime = random.randint(20, 40)
                    self.player.death_particles.append({
                        'x': self.player.x + self.player.width//2,
                        'y': self.player.y + self.player.height//2,
                        'dx': math.cos(angle) * speed,
                        'dy': math.sin(angle) * speed,
                        'size': size,
                        'lifetime': lifetime,
                        'color': random.choice([RED, ORANGE, YELLOW, WHITE])
                    })
            return
                
        # Handle death delay
        if self.death_timer > 0:
            # Update particles during death delay
            for particle in self.player.death_particles[:]:
                particle['x'] += particle['dx']
                particle['y'] += particle['dy']
                particle['lifetime'] -= 1
                if particle['lifetime'] <= 0:
                    self.player.death_particles.remove(particle)
            
            self.death_timer -= 1
            if self.death_timer <= 0:
                self.game_over = True
                if not self.mute_sounds:
                    game_over_sound.play()
            return
            
        if self.show_level_text:
            self.level_text_timer -= 1
            if self.level_text_timer <= 0:
                self.show_level_text = False
                if not self.mute_bgm and not game_bg_playing and not self.title_screen:
                    game_bg.play(-1)
                    game_bg_playing = True
            
        self.player.update(can_move=not self.show_level_text)
        
        for bullet in self.player_bullets[:]:
            bullet.update()
            if bullet.y < 0:
                self.player_bullets.remove(bullet)
                
        for bullet in self.invader_bullets[:]:
            bullet.update()
            if bullet.y > SCREEN_HEIGHT:
                self.invader_bullets.remove(bullet)
                
        if not self.show_level_text and not alt_pressed:
            move_down = False
            for invader in self.invaders:
                invader.update(self.invader_speed_x * self.invader_direction, 0)
                if invader.x <= 0 or invader.x + invader.width >= SCREEN_WIDTH:
                    move_down = True
                    
            if move_down:
                self.invader_direction *= -1
                for invader in self.invaders:
                    invader.update(0, self.invader_speed_y)
                
        if not alt_pressed:
            self.shoot_invader_bullet()
        
        for bullet in self.player_bullets[:]:
            for invader in self.invaders[:]:
                if bullet.rect.colliderect(invader.rect):
                    self.player_bullets.remove(bullet)
                    if invader.hit():
                        if not self.mute_sounds:
                            explosion_sound.play()
                        self.invaders.remove(invader)
                        self.score += invader.points
                    break
                    
        for bullet in self.invader_bullets[:]:
            if bullet.rect.colliderect(self.player.rect) and not self.player.is_invincible:
                self.invader_bullets.remove(bullet)
                self.lives -= 1
                if self.lives > 0:
                    self.player.trigger_hit()
                else:
                    self.player.trigger_death()  # Start death animation instead of immediate game over
                break

                if self.lives <= 0:
                    self.game_over = True
                    if not self.mute_sounds:
                        game_over_sound.play()
                    
        if not self.invaders and not self.level_complete and not self.show_level_text:
            if self.level >= self.max_level:
                self.won = True
                self.game_over = True
            else:
                self.level_complete = True
                
        for invader in self.invaders:
            if invader.y + invader.height >= self.player.y and not self.player.is_invincible:
                self.lives = 0
                self.player.trigger_death()  # Start death animation
                break
                
    def restart_game(self, current_level_only=False):
        global game_bg_playing
        if current_level_only:
            self.player_bullets = []
            self.invader_bullets = []
            self.lives = 5
            self.score = max(0, self.score - 100)
            self.create_invaders()
            self.game_over = False
            self.level_complete = False
            self.show_level_text = True
            self.level_text_timer = 180
            # Stop BGM during restart
            game_bg.stop()
            game_bg_playing = False
            
        else:
            self.__init__()
            self.title_screen = False
            self.show_level_text = True
            self.level_text_timer = 180
            # Stop BGM during full restart
            game_bg.stop()
            game_bg_playing = False
            
    def draw_title_screen(self):
        screen.fill(BLACK)
        
        title_font = pygame.font.Font(None, 120)
        shadow_offset = 5
        shadow_color = (50, 50, 100)
        
        shadow_text = title_font.render("SPACE INVADERS", True, shadow_color)
        shadow_rect = shadow_text.get_rect(center=(SCREEN_WIDTH//2 + shadow_offset, SCREEN_HEIGHT//4 + shadow_offset))
        screen.blit(shadow_text, shadow_rect)
        
        title_text = title_font.render("SPACE INVADERS", True, CYAN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
        screen.blit(title_text, title_rect)
        
        subtitle_font = pygame.font.Font(None, 36)
        subtitle_text = subtitle_font.render("Defeat Them All !", True, WHITE)
        screen.blit(subtitle_text, subtitle_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4 + 80)))

        subtitle_font = pygame.font.Font(None, 28)
        subtitle_text = subtitle_font.render("Press ENTER/SPACE to start", True, YELLOW)
        screen.blit(subtitle_text, subtitle_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4 + 120)))
        
        instr_font = pygame.font.Font(None, 24)
        instructions = [
            "Controls:",
            "Arrow Keys or A/D: Move",
            "SPACE: Shoot",
            "ESC: Pause/Back"
        ]
        
        for i, line in enumerate(instructions):
            text = instr_font.render(line, True, WHITE)
            screen.blit(text, (50, SCREEN_HEIGHT - 150 + i * 30))
    
        mouse_pos = pygame.mouse.get_pos()
        self.start_button.check_hover(mouse_pos)
        self.title_leaderboard_button.check_hover(mouse_pos)
        self.title_options_button.check_hover(mouse_pos)
        self.title_quit_button.check_hover(mouse_pos)
        
        if not (self.show_leaderboard or self.show_options):
            self.start_button.draw(screen)
            self.title_leaderboard_button.draw(screen)
            self.title_options_button.draw(screen)
            self.title_quit_button.draw(screen)
    
        if self.show_leaderboard:
            self.draw_leaderboard()
    
        if self.show_options:
            self.draw_options_menu()
    
    def draw_pause_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        big_font = pygame.font.Font(None, 72)
        title = big_font.render("GAME PAUSED", True, WHITE)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 200)))
        
        mouse_pos = pygame.mouse.get_pos()
        self.resume_button.check_hover(mouse_pos)
        self.leaderboard_button.check_hover(mouse_pos)
        self.options_button.check_hover(mouse_pos)
        self.restart_button.check_hover(mouse_pos)
        self.quit_button.check_hover(mouse_pos)
        
        self.resume_button.draw(screen)
        self.leaderboard_button.draw(screen)
        self.options_button.draw(screen)
        self.restart_button.draw(screen)
        self.quit_button.draw(screen)
    
    def draw_options_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        big_font = pygame.font.Font(None, 72)
        title = big_font.render("OPTIONS", True, WHITE)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 200)))
        
        mouse_pos = pygame.mouse.get_pos()
        self.mute_sounds_button.check_hover(mouse_pos)
        self.mute_bgm_button.check_hover(mouse_pos)
        self.fullscreen_button.check_hover(mouse_pos)
        self.reset_scores_button.check_hover(mouse_pos)
        self.options_back_button.check_hover(mouse_pos)
        
        self.mute_sounds_button.draw(screen)
        self.mute_bgm_button.draw(screen)
        self.fullscreen_button.draw(screen)
        self.reset_scores_button.draw(screen)
        self.options_back_button.draw(screen)

        if self.show_confirmation:
            self.draw_confirmation_dialog()
    
    def draw_leaderboard(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))
        
        big_font = pygame.font.Font(None, 72)
        title = big_font.render("LEADERBOARD", True, CYAN)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, 100)))

        # Check if this is a new high score and show message if it is
        if self.game_over and self.is_new_high_score():
            high_score_font = pygame.font.Font(None, 48)
            high_score_text = high_score_font.render("NEW HIGH SCORE!", True, YELLOW)
            screen.blit(high_score_text, high_score_text.get_rect(center=(SCREEN_WIDTH//2, 160)))
            
        header_font = pygame.font.Font(None, 48)
        rank_header = header_font.render("RANK", True, YELLOW)
        score_header = header_font.render("SCORE", True, YELLOW)
        level_header = header_font.render("LEVEL", True, YELLOW)
        date_header = header_font.render("DATE", True, YELLOW)
        
        header_y = 180
        screen.blit(rank_header, (200, header_y))
        screen.blit(score_header, (350, header_y))
        screen.blit(level_header, (550, header_y))
        screen.blit(date_header, (700, header_y))
        
        pygame.draw.line(screen, WHITE, (150, header_y + 50), (SCREEN_WIDTH - 150, header_y + 50), 2)
        
        score_font = pygame.font.Font(None, 36)
        scores = self.leaderboard_manager.get_top_scores()
        
        if not scores:
            no_scores_text = score_font.render("No scores yet! Be the first to play!", True, WHITE)
            screen.blit(no_scores_text, no_scores_text.get_rect(center=(SCREEN_WIDTH//2, 300)))
        else:
            for i, entry in enumerate(scores):
                y_pos = 250 + i * 40
                if self.game_over and self.is_new_high_score():
                    y_pos += 30  # Adjust position if we showed the high score message
                
                color = GREEN if (self.game_over and entry['score'] == self.score and 
                                entry['level'] == self.level) else WHITE
                
                rank_text = score_font.render(f"{i + 1}.", True, color)
                score_text = score_font.render(f"{entry['score']:,}", True, color)
                level_text = score_font.render(f"{entry['level']}", True, color)
                date_text = score_font.render(entry['date'][:10], True, color)
                
                screen.blit(rank_text, (200, y_pos))
                screen.blit(score_text, (350, y_pos))
                screen.blit(level_text, (550, y_pos))
                screen.blit(date_text, (700, y_pos))
        
        mouse_pos = pygame.mouse.get_pos()
        self.back_button.check_hover(mouse_pos)
        self.back_button.draw(screen)
        
    def draw_confirmation_dialog(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))
        
        # Calculate required width based on text
        confirm_font = pygame.font.Font(None, 48)
        confirm_text = confirm_font.render("Are you sure you want to reset all scores?", True, WHITE)
        text_width = confirm_text.get_width()
        
        # Set dialog dimensions with padding
        dialog_width = max(500, text_width + 100)  # Minimum 500, or text width + padding
        dialog_height = 250
        dialog_rect = pygame.Rect(SCREEN_WIDTH//2 - dialog_width//2, 
                                SCREEN_HEIGHT//2 - dialog_height//2, 
                                dialog_width, dialog_height)
        
        # Draw dialog box
        pygame.draw.rect(screen, DARK_GRAY, dialog_rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, dialog_rect, 2, border_radius=10)
        
        # Render and position text (split into two lines if needed)
        if text_width > SCREEN_WIDTH - 200:  # If text is too wide for screen
            # Split into two lines
            parts = "Are you sure you want to reset all scores?".split('reset')
            line1 = confirm_font.render(parts[0] + "reset", True, WHITE)
            line2 = confirm_font.render(parts[1] + "?", True, WHITE)
            
            screen.blit(line1, line1.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50)))
            screen.blit(line2, line2.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 10)))
        else:
            # Single line
            screen.blit(confirm_text, confirm_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30)))
        
        # Position buttons with new dialog width
        button_spacing = 20
        total_button_width = 120 * 2 + button_spacing
        button_start_x = SCREEN_WIDTH//2 - total_button_width//2
        
        self.yes_button.rect = pygame.Rect(button_start_x, SCREEN_HEIGHT//2 + 60, 120, 50)
        self.no_button.rect = pygame.Rect(button_start_x + 120 + button_spacing, SCREEN_HEIGHT//2 + 60, 120, 50)
        
        mouse_pos = pygame.mouse.get_pos()
        self.yes_button.check_hover(mouse_pos)
        self.no_button.check_hover(mouse_pos)
        
        self.yes_button.draw(screen)
        self.no_button.draw(screen)
    
    def draw_exit_confirmation(self):
        # Check if confirmation was already given
        if hasattr(self, 'exit_confirmed') and self.exit_confirmed:
            # Initialize starfield if not already done
            if not hasattr(self, 'exit_stars'):
                self.exit_stars = []
                for _ in range(100):  # Number of stars
                    self.exit_stars.append([
                        random.randint(0, SCREEN_WIDTH),  # x
                        random.randint(0, SCREEN_HEIGHT), # y
                        random.uniform(0.5, 3),          # speed
                        random.randint(1, 3)             # size
                    ])
            
            # Show thank you messages and exit after delay
            current_time = pygame.time.get_ticks()
            if current_time - self.exit_time >= 1000:  
                return "exit"
            
            # Solid black background
            screen.fill(BLACK)
            
            # Update and draw stars
            for star in self.exit_stars:
                star[1] += star[2]  # Move star downward
                if star[1] > SCREEN_HEIGHT:  # Reset star at top if it goes off screen
                    star[1] = 0
                    star[0] = random.randint(0, SCREEN_WIDTH)
                pygame.draw.circle(screen, WHITE, (int(star[0]), int(star[1])), int(star[3]))
                        
            return
        
        # Create a new overlay surface that will cover everything
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 250))
        screen.blit(overlay, (0, 0))
        
        # Draw confirmation dialog
        confirm_font = pygame.font.Font(None, 48)
        confirm_text = confirm_font.render("Are you sure you want to exit?", True, WHITE)
        
        screen.blit(confirm_text, confirm_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40)))
        
        mouse_pos = pygame.mouse.get_pos()
        self.yes_button.check_hover(mouse_pos)
        self.no_button.check_hover(mouse_pos)
        
        self.yes_button.draw(screen)
        self.no_button.draw(screen)
        
    def draw(self, screen):
        exit_signal = None  
        screen.fill(BLACK)
        font = pygame.font.Font(None, 36)
        big_font = pygame.font.Font(None, 72)

        # Draw particles first (so they appear behind other elements)
        if self.player.is_dying or (self.death_timer > 0 and self.player.death_particles):
            for particle in self.player.death_particles:
                pygame.draw.circle(
                    screen, 
                    particle['color'],
                    (int(particle['x']), int(particle['y'])),
                    particle['size']
                )
        
        # Draw game elements first (only if no overlays are active)
        if not (self.show_level_text or self.level_complete or self.game_over or self.paused or 
                self.show_leaderboard or self.show_options or self.show_exit_confirmation or self.title_screen):
            
            # Draw player unless in death animation (it draws itself during death)
            if not self.player.is_dying:
                self.player.draw(screen)
                
            for bullet in self.player_bullets:
                bullet.draw(screen)
                
            for bullet in self.invader_bullets:
                bullet.draw(screen)
                
            for invader in self.invaders:
                invader.draw(screen)
                
            # Draw HUD elements
            score_text = font.render(f'Score: {self.score}', True, WHITE)
            lives_text = font.render(f'Lives: {self.lives}', True, WHITE)
            level_text = font.render(f'Level: {self.level}/{self.max_level}', True, WHITE)
            screen.blit(score_text, (20, 20))
            screen.blit(lives_text, (20, 60))
            screen.blit(level_text, (20, 100))
            
            # Show "HIT!" message when player is hit
            if self.player.is_hit:
                hit_text = font.render("HIT!", True, RED)
                screen.blit(hit_text, (self.player.x + self.player.width//2 - 20, self.player.y - 30))
            
            control_font = pygame.font.Font(None, 24)
            controls = [
                "Arrow Keys / AD: Move",
                "SPACE: Shoot",
                "ESC: Pause"
            ]
            for i, control in enumerate(controls):
                text = control_font.render(control, True, WHITE)
                screen.blit(text, (SCREEN_WIDTH - 200, 20 + i * 25))
        
        # Draw overlay screens
        if self.show_level_text:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))
            
            level_name = self.level_configs[self.level]['name']
            level_intro_text = big_font.render(level_name, True, CYAN)
            screen.blit(level_intro_text, level_intro_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))
            
        elif self.level_complete and not self.won:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))
            
            complete_text = big_font.render('LEVEL COMPLETE!', True, GREEN)
            bonus_text = font.render(f'Bonus: {100 * self.level} points', True, YELLOW)
            continue_text = font.render('Press ENTER to continue', True, WHITE)
            
            screen.blit(complete_text, complete_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40)))
            screen.blit(bonus_text, bonus_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20)))
            screen.blit(continue_text, continue_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60)))
            
        elif self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))
            
            if self.won:
                game_over_text = big_font.render('YOU WON', True, RED)
                subtitle_text = font.render('You have defeated all invader waves!', True, GREEN)
                self.show_level_text = False

                menu_text = font.render('Press SPACE/RETURN to Exit Game', True, WHITE)
                quit_text = font.render('Press ESC to return to Main Menu', True, WHITE)

            else:
                game_over_text = big_font.render('GAME OVER', True, RED)
                subtitle_text = font.render(f'You reached Level {self.level}', True, WHITE)

                restart_text = font.render('Press R to Restart', True, WHITE)
                quit_text = font.render('Press ESC to return to Main Menu', True, WHITE)
                
            final_score_text = font.render(f'Final Score: {self.score}', True, YELLOW)

            screen.blit(game_over_text, game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 150)))
            screen.blit(subtitle_text, subtitle_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 35)))
            screen.blit(final_score_text, final_score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))
                                    
            if self.won:
                screen.blit(menu_text, menu_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100)))
                screen.blit(quit_text, quit_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 150)))
            else:
                screen.blit(restart_text, restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100)))
                screen.blit(quit_text, quit_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 150)))
        
        # Draw UI elements that should always be on top
        if self.paused and not self.show_leaderboard and not self.show_options:
            self.draw_pause_menu()
        
        if self.show_leaderboard:
            self.draw_leaderboard()
        
        if self.show_options:
            self.draw_options_menu()    
        
        if self.title_screen:
            self.draw_title_screen()
        
        # Draw exit confirmation last (on top of everything)
        if self.show_exit_confirmation:
            exit_signal = self.draw_exit_confirmation()
        
        return exit_signal

def star_wars_intro(screen, duration_seconds=11):
    # Star Wars intro crawl
    intro_text = [
        "SPACE INVADERS",
        "",
        "A long time ago in a galaxy far,",
        "far away...",
        "",
        "The last remnants of humanity",
        "are under attack by relentless",
        "alien invaders from deep space.",
        "",
        "The fate of humanity rests",
        "in your hands...",
        "",
        "May the Force be with you!"
    ]
    
    # Set up the crawl
    pygame.mixer.music.load(resource_path("space_invader_title.wav"))  # You'll need this file
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play()
    
    # Create a surface for the text with per-pixel alpha
    text_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT * 3), pygame.SRCALPHA)
    
    # Render the text
    font_large = pygame.font.Font(None, 80)
    font_small = pygame.font.Font(None, 48)
    y_pos = SCREEN_HEIGHT  # Start below the visible screen
    
    for i, line in enumerate(intro_text):
        if i == 0:  # Title
            text = font_large.render(line, True, YELLOW)
            text_rect = text.get_rect(centerx=SCREEN_WIDTH//2, centery=y_pos)
            text_surface.blit(text, text_rect)
            y_pos += 100
        elif line:  # Regular line
            text = font_small.render(line, True, YELLOW)
            text_rect = text.get_rect(centerx=SCREEN_WIDTH//2, centery=y_pos)
            text_surface.blit(text, text_rect)
            y_pos += 50
        else:  # Empty line
            y_pos += 30
    
    # Starfield background
    stars = []
    for _ in range(200):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT * 3)
        size = random.randint(1, 3)
        speed = random.uniform(0.5, 2.0)
        stars.append((x, y, size, speed))
    
    # Main crawl loop
    clock = pygame.time.Clock()
    crawl_pos = 0
    running = True
    start_time = pygame.time.get_ticks()  # Get the start time in milliseconds
    
    while running:
        current_time = pygame.time.get_ticks()
        elapsed_seconds = (current_time - start_time) / 1000  # Convert to seconds
        
        # Exit if duration is reached
        if elapsed_seconds >= duration_seconds:
            running = False
            pygame.mixer.music.stop()
            return
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                # Check for specific keys to skip
                if (event.key == pygame.K_RETURN):  
                    running = False
                    pygame.mixer.music.stop()
                    return
        
        # Update star positions
        new_stars = []
        for x, y, size, speed in stars:
            y -= speed
            if y > -10:  # Keep stars slightly above top to smooth disappearance
                new_stars.append((x, y, size, speed))
        stars = new_stars
        
        # Add new stars at the bottom only if text is still visible
        if crawl_pos < SCREEN_HEIGHT * 2 + y_pos:
            while len(stars) < 200:
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(SCREEN_HEIGHT, SCREEN_HEIGHT + 10)
                size = random.randint(1, 3)
                speed = random.uniform(0.5, 2.0)
                stars.append((x, y, size, speed))
        
        # Draw everything
        screen.fill(BLACK)
        
        # Draw stars (behind text)
        for x, y, size, _ in stars:
            pygame.draw.circle(screen, WHITE, (int(x), int(y)), size)
        
        # Draw the text surface (scrolling up) with transparency
        screen.blit(text_surface, (0, -crawl_pos))
        
        pygame.display.flip()
        clock.tick(60)
        
        # Update crawl position
        crawl_pos += 2
        if crawl_pos > SCREEN_HEIGHT * 2 + y_pos:
            running = False
            pygame.mixer.music.stop()

def show_exit_credits():
    """Display exit credits sequence with scrolling credits and dedicated outro music"""
    # Stop any currently playing sounds
    pygame.mixer.stop()
    
    # Load outro music (replace with your actual file path)
    outro_music_path = resource_path("outro_music.wav")  # or .ogg
    try:
        outro_music = pygame.mixer.Sound(outro_music_path)
        outro_music.set_volume(0.7)  # Adjust volume as needed
        outro_music.play(loops=-1)  # Loop indefinitely
    except:
        outro_music = None
    
    # Initialize parameters
    rolling_text_y = SCREEN_HEIGHT  # Start below screen
    rolling_text_speed = 2  # Pixels per frame
    total_duration = 14000  # 14 seconds total (can adjust as needed)
    start_time = pygame.time.get_ticks()
    
    # Define credits content
    credit_font = pygame.font.Font(None, 32)
    credits = [
        "SPACE INVADERS",
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
        pygame.K_RETURN, pygame.K_ESCAPE
    }
        
    # Main loop
    running = True
    while running:
        current_time = pygame.time.get_ticks()
        elapsed = current_time - start_time
        
        # Check if total duration has been reached
        if elapsed >= total_duration:
            if outro_music:
                outro_music.stop()
            return "quit"
        
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
                    return "quit"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Also allow skipping with mouse clicks
                if outro_music:
                    outro_music.stop()
                return "quit"
        
        # Update credits scrolling
        rolling_text_y -= rolling_text_speed
        if rolling_text_y < -2000:  # End when credits scroll past
            if outro_music:
                outro_music.stop()
            return "quit"
        
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
    return 'quit'

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption('Space Invaders')
    
    # Show logos first
    logo_screen = LogoScreen()
    logo_done = False
    while not logo_done:
        result = logo_screen.update()
        if result == "quit":
            pygame.quit()
            sys.exit()
        elif result is True:  # Logos finished or skipped
            logo_done = True
        
        logo_screen.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)
    
    # Show Star Wars intro after logos
    star_wars_intro(screen)
    
    game = Game()
    running = True
    
    while running:
        running = game.handle_events()
        game.update()
        
        # Check for exit signal from draw method
        exit_signal = game.draw(screen)
        if exit_signal == "exit":
            running = False

        pygame.display.flip()
        clock.tick(FPS)
        
        # Check if we should show exit credits (only after game is won and player has seen the message)
        if hasattr(game, 'exit_confirmed') and game.exit_confirmed:
            show_exit_credits()
            running = False
        elif game.won and game.game_over:
            # Check for key press to trigger credits
            keys = pygame.key.get_pressed()
            if keys[pygame.K_RETURN] or keys[pygame.K_SPACE]:
                show_exit_credits()
                running = False
    
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()