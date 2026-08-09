import json
from pathlib import Path


def load_schema():
    p = Path(__file__).with_name("transactions_realistic_schema.json")
    if p.exists():
        return json.loads(p.read_text())
    return {}

if __name__ == "__main__":
    print(load_schema())
