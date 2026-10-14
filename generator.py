# generator.py
import random
from data import GEOGRAPHY_DATA

def generate_puzzle_round():
    categories = list(GEOGRAPHY_DATA.keys())
    difficulties = ["yellow", "green", "blue", "purple"]

    for _ in range(50):
        selected_cats = random.sample(categories, 4)
        puzzle_groups = []
        used_countries = set()
        all_tiles = []
        failed = False

        for idx, cat_name in enumerate(selected_cats):
            available = [c for c in GEOGRAPHY_DATA[cat_name] if c not in used_countries]
            
            if len(available) < 4:
                failed = True
                break

            chosen_4 = random.sample(available, 4)
            used_countries.update(chosen_4)

            puzzle_groups.append({
                "category": cat_name,
                "difficulty": difficulties[idx],
                "items": chosen_4
            })
            all_tiles.extend(chosen_4)

        if not failed and len(puzzle_groups) == 4:
            random.shuffle(all_tiles)
            return {
                "tiles": all_tiles,
                "solution": puzzle_groups
            }

    fallback_cats = categories[:4]
    puzzle_groups = []
    all_tiles = []
    
    for idx, cat_name in enumerate(fallback_cats):
        chosen_4 = GEOGRAPHY_DATA[cat_name][:4]
        puzzle_groups.append({
            "category": cat_name,
            "difficulty": difficulties[idx],
            "items": chosen_4
        })
        all_tiles.extend(chosen_4)

    random.shuffle(all_tiles)
    return {
        "tiles": all_tiles,
        "solution": puzzle_groups
    }