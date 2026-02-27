import arcade
import random
import sqlite3
import datetime
import time

sqlite3.register_adapter(datetime.datetime, lambda dt: dt.isoformat())

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "KosmicheskieZashitniki"

ENEMY_BASE_SPEED = -1
BULLET_BASE_SPEED = 5
ENEMY_SHOOT_BASE_INTERVAL = 90
SHOT_COOLDOWN = 0.1
TOUGH_ENEMY_HEALTH = 3
WALL_DESTR_HEALTH = 3
TOUGH_ENEMY_SPAWN_SCORE = 1000
TOUGH_ENEMY_SPAWN_CHANCE = 0.2

SCORE_PER_ENEMY = 10
SCORE_PER_WALL = 20

SPEED_INCREASE_PER_100_SCORE = -0.05
BULLET_SPEED_INCREASE_PER_100_SCORE = 0.01
ENEMY_SHOOT_INCREASE_PER_100_SCORE = 2

COST_NORMAL_ENEMY = 1
COST_TOUGH_ENEMY = 10
COST_WALL_INDESTR = 3
COST_WALL_DESTR = 5
COST_WALL_PASS = 4

BASE_WAVE_BUDGET = 15
BUDGET_INCREASE_PER_WAVE = 5
MAX_WALL_PERCENT = 0.2
WAVE_COOLDOWN_FRAMES = 120

TEX_BACKGROUND = "images/space_background.png"
TEX_PLAYER = "images/x-wing.png"
TEX_BULLET = "images/laser.png"
TEX_ENEMY_BULLET = "images/laser_enemy.png"
TEX_ENEMY_1 = "images/tie_fighter1.png"
TEX_ENEMY_2 = "images/tie_fighter2.png"
TEX_TOUGH_ENEMY = "images/x-wing_enemy.png"
TEX_WALL = "images/Wall.png"
TEX_WALL_DESTR = "images/Wall_shoot.png"
TEX_WALL_PASS = "images/Wall_pass.png"

DB_NAME = "game_data.db"

class DatabaseManager:
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



class WarShip(arcade.Sprite):
    def update(self, delta_time: float = 1/60):
        if self.top > SCREEN_HEIGHT:
            self.top = SCREEN_HEIGHT
        if self.bottom < 0:
            self.bottom = 0
        if self.right > SCREEN_WIDTH:
            self.right = SCREEN_WIDTH
        if self.left < 0:
            self.left = 0


class Bullet(arcade.Sprite):
    def __init__(self, speed):
        super().__init__(TEX_BULLET, 0.8)
        self.change_y = speed

    def update(self, delta_time: float = 1/60):
        self.center_y += self.change_y


class EnemyBullet(arcade.Sprite):
    def __init__(self, x, y, speed=-3):
        super().__init__(TEX_ENEMY_BULLET, 0.5)
        self.center_x = x
        self.center_y = y
        self.change_y = speed

    def update(self, delta_time: float = 1/60):
        self.center_y += self.change_y
        if self.top < 0:
            self.remove_from_sprite_lists()


class Enemy(arcade.Sprite):
    def __init__(self, speed):
        super().__init__()
        self.textures = [
            arcade.load_texture(TEX_ENEMY_1),
            arcade.load_texture(TEX_ENEMY_2)
        ]
        self.texture = self.textures[0]
        self.change_y = speed
        self.animation_counter = 0

    def update(self, delta_time: float = 1/60):
        self.center_y += self.change_y
        if self.top < 0:
            self.remove_from_sprite_lists()
        self.animation_counter += 1
        if self.animation_counter % 10 == 0:
            self.texture = self.textures[1] if self.texture == self.textures[0] else self.textures[0]


class ToughEnemy(Enemy):
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

    def update(self, delta_time: float = 1/60):
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
    def __init__(self, texture_path, destructible=False, passable=False, health=1, speed=0):
        super().__init__(texture_path, 0.5)
        self.destructible = destructible
        self.passable = passable
        self.health = health
        self.max_health = health
        self.change_y = speed

    def update(self, delta_time: float = 1/60):
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

    def setup(self):
        self.background_sprite = arcade.Sprite(TEX_BACKGROUND)
        self.background_sprite.center_x = SCREEN_WIDTH / 2
        self.background_sprite.center_y = SCREEN_HEIGHT / 2

        self.player = WarShip(TEX_PLAYER, 0.5)
        self.player.center_x = SCREEN_WIDTH / 2
        self.player.center_y = SCREEN_HEIGHT / 2

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
        self.start_next_wave()

        self.set_mouse_visible(False)

    def start_next_wave(self):
        self.wave_number += 1
        self.wave_budget = BASE_WAVE_BUDGET + (self.wave_number - 1) * BUDGET_INCREASE_PER_WAVE
        self.spawn_wave()
        self.wave_spawned = True
        self.wave_cooldown = 0

    def is_position_free(self, x, y, margin=30):
        for wall in self.wall_list:
            if abs(wall.center_x - x) < margin and abs(wall.center_y - y) < margin:
                return False
        return True

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
                if self.is_position_free(x, y):
                    enemy = Enemy(self.current_enemy_speed)
                    enemy.center_x = x
                    enemy.center_y = y
                    self.enemy_list.append(enemy)
                    budget -= COST_NORMAL_ENEMY
            elif r < 0.6 and can_spawn_tough and budget >= COST_TOUGH_ENEMY:
                x = random.randint(20, SCREEN_WIDTH - 20)
                y = SCREEN_HEIGHT + random.randint(20, 100)
                if self.is_position_free(x, y):
                    enemy = ToughEnemy(self.current_enemy_speed, self, self.current_enemy_shoot_interval)
                    enemy.center_x = x
                    enemy.center_y = y
                    self.enemy_list.append(enemy)
                    budget -= COST_TOUGH_ENEMY
            else:
                if budget >= COST_WALL_INDESTR and wall_cost_spent < wall_budget_limit:
                    wall_type = random.choice(['indestructible', 'destructible', 'passable'])
                    if wall_type == 'indestructible':
                        wall = Wall(TEX_WALL, destructible=False, passable=False, health=1, speed=self.current_wall_speed)
                        cost = COST_WALL_INDESTR
                    elif wall_type == 'destructible':
                        wall = Wall(TEX_WALL_DESTR, destructible=True, passable=False, health=WALL_DESTR_HEALTH, speed=self.current_wall_speed)
                        cost = COST_WALL_DESTR
                    else:
                        wall = Wall(TEX_WALL_PASS, destructible=False, passable=True, health=1, speed=self.current_wall_speed)
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
                            if self.is_position_free(x, y):
                                enemy = Enemy(self.current_enemy_speed)
                                enemy.center_x = x
                                enemy.center_y = y
                                self.enemy_list.append(enemy)
                                budget -= COST_NORMAL_ENEMY
                else:
                    if budget >= COST_NORMAL_ENEMY:
                        x = random.randint(20, SCREEN_WIDTH - 20)
                        y = SCREEN_HEIGHT + random.randint(20, 100)
                        if self.is_position_free(x, y):
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
                bullet.center_x = x
                bullet.bottom = self.player.top
                self.bullet_list.append(bullet)
                self.last_shot_time = current_time

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.game_over_flag and not self.waiting_for_name:
            self.player.center_x = x
            self.player.center_y = y

    def on_key_press(self, key, modifiers):
        if key == arcade.key.TAB and not self.waiting_for_name:
            self.show_leaderboard = not self.show_leaderboard
            return

        if self.game_over_flag and not self.waiting_for_name and not self.name_saved and key == arcade.key.ENTER:
            self.waiting_for_name = True
            self.input_name = ""
            return

        if self.waiting_for_name:
            if key == arcade.key.ENTER:
                name = self.input_name if self.input_name else "Anonymous"
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

    def on_draw(self):
        self.clear()
        arcade.draw_sprite(self.background_sprite)
        arcade.draw_sprite(self.player)
        self.bullet_list.draw()
        self.enemy_bullet_list.draw()
        self.enemy_list.draw()
        self.wall_list.draw()

        arcade.draw_text(f"Score: {self.score}", 10, SCREEN_HEIGHT - 30, arcade.color.WHITE, 20)
        arcade.draw_text(f"Wave: {self.wave_number}", 10, SCREEN_HEIGHT - 60, arcade.color.YELLOW, 20)

        if self.game_over_flag:
            arcade.draw_text("GAME OVER", SCREEN_WIDTH/2, SCREEN_HEIGHT/2,
                             arcade.color.RED, 50, anchor_x="center")
            if not self.waiting_for_name and not self.name_saved:
                arcade.draw_text("Нажмите ENTER для ввода имени, R для рестарта",
                                 SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 50,
                                 arcade.color.WHITE, 16, anchor_x="center")
            elif self.waiting_for_name:
                arcade.draw_text("Введите имя:", SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 80,
                                 arcade.color.YELLOW, 20, anchor_x="center")
                arcade.draw_text(self.input_name + "_", SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 120,
                                 arcade.color.WHITE, 24, anchor_x="center")

        if self.show_leaderboard:
            arcade.draw_lrbt_rectangle_filled(
                200, SCREEN_WIDTH - 200, 150, SCREEN_HEIGHT - 100,
                (0, 0, 0, 200)
            )
            arcade.draw_text("ЛИДЕРЫ", SCREEN_WIDTH/2, SCREEN_HEIGHT - 150,
                             arcade.color.GOLD, 28, anchor_x="center")
            scores = self.db.get_top_scores(10)
            y = SCREEN_HEIGHT - 200
            for i, (name, score, date) in enumerate(scores):
                arcade.draw_text(f"{i+1}. {name} - {score}", SCREEN_WIDTH/2, y,
                                 arcade.color.WHITE, 18, anchor_x="center")
                y -= 25

    def on_update(self, delta_time):
        if self.game_over_flag or self.waiting_for_name:
            return

        self.player.update(delta_time)
        self.bullet_list.update()
        self.enemy_bullet_list.update()
        self.enemy_list.update()
        self.wall_list.update()

        self.check_score_progression()

        if self.wave_spawned and len(self.enemy_list) == 0 and len(self.wall_list) == 0:
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

            hit_enemies = arcade.check_for_collision_with_list(bullet, self.enemy_list)
            for enemy in hit_enemies:
                if isinstance(enemy, ToughEnemy):
                    if enemy.hit():
                        self.score += SCORE_PER_ENEMY
                        self.kill_count += 1
                        self.check_score_progression()
                else:
                    enemy.remove_from_sprite_lists()
                    self.score += SCORE_PER_ENEMY
                    self.kill_count += 1
                    self.check_score_progression()
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

    def close_db(self):
        self.db.close()


def main():
    window = MyGame()
    window.setup()
    arcade.run()
    window.close_db()


if __name__ == "__main__":

    main()
