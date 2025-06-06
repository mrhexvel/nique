import random


def generate_random_id() -> int:
    return random.randint(0, 2**31 - 1)
