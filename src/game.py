import arcade
import random
import sqlite3
import datetime
import time
import math
from constants import *

sqlite3.register_adapter(datetime.datetime, lambda dt: dt.isoformat())


class DatabaseManager:
    # работает с базой данных: сохраняет рекорды, загружает таблицу лидеров
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS high_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT,
                score INTEGER,
                date TEXT
            )
        """)
        self.conn.commit()

    def add_score(self, name, score):
        self.cursor.execute(
            "INSERT INTO high_scores (player_name, score, date) VALUES (?, ?, ?)",
            (name, score, datetime.datetime.now().isoformat())
        )
        self.conn.commit()

    def get_top_scores(self, limit=10):
        self.cursor.execute(
            "SELECT player_name, score, date FROM high_scores ORDER BY score DESC LIMIT ?",
            (limit,)
        )
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()


class Particle:
    # одна частица для эффектов: летит, исчезает, меняет прозрачность
    def __init__(self, x, y, color, size, lifetime, speed_x, speed_y):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.alpha = 255

    def update(self, delta_time):
        self.x += self.speed_x
        self.y += self.speed_y
        self.lifetime -= delta_time
        self.alpha = int(255 * (self.lifetime / self.max_lifetime))
        self.speed_y -= GRAVITY * 0.1
        self.speed_x *= FRICTION
        self.speed_y *= FRICTION

    def draw(self):
        color_with_alpha = (*self.color[:3], self.alpha)
        arcade.draw_circle_filled(self.x, self.y, self.size, color_with_alpha)

    def is_dead(self):
        return self.lifetime <= 0


class ParticleSystem:
    # управляет кучей частиц: создаёт взрывы, выстрелы, обновляет и рисует их
    def __init__(self):
        self.particles = []

    def emit(self, x, y, count, color, size_range=(2, 6),
             speed_range=(1, 5), lifetime_range=(0.5, 2.0), spread=360):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(*speed_range)
            size = random.uniform(*size_range)
            lifetime = random.uniform(*lifetime_range)

            speed_x = math.cos(angle) * speed
            speed_y = math.sin(angle) * speed

            particle = Particle(x, y, color, size, lifetime, speed_x, speed_y)
            self.particles.append(particle)

    def emit_explosion(self, x, y, color=(255, 200, 50), count=None):
        if count is None:
            count = EXPLOSION_PARTICLE_COUNT

        colors = [
            (255, 200, 50),
            (255, 100, 0),
            (255, 50, 0),
            (200, 200, 200),
        ]

        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            size = random.uniform(2, 8)
            lifetime = random.uniform(0.5, 2.0)
            color = random.choice(colors)

            speed_x = math.cos(angle) * speed
            speed_y = math.sin(angle) * speed

            particle = Particle(x, y, color, size, lifetime, speed_x, speed_y)
            self.particles.append(particle)

    def update(self, delta_time):
        for particle in self.particles[:]:
            particle.update(delta_time)
            if particle.is_dead():
                self.particles.remove(particle)

    def draw(self):
        for particle in self.particles:
            particle.draw()

    def clear(self):
        self.particles.clear()


class Boss(arcade.Sprite):
    # босс: появляется каждые 5 волн, двигается, стреляет, имеет здоровье и полоску хп
    def __init__(self, game):
        super().__init__(TEX_BOSS, 1.0)
        self.game = game
        self.center_x = SCREEN_WIDTH / 2
        self.center_y = SCREEN_HEIGHT - 150
        self.health = BOSS_HEALTH
        self.max_health = BOSS_HEALTH
        self.speed = BOSS_SPEED
        self.shoot_interval = BOSS_SHOOT_INTERVAL
        self.shoot_timer = 0
        self.move_timer = 0
        self.move_direction = 1
        self.animation_timer = 0
        self.attack_pattern = 0
        self.is_hit = False
        self.hit_timer = 0

        try:
            self.textures = [arcade.load_texture(TEX_BOSS)]
        except:
            self.textures = [arcade.load_texture(TEX_BOSS)]

        self.texture = self.textures[0]
        self.width = 120
        self.height = 100

    def update(self, delta_time):
        self.animation_timer += delta_time
        if self.animation_timer > 0.1:
            self.animation_timer = 0

        if self.is_hit:
            self.hit_timer -= delta_time
            if self.hit_timer <= 0:
                self.is_hit = False

        self.move_timer += delta_time * 60
        if self.move_timer > BOSS_MOVE_INTERVAL:
            self.move_direction *= -1
            self.move_timer = 0

        self.center_x += self.move_direction * self.speed

        if self.center_x < 80:
            self.center_x = 80
            self.move_direction = 1
        if self.center_x > SCREEN_WIDTH - 80:
            self.center_x = SCREEN_WIDTH - 80
            self.move_direction = -1

        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_interval:
            self.shoot()
            self.shoot_timer = 0

        if random.random() < 0.01:
            self.attack_pattern = random.randint(0, BOSS_ATTACK_PATTERNS - 1)

    def shoot(self):
        if self.attack_pattern == 0:
            bullet = EnemyBullet(self.center_x, self.bottom, speed=-6)
            self.game.enemy_bullet_list.append(bullet)
        elif self.attack_pattern == 1:
            for offset in [-30, 0, 30]:
                bullet = EnemyBullet(self.center_x + offset, self.bottom, speed=-5)
                bullet.change_x = offset * 0.05
                self.game.enemy_bullet_list.append(bullet)
        elif self.attack_pattern == 2:
            for i in range(8):
                angle = (i / 8) * 2 * math.pi + math.pi / 2
                bullet = EnemyBullet(self.center_x, self.center_y, speed=0)
                bullet.change_x = math.cos(angle) * 4
                bullet.change_y = math.sin(angle) * 4
                self.game.enemy_bullet_list.append(bullet)

    def hit(self, damage=1):
        self.health -= damage
        self.is_hit = True
        self.hit_timer = 0.1

        if self.game:
            self.game.particle_system.emit_explosion(
                self.center_x + random.uniform(-40, 40),
                self.center_y + random.uniform(-30, 30),
                color=(255, 100, 0),
                count=10
            )

        if self.health <= 0:
            return True
        return False

    def draw_health_bar(self):
        bar_width = 100
        bar_height = 10
        health_percent = self.health / self.max_health

        arcade.draw_rect_filled(
            arcade.XYWH(self.center_x, SCREEN_HEIGHT - 30, bar_width, bar_height),
            arcade.color.RED
        )
        arcade.draw_rect_filled(
            arcade.XYWH(self.center_x - bar_width / 2 + bar_width * health_percent / 2,
                        SCREEN_HEIGHT - 30, bar_width * health_percent, bar_height),
            arcade.color.GREEN
        )


class WarShip(arcade.Sprite):
    # корабль игрока: следует за мышкой, не вылетает за границы экрана
    def update(self, delta_time: float = 1 / 60):
        if self.top > SCREEN_HEIGHT:
            self.top = SCREEN_HEIGHT
        if self.bottom < 0:
            self.bottom = 0
        if self.right > SCREEN_WIDTH:
            self.right = SCREEN_WIDTH
        if self.left < 0:
            self.left = 0


class Bullet(arcade.Sprite):
    # пуля игрока: летит вверх, исчезает за экраном
    def __init__(self, speed):
        super().__init__(TEX_BULLET, 0.8)
        self.change_y = speed

    def update(self, delta_time: float = 1 / 60):
        self.center_y += self.change_y


class EnemyBullet(arcade.Sprite):
    # пуля врага: летит вниз, исчезает за экраном
    def __init__(self, x, y, speed=-3):
        super().__init__(TEX_ENEMY_BULLET, 0.5)
        self.center_x = x
        self.center_y = y
        self.change_y = speed
        self.change_x = 0

    def update(self, delta_time: float = 1 / 60):
        self.center_y += self.change_y
        self.center_x += self.change_x
        if self.top < 0 or self.bottom > SCREEN_HEIGHT + 100:
            self.remove_from_sprite_lists()


class Enemy(arcade.Sprite):
    # обычный враг: летит вниз, анимируется (мигает), исчезает внизу
    def __init__(self, speed):
        super().__init__()
        self.textures = [
            arcade.load_texture(TEX_ENEMY_1),
            arcade.load_texture(TEX_ENEMY_2)
        ]
        self.texture = self.textures[0]
        self.change_y = speed
        self.animation_counter = 0

    def update(self, delta_time: float = 1 / 60):
        self.center_y += self.change_y
        if self.top < 0:
            self.remove_from_sprite_lists()
        self.animation_counter += 1
        if self.animation_counter % 10 == 0:
            self.texture = self.textures[1] if self.texture == self.textures[0] else self.textures[0]


class ToughEnemy(Enemy):
    # усиленный враг: как обычный, но имеет здоровье и может стрелять в игрока
    def __init__(self, speed, game, shoot_interval):
        super().__init__(speed)
        self.texture = arcade.load_texture(TEX_TOUGH_ENEMY)
        self.textures = [self.texture]
        self.health = TOUGH_ENEMY_HEALTH
        self.max_health = TOUGH_ENEMY_HEALTH
        self.shoot_interval = shoot_interval
        self.shoot_timer = random.randint(0, self.shoot_interval)
        self.game = game

    def hit(self, damage=1):
        self.health -= damage
        if self.health <= 0:
            self.remove_from_sprite_lists()
            return True
        return False

    def update(self, delta_time: float = 1 / 60):
        self.center_y += self.change_y
        if self.top < 0:
            self.remove_from_sprite_lists()
        self.shoot_timer -= 1
        if self.shoot_timer <= 0 and self.game is not None:
            self.shoot()
            self.shoot_timer = self.shoot_interval

    def shoot(self):
        bullet = EnemyBullet(self.center_x, self.bottom)
        self.game.enemy_bullet_list.append(bullet)


class Wall(arcade.Sprite):
    # стена: может быть неразрушимой, разрушаемой или проходимой, летит вниз
    def __init__(self, texture_path, destructible=False, passable=False, health=1, speed=0):
        super().__init__(texture_path, 0.5)
        self.destructible = destructible
        self.passable = passable
        self.health = health
        self.max_health = health
        self.change_y = speed

    def update(self, delta_time: float = 1 / 60):
        self.center_y += self.change_y
        if self.top < 0:
            self.remove_from_sprite_lists()

    def hit(self, damage=1):
        if self.destructible:
            self.health -= damage
            if self.health <= 0:
                self.remove_from_sprite_lists()
                return True
        return False


class MyGame(arcade.Window):
    # главный класс игры
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        self.background_sprite = None
        self.player = None
        self.bullet_list = None
        self.enemy_bullet_list = None
        self.enemy_list = None
        self.wall_list = None
        self.last_shot_time = 0
        self.kill_count = 0
        self.score = 0
        self.game_over_flag = False
        self.db = DatabaseManager()

        self.current_enemy_speed = ENEMY_BASE_SPEED
        self.current_wall_speed = ENEMY_BASE_SPEED
        self.current_bullet_speed = BULLET_BASE_SPEED
        self.current_enemy_shoot_interval = ENEMY_SHOOT_BASE_INTERVAL
        self.last_score_threshold = 0

        self.wave_number = 0
        self.wave_budget = 0
        self.wave_spawned = False
        self.wave_cooldown = 0

        self.show_leaderboard = False
        self.waiting_for_name = False
        self.input_name = ""
        self.name_saved = False

        self.boss = None
        self.boss_active = False
        self.boss_defeated = False

        self.camera = None
        self.in_boss_room = False
        self.boss_room_transition = 0

        self.particle_system = ParticleSystem()

        self.lose_sound = None
        self.victory_sound = None
        try:
            self.lose_sound = arcade.load_sound("sounds/lose.mp3")
            self.victory_sound = arcade.load_sound("sounds/victory.wav")
        except:
            print("Warning: Could not load sound files")

        # ПАУЗА ПОСЛЕ ПОБЕДЫ НАД БОССОМ
        self.victory_pause = False
        self.victory_timer = 0

    def setup(self):
        self.background_sprite = arcade.Sprite(TEX_BACKGROUND)
        self.background_sprite.center_x = SCREEN_WIDTH / 2
        self.background_sprite.center_y = SCREEN_HEIGHT / 2

        self.player = WarShip(TEX_PLAYER, 0.5)
        self.player.center_x = SCREEN_WIDTH / 2
        self.player.center_y = 100

        self.bullet_list = arcade.SpriteList()
        self.enemy_bullet_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()

        self.score = 0
        self.kill_count = 0
        self.current_enemy_speed = ENEMY_BASE_SPEED
        self.current_wall_speed = ENEMY_BASE_SPEED
        self.current_bullet_speed = BULLET_BASE_SPEED
        self.current_enemy_shoot_interval = ENEMY_SHOOT_BASE_INTERVAL
        self.last_score_threshold = 0
        self.game_over_flag = False
        self.waiting_for_name = False
        self.input_name = ""
        self.name_saved = False

        self.wave_number = 0
        self.wave_cooldown = 0

        self.boss = None
        self.boss_active = False
        self.boss_defeated = False
        self.in_boss_room = False
        self.boss_room_transition = 0

        self.camera = arcade.Camera2D()

        self.particle_system.clear()

        self.start_next_wave()

        self.set_mouse_visible(False)

    def start_next_wave(self):
        self.wave_number += 1

        if self.wave_number % BOSS_WAVE_INTERVAL == 0:
            self.spawn_boss()
        else:
            self.wave_budget = BASE_WAVE_BUDGET + (self.wave_number - 1) * BUDGET_INCREASE_PER_WAVE
            self.spawn_wave()
            self.wave_spawned = True
            self.wave_cooldown = 0

    def spawn_boss(self):
        self.boss_active = True
        self.boss = Boss(self)
        self.in_boss_room = True
        self.boss_room_transition = 60
        self.wave_spawned = True

        self.particle_system.emit(
            SCREEN_WIDTH / 2, SCREEN_HEIGHT - 150,
            count=BOSS_EXPLOSION_PARTICLE_COUNT,
            color=(100, 200, 255),
            size_range=(5, 15),
            speed_range=(3, 10),
            lifetime_range=(1.0, 3.0)
        )

    def exit_boss_room(self):
        self.in_boss_room = False
        self.boss_active = False
        self.boss_defeated = True
        self.boss = None
        self.boss_room_transition = 60
        self.score += SCORE_PER_BOSS
        self.enemy_bullet_list.clear()

        self.particle_system.clear()

        self.particle_system.emit_explosion(
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
            color=(255, 215, 0),
            count=50
        )

        if self.victory_sound:
            arcade.play_sound(self.victory_sound)

        self.victory_pause = True
        self.victory_timer = 180

    def is_position_free(self, x, y, margin=30):
        for wall in self.wall_list:
            if abs(wall.center_x - x) < margin and abs(wall.center_y - y) < margin:
                return False
        return True

    def is_behind_wall(self, x, y):
        for wall in self.wall_list:
            if not wall.passable:
                wall_left = wall.center_x - wall.width / 2
                wall_right = wall.center_x + wall.width / 2
                enemy_left = x - 20
                enemy_right = x + 20

                if (enemy_right > wall_left and enemy_left < wall_right):
                    if wall.center_y >= y - 50:
                        return True
        return False

    def spawn_wave(self):
        budget = self.wave_budget
        wall_budget_limit = budget * MAX_WALL_PERCENT
        wall_cost_spent = 0

        attempts = 0
        while budget > 0 and attempts < 1000:
            attempts += 1
            r = random.random()
            can_spawn_tough = self.score >= TOUGH_ENEMY_SPAWN_SCORE

            if r < 0.4 and budget >= COST_NORMAL_ENEMY:
                x = random.randint(20, SCREEN_WIDTH - 20)
                y = SCREEN_HEIGHT + random.randint(20, 100)
                if self.is_position_free(x, y) and not self.is_behind_wall(x, y):
                    enemy = Enemy(self.current_enemy_speed)
                    enemy.center_x = x
                    enemy.center_y = y
                    self.enemy_list.append(enemy)
                    budget -= COST_NORMAL_ENEMY

            elif r < 0.6 and can_spawn_tough and budget >= COST_TOUGH_ENEMY:
                x = random.randint(20, SCREEN_WIDTH - 20)
                y = SCREEN_HEIGHT + random.randint(20, 100)
                if self.is_position_free(x, y) and not self.is_behind_wall(x, y):
                    enemy = ToughEnemy(self.current_enemy_speed, self, self.current_enemy_shoot_interval)
                    enemy.center_x = x
                    enemy.center_y = y
                    self.enemy_list.append(enemy)
                    budget -= COST_TOUGH_ENEMY

            else:
                if budget >= COST_WALL_INDESTR and wall_cost_spent < wall_budget_limit:
                    wall_type = random.choice(['indestructible', 'destructible', 'passable'])
                    if wall_type == 'indestructible':
                        wall = Wall(TEX_WALL, destructible=False, passable=False, health=1,
                                    speed=self.current_wall_speed)
                        cost = COST_WALL_INDESTR
                    elif wall_type == 'destructible':
                        wall = Wall(TEX_WALL_DESTR, destructible=True, passable=False, health=WALL_DESTR_HEALTH,
                                    speed=self.current_wall_speed)
                        cost = COST_WALL_DESTR
                    else:
                        wall = Wall(TEX_WALL_PASS, destructible=False, passable=True, health=1,
                                    speed=self.current_wall_speed)
                        cost = COST_WALL_PASS

                    x = random.randint(50, SCREEN_WIDTH - 50)
                    y = SCREEN_HEIGHT + random.randint(20, 100)
                    if self.is_position_free(x, y) and wall_cost_spent + cost <= wall_budget_limit:
                        wall.center_x = x
                        wall.center_y = y
                        self.wall_list.append(wall)
                        wall_cost_spent += cost
                        budget -= cost
                    else:
                        if budget >= COST_NORMAL_ENEMY:
                            x = random.randint(20, SCREEN_WIDTH - 20)
                            y = SCREEN_HEIGHT + random.randint(20, 100)
                            if self.is_position_free(x, y) and not self.is_behind_wall(x, y):
                                enemy = Enemy(self.current_enemy_speed)
                                enemy.center_x = x
                                enemy.center_y = y
                                self.enemy_list.append(enemy)
                                budget -= COST_NORMAL_ENEMY
                else:
                    if budget >= COST_NORMAL_ENEMY:
                        x = random.randint(20, SCREEN_WIDTH - 20)
                        y = SCREEN_HEIGHT + random.randint(20, 100)
                        if self.is_position_free(x, y) and not self.is_behind_wall(x, y):
                            enemy = Enemy(self.current_enemy_speed)
                            enemy.center_x = x
                            enemy.center_y = y
                            self.enemy_list.append(enemy)
                            budget -= COST_NORMAL_ENEMY
                    else:
                        break

    def check_score_progression(self):
        new_threshold = self.score // 100
        if new_threshold > self.last_score_threshold:
            self.current_enemy_speed += SPEED_INCREASE_PER_100_SCORE
            self.current_wall_speed += SPEED_INCREASE_PER_100_SCORE
            self.current_bullet_speed += BULLET_SPEED_INCREASE_PER_100_SCORE
            self.current_enemy_shoot_interval += ENEMY_SHOOT_INCREASE_PER_100_SCORE

            for enemy in self.enemy_list:
                enemy.change_y = self.current_enemy_speed
                if isinstance(enemy, ToughEnemy):
                    enemy.shoot_interval = self.current_enemy_shoot_interval

            for wall in self.wall_list:
                wall.change_y = self.current_wall_speed

            self.last_score_threshold = new_threshold

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT and not self.game_over_flag and not self.waiting_for_name:
            current_time = time.time()
            if current_time - self.last_shot_time >= SHOT_COOLDOWN:
                bullet = Bullet(self.current_bullet_speed)
                bullet.center_x = self.player.center_x
                bullet.bottom = self.player.top
                self.bullet_list.append(bullet)
                self.last_shot_time = current_time

                self.particle_system.emit(
                    self.player.center_x, self.player.top,
                    count=5,
                    color=(100, 200, 255),
                    size_range=(2, 4),
                    speed_range=(2, 5),
                    lifetime_range=(0.2, 0.5)
                )

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.game_over_flag and not self.waiting_for_name and not self.victory_pause:
            self.player.center_x = x
            self.player.center_y = y

    def on_key_press(self, key, modifiers):
        if self.victory_pause:
            if key == arcade.key.SPACE or key == arcade.key.ENTER:
                self.victory_pause = False
                self.start_next_wave()
            return

        if key == arcade.key.ESCAPE and not self.game_over_flag and not self.waiting_for_name:
            self.return_to_menu()
            return

        if key == arcade.key.TAB and not self.waiting_for_name:
            self.show_leaderboard = not self.show_leaderboard
            return

        if self.game_over_flag and not self.waiting_for_name and not self.name_saved and key == arcade.key.ENTER:
            self.waiting_for_name = True
            self.input_name = ""
            return

        if self.waiting_for_name:
            if key == arcade.key.ENTER:
                name = self.input_name if self.input_name else "Аноним"
                self.db.add_score(name, self.score)
                self.waiting_for_name = False
                self.name_saved = True
                self.show_leaderboard = True
            elif key == arcade.key.BACKSPACE:
                self.input_name = self.input_name[:-1]
            elif key == arcade.key.ESCAPE:
                self.waiting_for_name = False
            else:
                if 97 <= key <= 122 or 65 <= key <= 90 or 48 <= key <= 57 or key == 32:
                    self.input_name += chr(key)
            return

        if key == arcade.key.R and self.game_over_flag and not self.waiting_for_name:
            self.setup()

    def return_to_menu(self):
        self.close()
        from main import main as menu_main
        menu_main()

    def on_draw(self):
        self.clear()
        self.camera.use()

        arcade.draw_sprite(self.background_sprite)
        arcade.draw_sprite(self.player)
        self.bullet_list.draw()
        self.enemy_bullet_list.draw()
        self.enemy_list.draw()
        self.wall_list.draw()

        if self.boss:
            arcade.draw_sprite(self.boss)
            self.boss.draw_health_bar()

        self.particle_system.draw()

        self.camera.use()
        arcade.draw_text(f"Счёт: {self.score}", 10, SCREEN_HEIGHT - 30, arcade.color.YELLOW, 20)
        arcade.draw_text(f"Волна: {self.wave_number}", 10, SCREEN_HEIGHT - 60, arcade.color.YELLOW, 20)

        if self.boss_active:
            arcade.draw_text("БОСС!", SCREEN_WIDTH / 2, SCREEN_HEIGHT - 30,
                             arcade.color.RED, 30, anchor_x="center")

        if self.victory_pause:
            arcade.draw_lrbt_rectangle_filled(
                0, SCREEN_WIDTH, 0, SCREEN_HEIGHT,
                (0, 0, 0, 180)
            )

            arcade.draw_text("ПОБЕДА!", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50,
                             arcade.color.GOLD, 50, anchor_x="center")
            arcade.draw_text("Босс повержен!", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                             arcade.color.WHITE, 24, anchor_x="center")
            arcade.draw_text("Пробел для продолжения",
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 60,
                             arcade.color.GRAY, 18, anchor_x="center")
            return

        if self.game_over_flag:
            arcade.draw_text("ИГРА ОКОНЧЕНА", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                             arcade.color.RED, 50, anchor_x="center")
            if not self.waiting_for_name and not self.name_saved:
                arcade.draw_text("Нажмите ENTER для ввода имени, R для рестарта",
                                 SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50,
                                 arcade.color.WHITE, 16, anchor_x="center")
                arcade.draw_text("ESC - главное меню",
                                 SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 80,
                                 arcade.color.GRAY, 14, anchor_x="center")
            elif self.waiting_for_name:
                arcade.draw_text("Введите имя:", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 80,
                                 arcade.color.YELLOW, 20, anchor_x="center")
                arcade.draw_text(self.input_name + "_", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 120,
                                 arcade.color.WHITE, 24, anchor_x="center")
                arcade.draw_text("esc - назад | ENTER - сохранить",
                                 SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 160,
                                 arcade.color.GRAY, 14, anchor_x="center")

        if self.show_leaderboard:
            arcade.draw_lrbt_rectangle_filled(
                200, SCREEN_WIDTH - 200, 150, SCREEN_HEIGHT - 100,
                (0, 0, 0, 200)
            )
            arcade.draw_text("ТАБЛИЦА ЛИДЕРОВ", SCREEN_WIDTH / 2, SCREEN_HEIGHT - 150,
                             arcade.color.GOLD, 28, anchor_x="center")
            scores = self.db.get_top_scores(10)
            y = SCREEN_HEIGHT - 200
            for i, (name, score, date) in enumerate(scores):
                arcade.draw_text(f"{i + 1}. {name} - {score}", SCREEN_WIDTH / 2, y,
                                 arcade.color.WHITE, 18, anchor_x="center")
                y -= 25

    def on_update(self, delta_time):
        if self.game_over_flag or self.waiting_for_name or self.victory_pause:
            return

        if self.in_boss_room and self.boss_room_transition > 0:
            self.boss_room_transition -= 1
            zoom = 1.0 + (self.boss_room_transition / 60) * 0.5
            self.camera.zoom = zoom
        elif self.boss_defeated and self.boss_room_transition > 0:
            self.boss_room_transition -= 1
            zoom = 1.0 + (self.boss_room_transition / 60) * 0.5
            self.camera.zoom = zoom
            if self.boss_room_transition <= 0:
                self.boss_defeated = False
        else:
            self.camera.zoom = 1.0

        self.player.update(delta_time)
        self.bullet_list.update()
        self.enemy_bullet_list.update()
        self.enemy_list.update()
        self.wall_list.update()

        if self.boss:
            self.boss.update(delta_time)

            if arcade.check_for_collision(self.player, self.boss):
                self.game_over()
                return

        self.particle_system.update(delta_time)

        self.check_score_progression()

        if self.wave_spawned and not self.boss_active and len(self.enemy_list) == 0 and len(self.wall_list) == 0:
            self.wave_spawned = False
            self.wave_cooldown = WAVE_COOLDOWN_FRAMES

        if not self.wave_spawned and self.wave_cooldown > 0:
            self.wave_cooldown -= 1
            if self.wave_cooldown <= 0:
                self.start_next_wave()

        for enemy in self.enemy_list:
            if enemy.bottom <= 0:
                self.game_over()
                return

        if arcade.check_for_collision_with_list(self.player, self.enemy_bullet_list):
            self.game_over()
            return

        for wall in self.wall_list:
            if not wall.passable and arcade.check_for_collision(self.player, wall):
                self.game_over()
                return

        for bullet in self.bullet_list:
            hit_walls = arcade.check_for_collision_with_list(bullet, self.wall_list)
            for wall in hit_walls:
                if not wall.passable:
                    if wall.hit():
                        self.score += SCORE_PER_WALL
                        self.check_score_progression()
                        self.particle_system.emit_explosion(
                            wall.center_x, wall.center_y,
                            color=(150, 150, 150),
                            count=15
                        )
                    bullet.remove_from_sprite_lists()
                    break
                else:
                    new_bullet = EnemyBullet(
                        bullet.center_x,
                        bullet.bottom,
                        speed=-1.5 * self.current_bullet_speed
                    )
                    self.enemy_bullet_list.append(new_bullet)
                    bullet.remove_from_sprite_lists()
                    break

            if self.boss and arcade.check_for_collision(bullet, self.boss):
                if self.boss.hit(bullet.damage if hasattr(bullet, 'damage') else 1):
                    self.particle_system.emit_explosion(
                        self.boss.center_x, self.boss.center_y,
                        color=(255, 100, 0),
                        count=BOSS_EXPLOSION_PARTICLE_COUNT
                    )
                    self.exit_boss_room()
                bullet.remove_from_sprite_lists()
                continue

            hit_enemies = arcade.check_for_collision_with_list(bullet, self.enemy_list)
            for enemy in hit_enemies:
                if isinstance(enemy, ToughEnemy):
                    if enemy.hit():
                        self.score += SCORE_PER_ENEMY * 2
                        self.kill_count += 1
                        self.check_score_progression()
                        self.particle_system.emit_explosion(
                            enemy.center_x, enemy.center_y,
                            color=(255, 100, 0),
                            count=20
                        )
                else:
                    enemy.remove_from_sprite_lists()
                    self.score += SCORE_PER_ENEMY
                    self.kill_count += 1
                    self.check_score_progression()
                    self.particle_system.emit_explosion(
                        enemy.center_x, enemy.center_y,
                        color=(255, 200, 50),
                        count=15
                    )
                bullet.remove_from_sprite_lists()
                break

            if bullet.bottom > SCREEN_HEIGHT:
                bullet.remove_from_sprite_lists()

        for bullet in self.enemy_bullet_list:
            hit_walls = arcade.check_for_collision_with_list(bullet, self.wall_list)
            for wall in hit_walls:
                if not wall.passable:
                    bullet.remove_from_sprite_lists()
                    break

    def game_over(self):
        self.game_over_flag = True
        self.name_saved = False

        if self.lose_sound:
            arcade.play_sound(self.lose_sound)

        self.particle_system.emit_explosion(
            self.player.center_x, self.player.center_y,
            color=(100, 200, 255),
            count=50
        )

    def close_db(self):
        self.db.close()


def main():
    window = MyGame()
    window.setup()
    arcade.run()
    window.close_db()


if __name__ == "__main__":
    main()
