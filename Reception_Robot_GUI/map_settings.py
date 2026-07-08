"""Lưu map đang dùng (B1/B2) — đọc/ghi file JSON để đồng bộ với location (pgm, waypoint, log)."""
import json
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(_DIR, "selected_map.json")

DEFAULT_MAP_ID = "B2"
VALID_MAP_IDS = ("B1", "B2")


def get_map_id() -> str:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        mid = data.get("map_id", DEFAULT_MAP_ID)
        if mid not in VALID_MAP_IDS:
            return DEFAULT_MAP_ID
        return mid
    except (OSError, json.JSONDecodeError, TypeError):
        return DEFAULT_MAP_ID


def set_map_id(map_id: str) -> None:
    if map_id not in VALID_MAP_IDS:
        map_id = DEFAULT_MAP_ID
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"map_id": map_id}, f, indent=2, ensure_ascii=False)
