import random
import string


def generate_random_password(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def generate_username(full_name):
    base = full_name.lower().replace(" ", ".")
    # Add a random 3-digit number to ensure uniqueness
    suffix = random.randint(100, 999)
    return f"{base}.{suffix}"