
import os
import sys
import random
import arcade

# ======================================================
# Helper function for PyInstaller / normal execution
# ======================================================
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller exe"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# ======================================================
# Constants (adjust if needed)
# ======================================================
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Race Game"

ASSETS = "assets"
SOUNDS = "sounds"

PLAYER_SCALE = 0.5
PLAYER_Y = 100
PLAYER_SPEED = 8

BASE_ENEMY_SPEED = 5
SPAWN_TIME = 1.2  # seconds between spawns

LANES = [150, 250, 350, 450]  # example lane positions - adjust to your needs

class GameState:
    MENU = "menu"
    PLAYING = "playing"
    GAME_OVER = "game_over"


# ======================================================
# ------------------- ROAD MANAGER ---------------------
# ======================================================
class RoadManager:
    def __init__(self, speed):
        self.road_list = arcade.SpriteList()
        self.speed = speed
        for i in range(2):
            road = arcade.Sprite(resource_path(os.path.join(ASSETS, "road.png")))
            road.center_x = SCREEN_WIDTH // 2
            road.center_y = i * SCREEN_HEIGHT + SCREEN_HEIGHT // 2
            road.angle = 90
            self.road_list.append(road)

    def update(self):
        for road in self.road_list:
            road.center_y -= self.speed
            if road.center_y < -SCREEN_HEIGHT // 2:
                road.center_y += SCREEN_HEIGHT * 2

    def draw(self):
        self.road_list.draw()


# ======================================================
# ------------------- ENEMY MANAGER --------------------
# ======================================================
class EnemyManager:
    def __init__(self):
        self.enemy_list = arcade.SpriteList()
        self.spawn_timer = 0

    def spawn_enemy(self, speed):
        enemy = arcade.Sprite(
            resource_path(os.path.join(ASSETS, "car_enemies.png")),
            scale=0.5,
            angle=90
        )
        enemy.center_x = random.choice(LANES)
        enemy.center_y = SCREEN_HEIGHT + 150
        enemy.change_y = -speed
        self.enemy_list.append(enemy)

    def update(self, delta_time, speed):
        self.spawn_timer += delta_time
        passed = 0

        if self.spawn_timer >= SPAWN_TIME:
            self.spawn_enemy(speed)
            self.spawn_timer = 0

        for enemy in self.enemy_list[:]:  # safe iteration
            enemy.center_y += enemy.change_y
            if enemy.top < 0:
                enemy.remove_from_sprite_lists()
                passed += 1

        return passed

    def draw(self):
        self.enemy_list.draw()


# ======================================================
# --------------------- MAIN GAME ----------------------
# ======================================================
class RaceGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.BLACK)

        self.state = GameState.MENU
        self.road_manager = None
        self.enemy_manager = EnemyManager()
        self.player = None
        self.player_list = arcade.SpriteList()
        self.score = 0
        self.enemy_speed = BASE_ENEMY_SPEED

        # ------------------ SOUNDS ------------------
        self.engine_sound = arcade.Sound(resource_path(os.path.join(SOUNDS, "engine_loop.wav")))
        self.pass_sound   = arcade.Sound(resource_path(os.path.join(SOUNDS, "pass.wav")))
        self.crash_sound  = arcade.Sound(resource_path(os.path.join(SOUNDS, "crash.wav")))
        self.achievement_sound = arcade.Sound(resource_path(os.path.join(SOUNDS, "achievement.wav")))
        self.menu_sound   = arcade.Sound(resource_path(os.path.join(SOUNDS, "menu_click.wav")))

        self.engine_player = None  # looping engine handle

    def setup(self):
        self.player_list.clear()
        self.enemy_manager.enemy_list.clear()
        self.score = 0
        self.enemy_speed = BASE_ENEMY_SPEED

        self.road_manager = RoadManager(self.enemy_speed)

        self.player = arcade.Sprite(
            resource_path(os.path.join(ASSETS, "car_allies.png")),
            scale=PLAYER_SCALE,
            angle=-90
        )
        self.player.center_x = SCREEN_WIDTH // 2
        self.player.center_y = PLAYER_Y
        self.player.change_x = 0
        self.player_list.append(self.player)

        self.state = GameState.PLAYING

        # Start engine loop
        if self.engine_player:
            self.engine_player.delete()
        self.engine_player = self.engine_sound.play(volume=0.15, loop=True)

    def on_update(self, delta_time):
        if self.state != GameState.PLAYING:
            return

        self.road_manager.update()
        self.player.center_x += self.player.change_x
        self.player.center_x = max(120, min(SCREEN_WIDTH - 120, self.player.center_x))

        passed = self.enemy_manager.update(delta_time, self.enemy_speed)
        if passed > 0:
            self.score += passed
            self.pass_sound.play(volume=0.3)

        if arcade.check_for_collision_with_list(
            self.player, self.enemy_manager.enemy_list
        ):
            self.crash_sound.play(volume=0.7)
            if self.engine_player:
                self.engine_player.pause()
            self.state = GameState.GAME_OVER

    def on_draw(self):
        self.clear()

        # ---------- MENU ----------
        if self.state == GameState.MENU:
            arcade.draw_text(
                "RACE GAME",
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2 + 60,
                arcade.color.WHITE,
                48,
                anchor_x="center"
            )
            arcade.draw_text(
                "Press ENTER to Start",
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2 - 20,
                arcade.color.WHITE,
                20,
                anchor_x="center"
            )
            return

        # ---------- GAME PLAY / GAME OVER ----------
        self.road_manager.draw()
        self.player_list.draw()
        self.enemy_manager.draw()

        arcade.draw_text(
            f"Cars Passed: {self.score}",
            20,
            SCREEN_HEIGHT - 40,
            arcade.color.WHITE,
            20
        )

        if self.state == GameState.GAME_OVER:
            arcade.draw_text(
                "GAME OVER",
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                arcade.color.RED,
                48,
                anchor_x="center"
            )
            arcade.draw_text(
                "Press R to Restart",
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2 - 60,
                arcade.color.WHITE,
                20,
                anchor_x="center"
            )

    def on_key_press(self, key, modifiers):
        if self.state == GameState.MENU and key == arcade.key.ENTER:
            self.menu_sound.play(volume=0.4)
            self.setup()

        if self.state == GameState.PLAYING:
            if key in (arcade.key.LEFT, arcade.key.A):
                self.player.change_x = -PLAYER_SPEED
            elif key in (arcade.key.RIGHT, arcade.key.D):
                self.player.change_x = PLAYER_SPEED

        elif self.state == GameState.GAME_OVER and key == arcade.key.R:
            self.menu_sound.play(volume=0.4)
            self.setup()

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.RIGHT, arcade.key.A, arcade.key.D):
            self.player.change_x = 0


# ======================================================
# -------------------- ENTRY POINT ---------------------
# ======================================================
def main():
    game = RaceGame()
    arcade.run()


if __name__ == "__main__":
    main()