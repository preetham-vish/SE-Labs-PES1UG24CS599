import random
import pygame
from .paddle import Paddle
from .ball import Ball
from .brick import Brick
from .sounds import Sounds

# Game Engine

WHITE = (255, 255, 255)
BG = (15, 15, 25)
BRICK_COLORS = [
    (200, 60, 60),
    (200, 140, 60),
    (200, 200, 60),
    (80, 180, 80),
    (80, 140, 200),
]

# name: (ball speed, paddle width)
DIFFICULTIES = {
    "Easy": (3, 130),
    "Medium": (4, 100),
    "Hard": (6, 70),
}
DIFF_KEYS = {pygame.K_1: "Easy", pygame.K_2: "Medium", pygame.K_3: "Hard"}


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font = pygame.font.SysFont("Arial", 28)
        self.big_font = pygame.font.SysFont("Arial", 56, bold=True)
        self.sounds = Sounds()
        self.running = True
        self.difficulty = "Medium"
        self.rows, self.cols = 5, 8
        self._new_game(self.difficulty)

    # ---------- setup ----------
    def _new_game(self, difficulty):
        self.difficulty = difficulty
        self.ball_speed, paddle_w = DIFFICULTIES[difficulty]
        self.paddle = Paddle(self.width // 2 - paddle_w // 2, self.height - 30, paddle_w, 14)
        self.ball = Ball(self.width // 2, self.height - 50, radius=8)
        self._reset_ball()
        self.bricks = self._build_bricks(self.rows, self.cols)
        self.lives = 3
        self.score = 0
        self.game_over = False
        self.result = None  # "win" or "lose"
        self.state = "playing"  # "playing" | "end" | "difficulty"

    def _build_bricks(self, rows, cols):
        bricks = []
        margin, gap, top = 30, 6, 60
        brick_w = (self.width - margin * 2 - gap * (cols - 1)) // cols
        brick_h = 22
        for r in range(rows):
            for c in range(cols):
                x = margin + c * (brick_w + gap)
                y = top + r * (brick_h + gap)
                bricks.append(Brick(x, y, brick_w, brick_h))
        return bricks

    def _reset_ball(self):
        self.ball.x, self.ball.y = self.width // 2, self.height - 50
        self.ball.vx = random.choice((-1, 1)) * self.ball_speed
        self.ball.vy = -self.ball_speed

    # ---------- input ----------
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.state == "end":
            if event.key in (pygame.K_RETURN, pygame.K_r):
                self.state = "difficulty"
            elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                self.running = False
        elif self.state == "difficulty":
            if event.key in DIFF_KEYS:
                self._new_game(DIFF_KEYS[event.key])
            elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                self.running = False

    def handle_input(self):
        if self.state != "playing":
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.paddle.move(-self.paddle.speed, self.width)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.paddle.move(self.paddle.speed, self.width)

    # ---------- collision ----------
    def _resolve(self, rect):
        """Resolve ball vs rect along the axis of least penetration.
        Returns 'x' (side hit) or 'y' (top/bottom hit)."""
        b = self.ball.rect()
        o_left = b.right - rect.left
        o_right = rect.right - b.left
        o_top = b.bottom - rect.top
        o_bottom = rect.bottom - b.top

        if min(o_left, o_right) < min(o_top, o_bottom):
            if o_left < o_right:
                self.ball.vx = -abs(self.ball.vx)
                self.ball.x -= o_left
            else:
                self.ball.vx = abs(self.ball.vx)
                self.ball.x += o_right
            return "x"
        if o_top < o_bottom:
            self.ball.vy = -abs(self.ball.vy)
            self.ball.y -= o_top
        else:
            self.ball.vy = abs(self.ball.vy)
            self.ball.y += o_bottom
        return "y"

    # ---------- update ----------
    def update(self):
        if self.state != "playing":
            return

        ball = self.ball
        ball.move()

        # walls
        if ball.x - ball.radius <= 0:
            ball.x = ball.radius
            ball.vx = abs(ball.vx)
            self.sounds.play("wall")
        elif ball.x + ball.radius >= self.width:
            ball.x = self.width - ball.radius
            ball.vx = -abs(ball.vx)
            self.sounds.play("wall")
        if ball.y - ball.radius <= 0:
            ball.y = ball.radius
            ball.vy = abs(ball.vy)
            self.sounds.play("wall")

        # paddle
        prect = self.paddle.rect()
        if ball.vy > 0 and ball.rect().colliderect(prect):
            axis = self._resolve(prect)
            if axis == "y" and ball.vy < 0:
                # steer by hit position: -1 (left edge) .. +1 (right edge)
                offset = (ball.x - (prect.centerx)) / (prect.width / 2)
                offset = max(-1, min(1, offset))
                ball.vx = offset * self.ball_speed * 1.25
            self.sounds.play("paddle")

        # bricks
        for brick in self.bricks:
            if brick.alive and ball.rect().colliderect(brick.rect()):
                brick.alive = False
                self.score += 1
                self._resolve(brick.rect())
                self.sounds.play("brick")
                break

        # fell below
        if ball.y - ball.radius > self.height:
            self.lives -= 1
            if self.lives <= 0:
                self._finish("lose")
            else:
                self.sounds.play("lose_life")
                self._reset_ball()

        if self.state == "playing" and all(not b.alive for b in self.bricks):
            self._finish("win")

    def _finish(self, result):
        self.game_over = True
        self.result = result
        self.state = "end"
        self.sounds.play(result)

    # ---------- render ----------
    def _center_text(self, screen, text, font, y, color=WHITE):
        surf = font.render(text, True, color)
        screen.blit(surf, (self.width // 2 - surf.get_width() // 2, y))

    def _overlay(self, screen):
        shade = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 170))
        screen.blit(shade, (0, 0))

    def render(self, screen):
        screen.fill(BG)

        pygame.draw.rect(screen, WHITE, self.paddle.rect())
        pygame.draw.circle(screen, WHITE, (int(self.ball.x), int(self.ball.y)), self.ball.radius)

        for i, brick in enumerate(self.bricks):
            if brick.alive:
                row = i // self.cols
                color = BRICK_COLORS[row % len(BRICK_COLORS)]
                pygame.draw.rect(screen, color, brick.rect())

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        screen.blit(lives_text, (self.width - 130, 10))

        if self.state == "end":
            self._overlay(screen)
            won = self.result == "win"
            self._center_text(screen, "YOU WIN!" if won else "GAME OVER", self.big_font, 150,
                              (80, 220, 100) if won else (220, 80, 80))
            self._center_text(screen, f"Final score: {self.score}", self.font, 240)
            self._center_text(screen, "ENTER - play again", self.font, 310)
            self._center_text(screen, "ESC - quit", self.font, 350)
        elif self.state == "difficulty":
            self._overlay(screen)
            self._center_text(screen, "Select Difficulty", self.big_font, 130)
            for i, name in enumerate(DIFFICULTIES):
                self._center_text(screen, f"{i + 1} - {name}", self.font, 240 + i * 45)
            self._center_text(screen, "ESC - quit", self.font, 400)
