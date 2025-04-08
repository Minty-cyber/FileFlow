import random 
import string 
from fastapi.testclient import TestClient



def random_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))

def random_email() -> str:
    return f"{random_string()}@{random_string()}.com"

