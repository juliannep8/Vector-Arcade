import asyncio
import math
import random
import pygame
pygame.init()

WIDTH = 800
HEIGHT = 600
FPS = 60

BLACK = (15, 15, 25)
WHITE = (255, 255, 255)
CYAN = (0, 220, 255)
GREEN = (60, 220, 100)
RED = (235, 65, 65)
YELLOW = (255, 230, 80)
GRAY = (120, 120, 140)


PLAYER_SIZE = 28
PLAYER_ACCEL = 1400.0
PLAYER_DRAG = 0.88
PLAYER_MAX_SPEED = 260.0
DASH_IMPULSE = 420.0
DASH_COOLDOWN = 1.2
EVENT_TIME = 0.75  #between damage

ALIEN_SIZE = 26
ALIEN_SPEED = 90.0
DETECTION_RANGE = 260.0
FOV_THRESHOLD = 0.65

LASER_SPEED = 520.0
LASER_DAMAGE = 10


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Project 2")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 26)
big_font = pygame.font.Font(None, 56)


class P1:
    def __init__(self):
        self.position = pygame.Vector2(WIDTH / 2, HEIGHT / 2)
        self.velocity = pygame.Vector2(0, 0)
        self.acceleration = pygame.Vector2(0, 0)
        self.angle = 0.0
        self.forward = pygame.Vector2(1, 0)
        self.radius = PLAYER_SIZE / 2

        self.max_health = 100
        self.health = self.max_health
        self.damage_timer = 0.0
        self.fire_timer = 0.0
        self.dash_timer = 0.0

    def trigger_dash(self):
        if self.dash_timer <= 0:
            self.velocity += self.forward * DASH_IMPULSE
            self.dash_timer = DASH_COOLDOWN

    def update(self, keys, dt):
        if self.damage_timer > 0:
            self.damage_timer -= dt
        if self.fire_timer > 0:
            self.fire_timer -= dt
        if self.dash_timer > 0:
            self.dash_timer -= dt

        move_input = pygame.Vector2(0, 0)
        if keys[pygame.K_w]:
            move_input.y -= 1
        if keys[pygame.K_s]:
            move_input.y += 1
        if keys[pygame.K_a]:
            move_input.x -= 1
        if keys[pygame.K_d]:
            move_input.x += 1

        if move_input.length() > 0:
            move_input = move_input.normalize()
            self.angle = math.degrees(math.atan2(-move_input.y, move_input.x)) #face

        radians = math.radians(self.angle)
        self.forward = pygame.Vector2(math.cos(radians), -math.sin(radians))

        self.acceleration = move_input * PLAYER_ACCEL
        self.velocity += self.acceleration * dt
        self.velocity *= math.pow(PLAYER_DRAG, dt * 60)

        if self.dash_timer < DASH_COOLDOWN - 0.15:
            if self.velocity.length() > PLAYER_MAX_SPEED:
                self.velocity.scale_to_length(PLAYER_MAX_SPEED)

        self.position += self.velocity * dt

        self.position.x = max(self.radius, min(WIDTH - self.radius, self.position.x))
        self.position.y = max(self.radius, min(HEIGHT - self.radius, self.position.y))

    def draw(self):
        color = WHITE if (self.damage_timer > 0 and int(self.damage_timer * 15) % 2 == 0) else CYAN
        rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        rect.center = (int(self.position.x), int(self.position.y))
        pygame.draw.rect(screen, color, rect)

        visor_pos = self.position + self.forward * 10
        visor_rect = pygame.Rect(0, 0, 8, 8)
        visor_rect.center = (int(visor_pos.x), int(visor_pos.y))
        pygame.draw.rect(screen, YELLOW, visor_rect)


class Alien:
    def __init__(self, player_pos):
        while True:
            edge = random.choice(["top", "bottom", "left", "right"])
            if edge == "top":
                pos = pygame.Vector2(random.randint(0, WIDTH), 15)
            elif edge == "bottom":
                pos = pygame.Vector2(random.randint(0, WIDTH), HEIGHT - 15)
            elif edge == "left":
                pos = pygame.Vector2(15, random.randint(0, HEIGHT))
            else:
                pos = pygame.Vector2(WIDTH - 15, random.randint(0, HEIGHT))

            if pos.distance_to(player_pos) > 200:
                self.position = pos
                break

        self.velocity = pygame.Vector2(0, 0)
        self.angle = random.uniform(0, 360)
        radians = math.radians(self.angle)
        self.forward = pygame.Vector2(math.cos(radians), -math.sin(radians))

        self.radius = ALIEN_SIZE / 2
        self.health = 20
        self.state = "PATROL"
        self.patrol_timer = random.uniform(1.5, 3.5)

    def update(self, player, dt):
        to_player = player.position - self.position
        distance = self.position.distance_to(player.position)

        dot = -1.0
        if distance > 0:
            to_player_dir = to_player.normalize()
            dot = self.forward.dot(to_player_dir)

        if distance < DETECTION_RANGE and dot > FOV_THRESHOLD:
            self.state = "ATTACK"
        else:
            self.state = "PATROL"

        if self.state == "ATTACK" and distance > 0:
            direction = to_player.normalize()
            self.angle = math.degrees(math.atan2(-direction.y, direction.x))
            radians = math.radians(self.angle)
            self.forward = pygame.Vector2(math.cos(radians), -math.sin(radians))
            self.velocity = self.forward * (ALIEN_SPEED * 1.25)
        else:
            self.patrol_timer -= dt
            if self.patrol_timer <= 0:
                self.angle = random.uniform(0, 360)
                self.patrol_timer = random.uniform(1.5, 3.5)

            radians = math.radians(self.angle)
            self.forward = pygame.Vector2(math.cos(radians), -math.sin(radians))
            self.velocity = self.forward * (ALIEN_SPEED * 0.65)

        self.position += self.velocity * dt

        if self.position.x < self.radius:
            self.position.x = self.radius
            self.angle = 180 - self.angle
        elif self.position.x > WIDTH - self.radius:
            self.position.x = WIDTH - self.radius
            self.angle = 180 - self.angle

        if self.position.y < self.radius:
            self.position.y = self.radius
            self.angle = -self.angle
        elif self.position.y > HEIGHT - self.radius:
            self.position.y = HEIGHT - self.radius
            self.angle = -self.angle

    def draw(self):
        if self.state == "ATTACK":
            color = RED
        else:
            color = GREEN
        rect = pygame.Rect(0, 0, ALIEN_SIZE, ALIEN_SIZE)
        rect.center = (int(self.position.x), int(self.position.y))
        pygame.draw.rect(screen, color, rect)

        eye_pos = self.position + self.forward * 9
        eye_rect = pygame.Rect(0, 0, 6, 6)
        eye_rect.center = (int(eye_pos.x), int(eye_pos.y))
        pygame.draw.rect(screen, BLACK, eye_rect)


class LASER:
    def __init__(self, start_pos, target_pos, width):
        self.position = pygame.Vector2(start_pos)
        self.width = width
        self.radius = width / 2
        self.damage = LASER_DAMAGE

        direction = target_pos - self.position
        if direction.length() > 0:
            direction = direction.normalize()
        else:
            direction = pygame.Vector2(1, 0)

        self.velocity = direction * LASER_SPEED

    def update(self, dt):
        self.position += self.velocity * dt

    def draw(self):
        rect = pygame.Rect(0, 0, int(self.width), int(self.width))
        rect.center = (int(self.position.x), int(self.position.y))
        pygame.draw.rect(screen, YELLOW, rect)

    def is_off_screen(self):
        #check syntax pls
        return (self.position.x < -self.width or self.position.x > WIDTH + self.width or self.position.y < -self.width or self.position.y > HEIGHT + self.width)

def find_nearest_alien(player_pos, aliens):
    nearest = None
    shortest_dist = float("inf")
    for alien in aliens:
        dist = player_pos.distance_to(alien.position)
        if dist < shortest_dist:
            shortest_dist = dist
            nearest = alien
    return nearest

def check_collision(obj1, obj2):
    distance = obj1.position.distance_to(obj2.position)
    return distance <= (obj1.radius + obj2.radius)


async def main():
    game_state = "START"

    player = P1()
    aliens = []
    lasers = []
    score = 0
    elapsed_time = 0.0
    spawn_timer = 0.0
    spawn_interval = 2.0 
    fire_interval = 0.65
    shot_width = 8.0
    last_upgrade_tier = 0

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if game_state == "START" or game_state == "GAME_OVER":
                        player = P1()
                        aliens = []
                        lasers = []
                        score = 0
                        elapsed_time = 0.0
                        spawn_timer = 0.0
                        spawn_interval = 2.0
                        fire_interval = 0.65
                        shot_width = 8.0
                        last_upgrade_tier = 0

                        # First ones
                        for _ in range(4):
                            aliens.append(Alien(player.position))
                        game_state = "PLAYING"

                elif event.key == pygame.K_ESCAPE:
                    if game_state == "PLAYING":
                        game_state = "PAUSED"
                    elif game_state == "PAUSED":
                        game_state = "PLAYING"

            if event.type == pygame.KEYDOWN and game_state == "PLAYING":
                if event.key == pygame.K_l:
                    player.trigger_dash()

        if game_state == "PLAYING":
            elapsed_time += dt
            spawn_timer += dt

            current_tier = int(elapsed_time // 30)
            if current_tier > last_upgrade_tier:
                last_upgrade_tier = current_tier
                spawn_interval = max(0.45, spawn_interval * 0.80)
                fire_interval = max(0.18, fire_interval * 0.85)
                shot_width = min(28.0, shot_width + 3.0)

            if spawn_timer >= spawn_interval:
                spawn_timer = 0.0
                aliens.append(Alien(player.position))

            keys = pygame.key.get_pressed()
            player.update(keys, dt)

            if player.fire_timer <= 0 and len(aliens) > 0:
                nearest = find_nearest_alien(player.position, aliens)
                if nearest is not None:
                    lasers.append(LASER(player.position, nearest.position, shot_width))
                    player.fire_timer = fire_interval

            for alien in aliens:
                alien.update(player, dt)

            for laser in lasers:
                laser.update(dt)
            lasers = [l for l in lasers if not l.is_off_screen()]

            for laser in lasers[:]:
                for alien in aliens[:]:
                    if check_collision(laser, alien):
                        alien.health -= laser.damage
                        if laser in lasers:
                            lasers.remove(laser)
                        if alien.health <= 0 and alien in aliens:
                            aliens.remove(alien)
                            score += 10
                        break

            for alien in aliens:
                if check_collision(player, alien):
                    if player.damage_timer <= 0:
                        player.health -= 10
                        player.damage_timer = EVENT_TIME
                        if player.health <= 0:
                            player.health = 0
                            game_state = "GAME_OVER"

        screen.fill(BLACK)

        if game_state == "START":
            title_surf = big_font.render("HOUSTON'S PROBLEM", True, CYAN)
            inst1 = font.render("WASD -- Left-Click = Dash -- Esc = Pause", True, WHITE)
            start_prompt = font.render("Press ENTER to Start", True, YELLOW)

            screen.blit(title_surf, title_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 80)))
            screen.blit(inst1, inst1.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 15)))
            screen.blit(start_prompt, start_prompt.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 80)))

        else:
            for laser in lasers:
                laser.draw()
            for alien in aliens:
                alien.draw()
            player.draw()


            score_surf = font.render(f"Score = {score}", True, WHITE)
            screen.blit(score_surf, (15, 15))

            time_surf = font.render(f"Time: {elapsed_time:.1f}s", True, WHITE)
            screen.blit(time_surf, time_surf.get_rect(midtop=(WIDTH / 2, 15)))

            stats_surf = font.render(
                f"Spawn = {1/spawn_interval:.1f}/s -- Fire = {1/fire_interval:.1f}/s -- Width = {int(shot_width)}px",
                True,
                GRAY,
            )
            screen.blit(stats_surf, stats_surf.get_rect(topright=(WIDTH - 15, 15)))

            hp_color = GREEN if player.health > 30 else RED
            hp_surf = font.render(f"Health = {player.health} / {player.max_health}", True, hp_color)
            screen.blit(hp_surf, (15, HEIGHT - 35))

            if game_state == "PAUSED":
                pause_surf = big_font.render("PAUSED", True, YELLOW)
                screen.blit(pause_surf, pause_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 20)))
                screen.blit(resume_surf, resume_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 25)))

            elif game_state == "GAME_OVER":
                over_surf = big_font.render("GAME OVER", True, RED)
                final_surf = font.render(
                    f"Final Score: {score} -- Survived = {elapsed_time:.1f}s", True, WHITE
                )
                restart_surf = font.render("Press ENTER to Reset", True, YELLOW)
                screen.blit(over_surf, over_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 40)))
                screen.blit(final_surf, final_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 10)))
                screen.blit(restart_surf, restart_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 55)))

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
