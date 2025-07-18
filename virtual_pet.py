import sys
import random
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect
from PyQt5.QtGui import QPixmap, QTransform, QPainter, QBrush, QColor
from PyQt5.QtWidgets import QApplication, QLabel, QWidget


class SpriteAnimator:
    def __init__(self, sprite_path, frame_width, frame_height, frame_count, mirrored=False):
        original = QPixmap(sprite_path)
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.frame_count = frame_count
        self.current_frame = 0

        if mirrored:
            transform = QTransform().scale(-1, 1)
            mirrored_sprite = original.transformed(transform)
            # flip frames left to right by slicing from rightmost
            self.frames = [mirrored_sprite.copy(mirrored_sprite.width() - (i+1)*frame_width, 0, frame_width, frame_height)
                           for i in range(frame_count)]
        else:
            self.frames = [original.copy(i*frame_width, 0, frame_width, frame_height)
                           for i in range(frame_count)]

    def next_frame(self):
        frame = self.frames[self.current_frame]
        self.current_frame = (self.current_frame + 1) % self.frame_count
        return frame

    def reset(self):
        self.current_frame = 0


class Fish(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Create fish sprite from tileset
        self.fish_pixmap = self.create_fish_sprite()
        self.label = QLabel(self)
        self.label.setPixmap(self.fish_pixmap)
        self.label.setFixedSize(32, 32)
        self.resize(32, 32)
        
        self.old_pos = QPoint(0, 0)
        self.being_dragged = False
        
    def create_fish_sprite(self):
        # Load fish tileset and select random fish
        try:
            tileset = QPixmap("assets/fish.png")
            # Select random fish (0-3) from the 4 fish in the tileset
            fish_index = random.randint(0, 3)
            fish_x = fish_index * 32
            
            # Extract the specific fish sprite (32x32)
            fish_sprite = tileset.copy(fish_x, 0, 32, 32)
            return fish_sprite
        except:
            # Fallback to programmatic fish if image fails to load
            return self.create_fallback_fish()
    
    def create_fallback_fish(self):
        # Create a simple fish sprite programmatically as fallback
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fish body (orange)
        painter.setBrush(QBrush(QColor(255, 165, 0)))
        painter.drawEllipse(8, 12, 16, 8)
        
        # Fish tail (orange)
        painter.drawPolygon([QPoint(8, 16), QPoint(2, 12), QPoint(2, 20)])
        
        # Fish eye (white with black pupil)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(18, 14, 3, 3)
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawEllipse(19, 15, 1, 1)
        
        painter.end()
        return pixmap
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()
            self.being_dragged = True
    
    def mouseMoveEvent(self, event):
        if self.being_dragged:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
    
    def mouseReleaseEvent(self, event):
        self.being_dragged = False


class VirtualPet(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.screen_geometry = QApplication.primaryScreen().geometry()
        self.old_pos = QPoint(0, 0)

        # Pet state
        self.hunger = 0
        self.is_hungry = False
        self.direction = 1  # 1 = right, -1 = left
        
        # Movement state
        self.is_walking = False
        self.target_x = 0
        self.target_y = 0
        self.walk_speed = 2
        self.was_offscreen = False
        
        # Fish feeding system
        self.fish = None

        # Frame size and counts
        self.frame_width = 80
        self.frame_height = 80

        # Load animators
        self.animators = {
            'idle_l': SpriteAnimator("assets/IDLE.png", 80, 64, 8),
            'idle_r': SpriteAnimator("assets/IDLE.png", 80, 64, 8, mirrored=True),
            'walk_r': SpriteAnimator("assets/WALK.png", 80, 64, 8, mirrored=True),
            'walk_l': SpriteAnimator("assets/WALK.png", 80, 64, 8),
            'meow': SpriteAnimator("assets/ATTACK 1.png", 80, 64, 8),
        }

        self.current_animator = self.animators['idle_l']

        self.label = QLabel(self)
        self.label.setFixedSize(self.frame_width, self.frame_height)
        self.label.setScaledContents(False)
        self.label.setPixmap(self.current_animator.next_frame())
        self.resize(self.frame_width, self.frame_height)


        self.move(random.randint(100, 500), random.randint(100, 400))

        # Timers
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(100)

        self.movement_timer = QTimer()
        self.movement_timer.timeout.connect(self.update_position)
        self.movement_timer.start(50)
        
        self.fish_check_timer = QTimer()
        self.fish_check_timer.timeout.connect(self.check_fish_collision)
        self.fish_check_timer.start(100)

        self.walk_timer = QTimer()
        self.walk_timer.timeout.connect(self.random_walk)
        self.walk_timer.start(15000)

        self.hunger_timer = QTimer()
        self.hunger_timer.timeout.connect(self.increase_hunger)
        self.hunger_timer.start(20000)

        self.attention_timer = QTimer()
        self.attention_timer.timeout.connect(self.attention_seek)
        self.attention_timer.start(60000)

    def animate(self):
        frame = self.current_animator.next_frame()
        self.label.setPixmap(frame)

    def set_animation(self, name):
        self.current_animator = self.animators[name]
        self.current_animator.reset()

    def random_walk(self):
        if self.is_hungry or self.is_walking:
            return

        # Only walk 30% of the time
        if random.random() > 0.3:
            return

        # Move in smaller steps - within 200 pixels from current position
        max_distance = 200
        current_x = self.x()
        current_y = self.y()
        
        # Calculate new position within bounds
        min_x = max(0, current_x - max_distance)
        max_x = min(self.screen_geometry.width() - self.width(), current_x + max_distance)
        min_y = max(0, current_y - max_distance)
        max_y = min(self.screen_geometry.height() - self.height(), current_y + max_distance)
        
        self.target_x = random.randint(min_x, max_x)
        self.target_y = random.randint(min_y, max_y)

        if self.target_x < self.x():
            self.direction = -1
            self.set_animation('walk_l')
        else:
            self.direction = 1
            self.set_animation('walk_r')

        self.is_walking = True

    def update_position(self):
        if not self.is_walking:
            return

        current_x = self.x()
        current_y = self.y()
        
        # Check if cat is offscreen
        if (current_x < -self.width() or current_x > self.screen_geometry.width() or 
            current_y < -self.height() or current_y > self.screen_geometry.height()):
            self.was_offscreen = True
        
        # Calculate distance to target
        dx = self.target_x - current_x
        dy = self.target_y - current_y
        distance = (dx**2 + dy**2)**0.5
        
        # If close enough to target, stop walking
        if distance < self.walk_speed:
            self.move(self.target_x, self.target_y)
            self.is_walking = False
            if self.direction == 1:
                self.set_animation('idle_r')
            else:
                self.set_animation('idle_l')
            return
        
        # Move towards target
        if distance > 0:
            step_x = (dx / distance) * self.walk_speed
            step_y = (dy / distance) * self.walk_speed
            
            # Update direction if needed
            if step_x < 0 and self.direction == 1:
                self.direction = -1
                self.set_animation('walk_l')
            elif step_x > 0 and self.direction == -1:
                self.direction = 1
                self.set_animation('walk_r')
            
            self.move(int(current_x + step_x), int(current_y + step_y))

    def increase_hunger(self):
        self.hunger += 1
        if self.hunger > 3:
            self.get_hungry()

    def get_hungry(self):
        self.is_hungry = True
        self.set_animation('meow')
        self.spawn_fish()

    def feed_pet(self):
        if self.is_walking:
            return
        self.hunger = 0
        self.is_hungry = False
        self.is_walking = False
        if self.fish:
            self.fish.close()
            self.fish = None
        if self.direction == 1:
            self.set_animation('idle_r')
        else:
            self.set_animation('idle_l')
    
    def spawn_fish(self):
        if self.fish is None:
            self.fish = Fish()
            # Spawn fish at random location on screen
            screen = QApplication.primaryScreen().geometry()
            fish_x = random.randint(50, screen.width() - 90)
            fish_y = random.randint(50, screen.height() - 75)
            self.fish.move(fish_x, fish_y)
            self.fish.show()
    
    def check_fish_collision(self):
        if self.fish and self.is_hungry:
            # Check if fish is close enough to cat
            fish_rect = QRect(self.fish.x(), self.fish.y(), self.fish.width(), self.fish.height())
            cat_rect = QRect(self.x(), self.y(), self.width(), self.height())
            
            if fish_rect.intersects(cat_rect):
                self.feed_pet()

    def attention_seek(self):
        if not self.is_hungry and not self.is_walking and self.was_offscreen:
            screen = QApplication.primaryScreen().geometry()
            self.move(-self.width(), random.randint(0, screen.height() - self.height()))
            self.was_offscreen = False
            QTimer.singleShot(1000, self.walk_back_for_attention)

    def walk_back_for_attention(self):
        self.target_x = self.screen_geometry.width() // 2
        self.target_y = self.screen_geometry.height() // 2
        self.direction = 1
        self.set_animation('walk_r')
        self.is_walking = True

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPos()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    pet = VirtualPet()
    pet.show()
    sys.exit(app.exec_())
