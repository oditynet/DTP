import pygame
import sys
import random
import math
from datetime import datetime, timedelta

pygame.init()

# === НАСТРОЙКИ ===
WIDTH, HEIGHT = 1920, 1080
FPS = 30
MAX_CARS_IN_CITY = 1400
MAX_SPEED_KMH = 80
MAX_SPEED = 1.8

# Характеристики водителей
YOUNG_DRIVER_AGE = 25
OLD_DRIVER_AGE = 60
INATTENTIVE_DRIVER_PERCENT = 60
VERY_ATTENTIVE_DRIVER_PERCENT = 20
BAD_TIRES_PERCENT = 7
BAD_BRAKES_PERCENT = 3

# Интенсивность движения
TRAFFIC_INTENSITY = {
    0: 0.003, 1: 0.002, 2: 0.001, 3: 0.001, 4: 0.001, 5: 0.002,
    6: 0.005, 7: 0.015, 8: 0.03, 9: 0.02, 10: 0.015, 11: 0.015,
    12: 0.015, 13: 0.015, 14: 0.015, 15: 0.015, 16: 0.02, 17: 0.025,
    18: 0.03, 19: 0.02, 20: 0.01, 21: 0.005, 22: 0.003, 23: 0.002
}

ACCIDENT_DURATION = 1 * FPS

# === Инициализация экрана ===
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Реалистичный трафик: Городской симулятор с авариями")
clock = pygame.time.Clock()

# === Цвета ===
BACKGROUND = (25, 30, 35)
ROAD_COLOR = (85, 85, 85)
LANE_MARK = (220, 220, 220)
CENTER_LINE = (255, 255, 0)
RED = (255, 60, 60)
GREEN = (60, 255, 60)
YELLOW = (255, 255, 60)
ACCIDENT_COLOR = (255, 100, 100)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
INFO_BG = (40, 45, 50)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)

# === Параметры дорог ===
ROAD_WIDTH = 60
LANE_WIDTH = ROAD_WIDTH // 4
CAR_SIZE = 16
LIGHT_OFFSET = 35
CYCLE_TIME = 4 * FPS
FOLLOW_DISTANCE = CAR_SIZE * 1.5
STOP_LINE_DISTANCE = 20
TURN_PROBABILITY = 0.4

# Глобальное время
current_time = datetime(2024, 1, 1, 6, 0)
TIME_SPEED = 10
game_start_time = pygame.time.get_ticks()

# === Дороги ===
# ИСПРАВЛЕНО: Правильные координаты дорог с учетом ширины
h_roads = [200, 500,800, 950, 1400]  # Горизонтальные дороги (y-координаты)
v_roads = [250, 750,1050, 1650]       # Вертикальные дороги (x-координаты)

# ИСПРАВЛЕНО: Правильные смещения для полос
# Горизонтальные дороги: полосы 0-1 (верхние) - движение слева направо
H_LANE_OFFSETS = [15, 5, -5, -15]

# Вертикальные дороги: полосы 0-1 (левые) - движение сверху вниз
V_LANE_OFFSETS = [-15, -5, 5, 15]

# === Авария ===
class Accident:
    def __init__(self, x, y, car1, car2, reason):
        self.x = x
        self.y = y
        self.car1 = car1
        self.car2 = car2
        self.reason = reason
        self.timer = ACCIDENT_DURATION
        self.severity = random.choice(["легкая", "средняя", "тяжелая"])

    def update(self):
        self.timer -= 1
        return self.timer > 0

    def draw(self, surface):
        radius = 25 - (self.timer / ACCIDENT_DURATION * 15)
        if radius > 5:
            pygame.draw.circle(surface, ACCIDENT_COLOR, (int(self.x), int(self.y)), int(radius))
            pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), int(radius - 3))

# === Перекрёсток ===
class Intersection:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = random.randint(0, CYCLE_TIME)
        self.horizontal_green = random.choice([True, False])
        self.rect = pygame.Rect(x - ROAD_WIDTH//2, y - ROAD_WIDTH//2, ROAD_WIDTH, ROAD_WIDTH)
        
        # ИСПРАВЛЕНО: Правильные стоп-линии
        self.stop_lines = {
            'right': x - ROAD_WIDTH//2 - STOP_LINE_DISTANCE,
            'left': x + ROAD_WIDTH//2 + STOP_LINE_DISTANCE,
            'down': y - ROAD_WIDTH//2 - STOP_LINE_DISTANCE,
            'up': y + ROAD_WIDTH//2 + STOP_LINE_DISTANCE
        }

    def update(self):
        self.timer += 1
        if self.timer >= CYCLE_TIME:
            self.timer = 0
            self.horizontal_green = not self.horizontal_green

    def is_green_for(self, direction):
        if direction in ('left', 'right'):
            return self.horizontal_green
        else:  # up, down
            return not self.horizontal_green

    def toggle_lights(self):
        self.horizontal_green = not self.horizontal_green
        self.timer = 0

    def draw(self, surface):
        left_right_color = GREEN if self.horizontal_green else RED
        up_down_color = GREEN if not self.horizontal_green else RED

        light_size = 4

        # Светофоры для горизонтального движения
        pygame.draw.circle(surface, left_right_color, (self.x - ROAD_WIDTH//2 - 20, self.y - 25), light_size)
        pygame.draw.circle(surface, left_right_color, (self.x - ROAD_WIDTH//2 - 20, self.y + 25), light_size)
        pygame.draw.circle(surface, left_right_color, (self.x + ROAD_WIDTH//2 + 20, self.y - 25), light_size)
        pygame.draw.circle(surface, left_right_color, (self.x + ROAD_WIDTH//2 + 20, self.y + 25), light_size)

        # Светофоры для вертикального движения
        pygame.draw.circle(surface, up_down_color, (self.x - 25, self.y - ROAD_WIDTH//2 - 20), light_size)
        pygame.draw.circle(surface, up_down_color, (self.x + 25, self.y - ROAD_WIDTH//2 - 20), light_size)
        pygame.draw.circle(surface, up_down_color, (self.x - 25, self.y + ROAD_WIDTH//2 + 20), light_size)
        pygame.draw.circle(surface, up_down_color, (self.x + 25, self.y + ROAD_WIDTH//2 + 20), light_size)

        # Стоп-линии
        pygame.draw.line(surface, WHITE, (self.x - ROAD_WIDTH//2, self.y - STOP_LINE_DISTANCE),
                         (self.x + ROAD_WIDTH//2, self.y - STOP_LINE_DISTANCE), 2)
        pygame.draw.line(surface, WHITE, (self.x - ROAD_WIDTH//2, self.y + STOP_LINE_DISTANCE),
                         (self.x + ROAD_WIDTH//2, self.y + STOP_LINE_DISTANCE), 2)
        pygame.draw.line(surface, WHITE, (self.x - STOP_LINE_DISTANCE, self.y - ROAD_WIDTH//2),
                         (self.x - STOP_LINE_DISTANCE, self.y + ROAD_WIDTH//2), 2)
        pygame.draw.line(surface, WHITE, (self.x + STOP_LINE_DISTANCE, self.y - ROAD_WIDTH//2),
                         (self.x + STOP_LINE_DISTANCE, self.y + ROAD_WIDTH//2), 2)

# === Машина ===
class Car:
    def __init__(self, x, y, direction, lane, base_road):
        self.x = x
        self.y = y
        self.direction = direction
        self.lane = lane
        self.base_road = base_road
        self.speed = 0.0

        # Характеристики водителя
        self.driver_age = random.randint(18, 75)
        self.driver_experience = max(1, self.driver_age - 18)
        self.driver_mood = random.choice(["спокойный", "нервный", "расслабленный", "злой", "уставший"])
        self.driver_attention = self.calculate_attention()
        self.driver_aggression = random.uniform(0.1, 1.0)

        # Характеристики машины
        self.car_age = random.randint(0, 20)
        self.bad_tires = random.random() < BAD_TIRES_PERCENT / 100
        self.bad_brakes = random.random() < BAD_BRAKES_PERCENT / 100
        self.engine_power = random.uniform(0.8, 1.2)

        # Манера езды
        self.max_speed_multiplier = self.calculate_max_speed()
        self.max_speed = MAX_SPEED * self.max_speed_multiplier
        self.accel = 0.07 * self.engine_power
        self.decel = 0.15 * (0.7 if self.bad_brakes else 1.0)
        self.reaction_time = self.calculate_reaction_time()

        self.color = (
            random.randint(180, 255),
            random.randint(100, 220),
            random.randint(100, 220)
        )

        # Система поворотов
        self.turn_decision = None
        self.turning = False
        self.passed_stop_line = False

        # Для смены полосы
        self.changing_lane = False
        self.lane_change_progress = 0
        self.target_lane_temp = lane
        self.lane_change_cooldown = 0

        # Для аварий
        self.accident_timer = 0
        self.in_accident = False

        # Для выделения
        self.selected = False

    def calculate_attention(self):
        base_attention = 1.0

        if self.driver_age < YOUNG_DRIVER_AGE:
            base_attention *= 0.8
        elif self.driver_age > OLD_DRIVER_AGE:
            base_attention *= 0.9

        mood_effects = {
            "нервный": 0.8,
            "злой": 0.7,
            "уставший": 0.6,
            "расслабленный": 1.0,
            "спокойный": 1.1
        }
        base_attention *= mood_effects.get(self.driver_mood, 1.0)

        base_attention *= min(1.2, 1.0 + self.driver_experience * 0.01)

        rand_val = random.random() * 100
        if rand_val < INATTENTIVE_DRIVER_PERCENT:
            base_attention *= 0.7
        elif rand_val < INATTENTIVE_DRIVER_PERCENT + VERY_ATTENTIVE_DRIVER_PERCENT:
            base_attention *= 1.2

        return base_attention

    def calculate_max_speed(self):
        multiplier = 1.0
        if self.driver_age < YOUNG_DRIVER_AGE:
            multiplier *= 1.1
        if self.driver_mood == "злой":
            multiplier *= 1.2
        multiplier *= (0.9 + self.driver_aggression * 0.2)
        return multiplier

    def calculate_reaction_time(self):
        reaction = 1.0
        if self.driver_age > OLD_DRIVER_AGE:
            reaction *= 1.2
        if self.driver_experience < 5:
            reaction *= 1.1

        if self.driver_mood in ["уставший", "нервный"]:
            reaction *= 1.2

        reaction /= self.driver_attention

        return max(0.7, min(1.5, reaction))

    def get_position(self):
        # ИСПРАВЛЕНО: Правильное позиционирование на дороге
        if self.direction == 'right':
            offset = H_LANE_OFFSETS[self.lane]
            return self.x, self.base_road + offset
        elif self.direction == 'left':
            offset = H_LANE_OFFSETS[self.lane]
            return self.x, self.base_road + offset
        elif self.direction == 'down':
            offset = V_LANE_OFFSETS[self.lane]
            return self.base_road + offset, self.y
        elif self.direction == 'up':
            offset = V_LANE_OFFSETS[self.lane]
            return self.base_road + offset, self.y

    def check_accident(self, other_car, distance):
        if self.in_accident or other_car.in_accident:
            return False

        accident_prob = 0.0

        if distance < FOLLOW_DISTANCE * 0.3:
            accident_prob = 0.01

        risk_multiplier = 1.0

        risk_multiplier *= (1.5 - min(self.driver_attention, other_car.driver_attention))

        if self.bad_brakes or other_car.bad_brakes:
            risk_multiplier *= 1.2
        if self.bad_tires or other_car.bad_tires:
            risk_multiplier *= 1.1

        risk_multiplier *= (0.5 + (self.speed + other_car.speed) / (MAX_SPEED * 2))

        if self.driver_experience < 3 or other_car.driver_experience < 3:
            risk_multiplier *= 1.05

        if "злой" in [self.driver_mood, other_car.driver_mood]:
            risk_multiplier *= 1.1

        final_probability = accident_prob * risk_multiplier * 0.02

        return random.random() < final_probability

    def update(self, intersections, all_cars, accidents):
        if self.in_accident:
            self.accident_timer -= 1
            if self.accident_timer <= 0:
                self.in_accident = False
                self.speed = self.max_speed * 0.5
            return True

        if self.turning:
            return self.update_turn()

        if self.changing_lane:
            self.lane_change_progress += 0.1
            if self.lane_change_progress >= 1:
                self.lane = self.target_lane_temp
                self.changing_lane = False
                self.lane_change_progress = 0
                self.lane_change_cooldown = 30
            else:
                # Плавное изменение позиции при смене полосы
                if self.direction in ['left', 'right']:
                    start_offset = H_LANE_OFFSETS[self.lane]
                    end_offset = H_LANE_OFFSETS[self.target_lane_temp]
                    current_offset = start_offset + (end_offset - start_offset) * self.lane_change_progress
                    self.y = self.base_road + current_offset
                else:
                    start_offset = V_LANE_OFFSETS[self.lane]
                    end_offset = V_LANE_OFFSETS[self.target_lane_temp]
                    current_offset = start_offset + (end_offset - start_offset) * self.lane_change_progress
                    self.x = self.base_road + current_offset
        else:
            self.x, self.y = self.get_position()

        if self.lane_change_cooldown > 0:
            self.lane_change_cooldown -= 1

        # Удаление машин за пределами экрана
        if (self.x < -100 or self.x > WIDTH + 100 or
            self.y < -100 or self.y > HEIGHT + 100):
            return False

        # Поиск ближайшего перекрёстка
        next_int = None
        dist_to_int = float('inf')
        for inter in intersections:
            if self.direction == 'right' and abs(inter.y - self.base_road) < 10 and inter.x > self.x:
                d = inter.x - self.x - STOP_LINE_DISTANCE
                if d < dist_to_int and d > 0:
                    dist_to_int = d
                    next_int = inter
            elif self.direction == 'left' and abs(inter.y - self.base_road) < 10 and inter.x < self.x:
                d = self.x - inter.x - STOP_LINE_DISTANCE
                if d < dist_to_int and d > 0:
                    dist_to_int = d
                    next_int = inter
            elif self.direction == 'down' and abs(inter.x - self.base_road) < 10 and inter.y > self.y:
                d = inter.y - self.y - STOP_LINE_DISTANCE
                if d < dist_to_int and d > 0:
                    dist_to_int = d
                    next_int = inter
            elif self.direction == 'up' and abs(inter.x - self.base_road) < 10 and inter.y < self.y:
                d = self.y - inter.y - STOP_LINE_DISTANCE
                if d < dist_to_int and d > 0:
                    dist_to_int = d
                    next_int = inter

        # Проверка проезда стоп-линии
        if next_int and not self.passed_stop_line:
            if self.direction == 'right' and self.x > next_int.x - STOP_LINE_DISTANCE:
                self.passed_stop_line = True
            elif self.direction == 'left' and self.x < next_int.x + STOP_LINE_DISTANCE:
                self.passed_stop_line = True
            elif self.direction == 'down' and self.y > next_int.y - STOP_LINE_DISTANCE:
                self.passed_stop_line = True
            elif self.direction == 'up' and self.y < next_int.y + STOP_LINE_DISTANCE:
                self.passed_stop_line = True

        # Поиск ближайшей машины впереди
        lead_dist = float('inf')
        lead_car = None
        for other in all_cars:
            if other is self or other.turning or other.in_accident:
                continue
            if other.direction != self.direction or other.lane != self.lane:
                continue

            if self.direction == 'right' and other.x > self.x:
                d = other.x - self.x
                if d < lead_dist:
                    lead_dist = d
                    lead_car = other
            elif self.direction == 'left' and other.x < self.x:
                d = self.x - other.x
                if d < lead_dist:
                    lead_dist = d
                    lead_car = other
            elif self.direction == 'down' and other.y > self.y:
                d = other.y - self.y
                if d < lead_dist:
                    lead_dist = d
                    lead_car = other
            elif self.direction == 'up' and other.y < self.y:
                d = self.y - other.y
                if d < lead_dist:
                    lead_dist = d
                    lead_car = other

        # Проверка на аварию
        if lead_car and lead_dist < CAR_SIZE:
            if self.check_accident(lead_car, lead_dist):
                self.cause_accident(lead_car, "Столкновение", accidents)
                return True

        # Определение состояния светофора
        light_ok = True
        if next_int:
            light_ok = next_int.is_green_for(self.direction)

        # Логика движения
        should_brake = False
        
        # 1. Торможение из-за машины впереди
        safe_follow_distance = FOLLOW_DISTANCE * (1.0 + (1 - self.driver_attention) * 0.5)
        if lead_car and lead_dist < safe_follow_distance:
            should_brake = True
            # Попытка смены полосы
            if (not self.changing_lane and self.lane_change_cooldown == 0 and
                random.random() < 0.02 * self.driver_aggression):
                self.try_change_lane(all_cars)
        
        # 2. Торможение на красный свет
        if next_int and dist_to_int < STOP_LINE_DISTANCE * 3:
            if not light_ok and not self.passed_stop_line:
                should_brake = True
                if dist_to_int < 5:
                    self.speed = 0
        
        # 3. Торможение из-за пробки
        if lead_car and lead_car.speed == 0 and lead_dist < safe_follow_distance * 1.2:
            should_brake = True

        # Ускорение/торможение
        if should_brake:
            self.speed = max(0, self.speed - self.decel * self.reaction_time)
        else:
            self.speed = min(self.max_speed, self.speed + self.accel)

        # Движение
        if self.speed > 0:
            if self.direction == 'right':
                self.x += self.speed
            elif self.direction == 'left':
                self.x -= self.speed
            elif self.direction == 'down':
                self.y += self.speed
            elif self.direction == 'up':
                self.y -= self.speed

        # Корректировка позиции
        if not self.turning and not self.changing_lane:
            self.x, self.y = self.get_position()

        # Решение о повороте
        if (next_int and dist_to_int < 40 and
            self.speed > 0.1 and light_ok and
            self.turn_decision is None and not self.passed_stop_line):
            self.decide_turn()

        # Начало поворота
        if (self.turn_decision and not self.turning and
            next_int and dist_to_int < 20 and light_ok and self.speed > 0.1):
            self.start_turn(next_int)

        return True

    def try_change_lane(self, all_cars):
        if self.changing_lane or self.lane_change_cooldown > 0:
            return

        # Определение возможных полос для смены
        possible_lanes = []
        if self.direction in ['right', 'left']:
            if self.lane == 0: possible_lanes = [1]
            elif self.lane == 1: possible_lanes = [0]
            elif self.lane == 2: possible_lanes = [3]
            elif self.lane == 3: possible_lanes = [2]
        else:
            if self.lane == 0: possible_lanes = [1]
            elif self.lane == 1: possible_lanes = [0]
            elif self.lane == 2: possible_lanes = [3]
            elif self.lane == 3: possible_lanes = [2]

        if not possible_lanes:
            return

        # Проверка доступности полосы
        for new_lane in possible_lanes:
            lane_clear = True
            for other in all_cars:
                if other is self or other.in_accident or other.turning:
                    continue
                if other.direction != self.direction:
                    continue
                if other.lane != new_lane:
                    continue

                # Проверка дистанции
                if self.direction in ['left', 'right']:
                    if abs(other.x - self.x) < FOLLOW_DISTANCE * 2:
                        lane_clear = False
                        break
                else:
                    if abs(other.y - self.y) < FOLLOW_DISTANCE * 2:
                        lane_clear = False
                        break

            if lane_clear:
                self.target_lane_temp = new_lane
                self.changing_lane = True
                self.lane_change_progress = 0
                break

    def cause_accident(self, other_car, reason, accidents):
        self.in_accident = True
        other_car.in_accident = True
        self.accident_timer = ACCIDENT_DURATION
        other_car.accident_timer = ACCIDENT_DURATION
        self.speed = 0
        other_car.speed = 0

        accident_x = (self.x + other_car.x) / 2
        accident_y = (self.y + other_car.y) / 2
        accidents.append(Accident(accident_x, accident_y, self, other_car, reason))

    def decide_turn(self):
        options = ['straight']

        # Логика доступных поворотов
        if self.direction == 'right':
            if self.lane == 0:  # Левая полоса
                options = ['straight', 'left', 'uturn']
            elif self.lane == 1:  # Правая полоса
                options = ['straight', 'right']

        elif self.direction == 'left':
            if self.lane == 3:  # Правая полоса
                options = ['straight', 'left', 'uturn']
            elif self.lane == 2:  # Левая полоса
                options = ['straight', 'right']

        elif self.direction == 'down':
            if self.lane == 0:  # Левая полоса
                options = ['straight', 'left', 'uturn']
            elif self.lane == 1:  # Правая полоса
                options = ['straight', 'right']

        elif self.direction == 'up':
            if self.lane == 3:  # Правая полоса
                options = ['straight', 'left', 'uturn']
            elif self.lane == 2:  # Левая полоса
                options = ['straight', 'right']

        if random.random() < TURN_PROBABILITY:
            self.turn_decision = random.choice(options)
        else:
            self.turn_decision = 'straight'

    def start_turn(self, intersection):
        if self.turn_decision == 'straight':
            self.turn_decision = None
            return

        self.turning = True
        self.passed_stop_line = False

        # ИСПРАВЛЕНО: Упрощенный поворот - резкая смена направления
        if self.turn_decision == 'left':
            if self.direction == 'right':
                self.direction = 'up'
                self.lane = 2  # Крайняя левая полоса
            elif self.direction == 'left':
                self.direction = 'down'
                self.lane = 0  # Крайняя левая полоса
            elif self.direction == 'down':
                self.direction = 'right'
                self.lane = 0  # Крайняя левая полоса
            elif self.direction == 'up':
                self.direction = 'left'
                self.lane = 2  # Крайняя левая полоса

        elif self.turn_decision == 'right':
            if self.direction == 'right':
                self.direction = 'down'
                self.lane = 1  # Крайняя правая полоса
            elif self.direction == 'left':
                self.direction = 'up'
                self.lane = 3  # Крайняя правая полоса
            elif self.direction == 'down':
                self.direction = 'left'
                self.lane = 3  # Крайняя правая полоса
            elif self.direction == 'up':
                self.direction = 'right'
                self.lane = 1  # Крайняя правая полоса

        elif self.turn_decision == 'uturn':
            # ИСПРАВЛЕНО: При развороте машина перестраивается на соседнюю полосу встречного направления
            if self.direction == 'right':
                self.direction = 'left'
                # Была полоса 0 или 1 (движение направо), после разворота - полоса 2 или 3 (движение налево)
                self.lane = 2 if self.lane == 0 else 3
            elif self.direction == 'left':
                self.direction = 'right'
                # Была полоса 2 или 3 (движение налево), после разворота - полоса 0 или 1 (движение направо)
                self.lane = 0 if self.lane == 2 else 1
            elif self.direction == 'down':
                self.direction = 'up'
                # Была полоса 0 или 1 (движение вниз), после разворота - полоса 2 или 3 (движение вверх)
                self.lane = 2 if self.lane == 0 else 3
            elif self.direction == 'up':
                self.direction = 'down'
                # Была полоса 2 или 3 (движение вверх), после разворота - полоса 0 или 1 (движение вниз)
                self.lane = 0 if self.lane == 2 else 1

        # Обновление базовой дороги
        if self.direction in ['left', 'right']:
            self.base_road = intersection.y
        else:
            self.base_road = intersection.x

        self.turn_decision = None
        self.turning = False

    def update_turn(self):
        # ИСПРАВЛЕНО: Упрощенная логика поворота
        return True

    def draw(self, surface):
        if self.in_accident:
            if pygame.time.get_ticks() % 500 < 250:
                color = RED
            else:
                color = self.color
        else:
            color = self.color

        if self.direction in ('left', 'right'):
            pygame.draw.rect(surface, color,
                             (self.x - CAR_SIZE//2, self.y - CAR_SIZE//4, CAR_SIZE, CAR_SIZE//2))
        else:
            pygame.draw.rect(surface, color,
                             (self.x - CAR_SIZE//4, self.y - CAR_SIZE//2, CAR_SIZE//2, CAR_SIZE))

        if self.selected:
            if self.direction in ('left', 'right'):
                pygame.draw.rect(surface, YELLOW,
                                (self.x - CAR_SIZE//2 - 3, self.y - CAR_SIZE//4 - 3,
                                 CAR_SIZE + 6, CAR_SIZE//2 + 6), 2)
            else:
                pygame.draw.rect(surface, YELLOW,
                                (self.x - CAR_SIZE//4 - 3, self.y - CAR_SIZE//2 - 3,
                                 CAR_SIZE//2 + 6, CAR_SIZE + 6), 2)

# === Кнопка паузы ===
class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.hovered = False

    def draw(self, surface):
        color = BUTTON_HOVER if self.hovered else BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 2)

        font = pygame.font.SysFont(None, 28)
        text_surface = font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

# === Спавн машин ===
def spawn_cars(cars):
    global current_time

    hour = current_time.hour
    spawn_probability = TRAFFIC_INTENSITY.get(hour, 0.01)

    if len(cars) >= MAX_CARS_IN_CITY * 0.8:
        spawn_probability *= 0.5

    # ИСПРАВЛЕНО: Правильный спавн машин только на правых полосах
    for y in h_roads:
        if random.random() < spawn_probability:
            lane = random.choice([0, 1])  # Только правые полосы для движения направо
            cars.append(Car(-50, y, 'right', lane, y))
        if random.random() < spawn_probability:
            lane = random.choice([2, 3])  # Только левые полосы для движения налево
            cars.append(Car(WIDTH + 50, y, 'left', lane, y))

    for x in v_roads:
        if random.random() < spawn_probability:
            lane = random.choice([0, 1])  # Только левые полосы для движения вниз
            cars.append(Car(x, -50, 'down', lane, x))
        if random.random() < spawn_probability:
            lane = random.choice([2, 3])  # Только правые полосы для движения вверх
            cars.append(Car(x, HEIGHT + 50, 'up', lane, x))

# === Инициализация ===
intersections = [Intersection(x, y) for x in v_roads for y in h_roads]
cars = []
accidents = []
font = pygame.font.SysFont(None, 24)
small_font = pygame.font.SysFont(None, 20)
large_font = pygame.font.SysFont(None, 36)

pause_button = Button(10, HEIGHT - 50, 100, 40, "Пауза")
paused = False
selected_car = None

# === Главный цикл ===
running = True
while running:
    dt = clock.tick(FPS)

    mouse_pos = pygame.mouse.get_pos()
    pause_button.check_hover(mouse_pos)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for inter in intersections:
                if inter.rect.collidepoint(mouse_pos):
                    inter.toggle_lights()

            selected_car = None
            car_clicked = False
            for car in cars:
                if car.direction in ('left', 'right'):
                    car_rect = pygame.Rect(car.x - CAR_SIZE//2, car.y - CAR_SIZE//4, CAR_SIZE, CAR_SIZE//2)
                else:
                    car_rect = pygame.Rect(car.x - CAR_SIZE//4, car.y - CAR_SIZE//2, CAR_SIZE//2, CAR_SIZE)

                if car_rect.collidepoint(mouse_pos):
                    selected_car = car
                    car.selected = True
                    car_clicked = True
                else:
                    car.selected = False

            if not car_clicked and not any(inter.rect.collidepoint(mouse_pos) for inter in intersections):
                selected_car = None
                for car in cars:
                    car.selected = False

            if pause_button.is_clicked(mouse_pos, event):
                paused = not paused

    if not paused:
        current_time += timedelta(minutes=TIME_SPEED)
        spawn_cars(cars)

        for light in intersections:
            light.update()

        cars = [car for car in cars if car.update(intersections, cars, accidents)]
        accidents = [accident for accident in accidents if accident.update()]

    # === Отрисовка ===
    screen.fill(BACKGROUND)

    # Горизонтальные дороги
    for y in h_roads:
        pygame.draw.rect(screen, ROAD_COLOR, (0, y - ROAD_WIDTH//2, WIDTH, ROAD_WIDTH))
        pygame.draw.line(screen, CENTER_LINE, (0, y), (WIDTH, y), 2)
        for x in range(0, WIDTH, 40):
            pygame.draw.rect(screen, LANE_MARK, (x, y - 10, 20, 2))
            pygame.draw.rect(screen, LANE_MARK, (x, y + 10, 20, 2))

    # Вертикальные дороги
    for x in v_roads:
        pygame.draw.rect(screen, ROAD_COLOR, (x - ROAD_WIDTH//2, 0, ROAD_WIDTH, HEIGHT))
        pygame.draw.line(screen, CENTER_LINE, (x, 0), (x, HEIGHT), 2)
        for y in range(0, HEIGHT, 40):
            pygame.draw.rect(screen, LANE_MARK, (x - 10, y, 2, 20))
            pygame.draw.rect(screen, LANE_MARK, (x + 10, y, 2, 20))

    for light in intersections:
        light.draw(screen)

    for car in cars:
        car.draw(screen)

    for accident in accidents:
        accident.draw(screen)

    # Время игры сверху по центру
    game_time = (pygame.time.get_ticks() - game_start_time) // 1000
    minutes = game_time // 60
    seconds = game_time % 60
    time_text = large_font.render(f"Время игры: {minutes:02d}:{seconds:02d}", True, WHITE)
    time_rect = time_text.get_rect(center=(WIDTH//2, 30))
    screen.blit(time_text, time_rect)

    if selected_car:
        info_lines = [
            f"Возраст: {selected_car.driver_age}",
            f"Опыт: {selected_car.driver_experience}л",
            f"Настроение: {selected_car.driver_mood}",
            f"Машина: {selected_car.car_age}л",
            f"Шины: {'ПЛОХИЕ' if selected_car.bad_tires else 'норм'}",
            f"Тормоза: {'ПЛОХИЕ' if selected_car.bad_brakes else 'норм'}"
        ]

        info_x = selected_car.x + 20
        info_y = selected_car.y - 80

        max_width = max(small_font.size(line)[0] for line in info_lines) + 10
        total_height = len(info_lines) * 18 + 10
        pygame.draw.rect(screen, INFO_BG, (info_x, info_y, max_width, total_height))
        pygame.draw.rect(screen, YELLOW, (info_x, info_y, max_width, total_height), 1)

        for i, line in enumerate(info_lines):
            text_surface = small_font.render(line, True, WHITE)
            screen.blit(text_surface, (info_x + 5, info_y + 5 + i * 18))

    info_panel_width = 350
    info_panel_x = WIDTH - info_panel_width - 10

    pygame.draw.rect(screen, INFO_BG, (info_panel_x, 10, info_panel_width, 180))
    pygame.draw.rect(screen, WHITE, (info_panel_x, 10, info_panel_width, 180), 2)

    y_offset = 20

    time_text = font.render(f"Время: {current_time.strftime('%H:%M')}", True, WHITE)
    screen.blit(time_text, (info_panel_x + 10, y_offset))
    y_offset += 30

    status_text = "ПАУЗА" if paused else "ИГРА"
    status_color = RED if paused else GREEN
    status_surface = font.render(f"Статус: {status_text}", True, status_color)
    screen.blit(status_surface, (info_panel_x + 10, y_offset))
    y_offset += 30

    cars_text = font.render(f"Машин: {len(cars)}/{MAX_CARS_IN_CITY}", True, WHITE)
    screen.blit(cars_text, (info_panel_x + 10, y_offset))
    y_offset += 25

    accidents_text = font.render(f"Аварии: {len(accidents)}", True, WHITE)
    screen.blit(accidents_text, (info_panel_x + 10, y_offset))

    pause_button.draw(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()
