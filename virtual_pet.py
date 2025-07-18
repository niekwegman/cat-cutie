import sys
import random
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect
from PyQt5.QtGui import QPixmap, QTransform
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

        # Frame size and counts
        self.frame_width = 80
        self.frame_height = 80

        # Load animators
        self.animators = {
            'idle': SpriteAnimator("assets/IDLE.png", 80, 64, 8),
            'walk_r': SpriteAnimator("assets/WALK.png", 80, 64, 8),
            'walk_l': SpriteAnimator("assets/WALK.png", 80, 64, 8, mirrored=True),
            'meow': SpriteAnimator("assets/ATTACK 1.png", 80, 64, 8),
        }

        self.current_animator = self.animators['idle']

        self.label = QLabel(self)
        self.label.setFixedSize(self.frame_width, self.frame_height)
        self.label.setScaledContents(False)
        self.label.setPixmap(self.current_animator.next_frame())
        self.resize(self.frame_width, self.frame_height)

        # Feed icon (reuse a frame from meow animation)
        self.feed_icon = QLabel(self)
        self.feed_icon.setFixedSize(self.frame_width, self.frame_height)
        self.feed_icon.setPixmap(self.animators['meow'].frames[0])
        self.feed_icon.move(40, 0)
        self.feed_icon.hide()
        self.feed_icon.mousePressEvent = self.feed_pet

        self.move(random.randint(100, 500), random.randint(100, 400))

        # Timers
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(100)

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
        if self.is_hungry:
            return

        new_x = random.randint(0, self.screen_geometry.width() - self.width())
        new_y = random.randint(0, self.screen_geometry.height() - self.height())

        if new_x < self.x():
            self.direction = -1
            self.set_animation('walk_l')
        else:
            self.direction = 1
            self.set_animation('walk_r')

        self.move(new_x, new_y)
        QTimer.singleShot(2000, lambda: self.set_animation('idle'))

    def increase_hunger(self):
        self.hunger += 1
        if self.hunger > 3:
            self.get_hungry()

    def get_hungry(self):
        self.is_hungry = True
        self.set_animation('meow')
        self.feed_icon.show()

    def feed_pet(self, event):
        self.hunger = 0
        self.is_hungry = False
        self.feed_icon.hide()
        self.set_animation('idle')

    def attention_seek(self):
        if not self.is_hungry:
            screen = QApplication.primaryScreen().geometry()
            self.move(-self.width(), random.randint(0, screen.height() - self.height()))
            QTimer.singleShot(1000, self.walk_back_for_attention)

    def walk_back_for_attention(self):
        self.set_animation('walk_r')
        self.move(self.screen_geometry.width() // 2, self.screen_geometry.height() // 2)
        QTimer.singleShot(2000, lambda: self.set_animation('idle'))

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
