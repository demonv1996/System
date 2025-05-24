import random
from collections import defaultdict

SNAKE_SEEDING = {
    8:  [0, 7, 4, 3, 2, 5, 6, 1],
    16: [0, 15, 8, 7, 4, 11, 12, 3, 2, 13, 10, 5, 6, 9, 14, 1],
    32: [0, 31, 16, 15, 8, 23, 24, 7, 4, 27, 20, 11, 12, 19, 28, 3, 2, 29, 18, 13, 10, 21, 22, 5, 6, 25, 14, 17, 26, 9, 30, 1],
    64: [0, 63, 32, 31, 16, 47, 48, 15, 8, 55, 40, 23, 24, 39, 56, 7, 4, 59, 36, 27, 20, 43, 52, 11, 12, 51, 44, 19, 28, 35, 60, 3,
         2, 61, 34, 21, 18, 45, 42, 5, 6, 41, 46, 17, 26, 37, 58, 9, 10, 57, 38, 25, 14, 53, 50, 13, 22, 49, 54, 1, 62, 33, 16, 29, 30]
}


def group_by_club(athletes):
    clubs = defaultdict(list)
    for athlete in athletes:
        clubs[athlete.get('club', '')].append(athlete)
    return list(clubs.values())


def round_robin_distribute(athletes):
    # Группируем по клубам и равномерно чередуем
    clubs = group_by_club(athletes)
    for club in clubs:
        random.shuffle(club)
    clubs.sort(key=len, reverse=True)
    result = []
    pointers = [0] * len(clubs)
    total = len(athletes)
    while len(result) < total:
        for idx, club in enumerate(clubs):
            if pointers[idx] < len(club):
                result.append(club[pointers[idx]])
                pointers[idx] += 1
    return result


def generate_bracket_random(athletes):

    n = len(athletes)
    if n <= 8:
        size = 8
    elif n <= 16:
        size = 16
    elif n <= 32:
        size = 32
    else:
        size = 64

    # 1. Просто перемешиваем
    random.shuffle(athletes)
    ordered = athletes

    indices = SNAKE_SEEDING[size][:n]
    slots = [None] * size
    for i, idx in enumerate(indices):
        slots[idx] = ordered[i]
    return slots


def generate_bracket(athletes):
    # print(athletes)
    n = len(athletes)
    # Подбираем размер сетки (8, 16, 32, 64)
    if n <= 8:
        size = 8
    elif n <= 16:
        size = 16
    elif n <= 32:
        size = 32
    else:
        size = 64

    # 1. Чередуем клубы
    ordered = round_robin_distribute(athletes)

    indices = SNAKE_SEEDING[size][:n]
    slots = [None] * size
    for i, idx in enumerate(indices):
        slots[idx] = ordered[i]
    return slots
