import random


def generate_random_id() -> int:
    return random.randint(1, 2_000_000_000)
