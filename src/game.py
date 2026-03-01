import arcade
import random
from settings import load_settings, save_settings

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "WarShip"

class MenuWindow(arcade.Window):

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.BLACK)

        self.state = "menu"   # menu / settings
        self.settings = load_settings()

        # Звёзды
        self.stars = [
            [random.randint(0, SCREEN_WIDTH),
             random.randint(0, SCREEN_HEIGHT),
             random.uniform(0.5, 2)]
            for _ in range(120)
        ]

        # Кнопки меню
        self.play_btn = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 60, 240, 60)
        self.settings_btn = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2, 240, 60)
        self.exit_btn = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 60, 240, 60)

        # Ползунок громкости
        self.slider_x = SCREEN_WIDTH/2
        self.slider_y = SCREEN_HEIGHT/2
        self.slider_width = 300
        self.dragging = False

    # ---------- DRAW ----------
    def on_draw(self):
        self.clear()
        self.draw_stars()

        if self.state == "menu":
            self.draw_menu()
        elif self.state == "settings":
            self.draw_settings()

    def draw_stars(self):
        for star in self.stars:
            arcade.draw_circle_filled(star[0], star[1], star[2], arcade.color.WHITE)

    def draw_button(self, rect, text, color=arcade.color.DARK_BLUE):
        cx, cy, w, h = rect
        arcade.draw_rect_filled(arcade.XYWH(cx, cy, w, h), color)
        arcade.draw_rect_outline(arcade.XYWH(cx, cy, w, h), arcade.color.WHITE, 2)
        arcade.draw_text(text, cx, cy, arcade.color.WHITE, 18,
                         anchor_x="center", anchor_y="center")

    def draw_menu(self):
        arcade.draw_text("WARSHIP",
                         SCREEN_WIDTH/2, SCREEN_HEIGHT - 120,
                         arcade.color.SKY_BLUE, 48,
                         anchor_x="center")

        self.draw_button(self.play_btn, "Играть")
        self.draw_button(self.settings_btn, "Настройки")
        self.draw_button(self.exit_btn, "Выход")

    def draw_settings(self):
        arcade.draw_text("Настройки",
                         SCREEN_WIDTH/2, SCREEN_HEIGHT - 120,
                         arcade.color.SKY_BLUE, 40,
                         anchor_x="center")

        arcade.draw_text("Громкость",
                         SCREEN_WIDTH/2, self.slider_y + 40,
                         arcade.color.WHITE, 18,
                         anchor_x="center")

        # линия
        left = self.slider_x - self.slider_width/2
        right = self.slider_x + self.slider_width/2
        arcade.draw_line(left, self.slider_y, right, self.slider_y,
                         arcade.color.GRAY, 4)

        # позиция ползунка
        knob_x = left + self.settings["volume"] * self.slider_width
        arcade.draw_circle_filled(knob_x, self.slider_y, 10, arcade.color.WHITE)

        # кнопка назад
        self.draw_button((SCREEN_WIDTH/2, 100, 200, 50), "Назад")

    # ---------- INPUT ----------
    def on_mouse_press(self, x, y, button, modifiers):
        if self.state == "menu":
            if self.hit(self.play_btn, x, y):
                self.start_game()

            elif self.hit(self.settings_btn, x, y):
                self.state = "settings"

            elif self.hit(self.exit_btn, x, y):
                arcade.close_window()

        elif self.state == "settings":
            left = self.slider_x - self.slider_width/2
            right = self.slider_x + self.slider_width/2

            # Проверка нажатия на ползунок
            if abs(y - self.slider_y) < 15 and left <= x <= right:
                self.dragging = True
                self.update_volume(x)

            # Назад
            if self.hit((SCREEN_WIDTH/2, 100, 200, 50), x, y):
                save_settings(self.settings)
                self.state = "menu"

    def on_mouse_release(self, x, y, button, modifiers):
        self.dragging = False

    def on_mouse_motion(self, x, y, dx, dy):
        if self.dragging:
            self.update_volume(x)

    def update_volume(self, x):
        left = self.slider_x - self.slider_width/2
        right = self.slider_x + self.slider_width/2
        value = (x - left) / self.slider_width
        self.settings["volume"] = max(0, min(1, value))

    def hit(self, rect, x, y):
        cx, cy, w, h = rect
        return (cx - w/2 <= x <= cx + w/2) and (cy - h/2 <= y <= cy + h/2)

    # ---------- GAME ----------
    def start_game(self):
        self.close()
        from game import main
        main()


def main():
    window = MenuWindow()
    arcade.run()


if __name__ == "__main__":
    main()
