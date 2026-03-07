# 1. Настройки экрана и окна
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "KosmicheskieZashitniki"

# 2. Физика и движение
ENEMY_BASE_SPEED = -1
BULLET_BASE_SPEED = 5
ENEMY_SHOOT_BASE_INTERVAL = 90
SHOT_COOLDOWN = 0.1

# 3. Здоровье и характеристики сущностей
TOUGH_ENEMY_HEALTH = 3
WALL_DESTR_HEALTH = 3
PLAYER_LIVES = 1

# 4. Система очков и прогрессия сложности
SCORE_PER_ENEMY = 10
SCORE_PER_WALL = 20
SCORE_PER_BOSS = 500
SPEED_INCREASE_PER_100_SCORE = -0.05
BULLET_SPEED_INCREASE_PER_100_SCORE = 0.01
ENEMY_SHOOT_INCREASE_PER_100_SCORE = 2

# Условия появления усиленного врага
TOUGH_ENEMY_SPAWN_SCORE = 1000
TOUGH_ENEMY_SPAWN_CHANCE = 0.2

# 6. Стоимость сущностей (для бюджета волны)
COST_NORMAL_ENEMY = 1
COST_TOUGH_ENEMY = 10
COST_WALL_INDESTR = 3
COST_WALL_DESTR = 5
COST_WALL_PASS = 4
COST_BOSS = 100

# 5. Система волн и бюджет спавна
BASE_WAVE_BUDGET = 15
BUDGET_INCREASE_PER_WAVE = 5
MAX_WALL_PERCENT = 0.2
WAVE_COOLDOWN_FRAMES = 120
BOSS_WAVE_INTERVAL = 3 # каждые 3 волны

# 7. Графические ресурсы (Текстуры)
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
TEX_BOSS = "images/boss.png"
TEX_BOSS_HIT = "images/boss_hit.png"

# 8. Данные и сохранение
DB_NAME = "data/game_data.db"

# 9. Настройки босса
BOSS_HEALTH = 50
BOSS_SPEED = 2
BOSS_SHOOT_INTERVAL = 60
BOSS_MOVE_INTERVAL = 120
BOSS_ATTACK_PATTERNS = 3
BOSS_ROOM_HEIGHT = 800

# 10. Система частиц
PARTICLE_COUNT = 50
PARTICLE_LIFETIME = 1.0
PARTICLE_SPEED = 3
PARTICLE_SIZE = 4
EXPLOSION_PARTICLE_COUNT = 30
BOSS_EXPLOSION_PARTICLE_COUNT = 100

# 11. Физика
GRAVITY = 0.5
FRICTION = 0.98
BOUNCE_FACTOR = 0.7
