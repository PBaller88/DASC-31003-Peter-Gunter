import random
import requests

REST_COUNTRIES_URL = "https://restcountries.com/v3.1/all?fields=name,region,subregion,borders,landlocked"

def fetch_country_data():
    response = requests.get(REST_COUNTRIES_URL)
    response.raise_for_status()
    return response.json()

def build_category_pools(countries):
    pools = {
        "Countries in South America": [],
        "Countries in Southeast Asia": [],
        "Countries in Western Europe": [],
        "Countries in the Caribbean": [],
        "Landlocked Countries": [],
        "Island / Non-Bordering Nations": [],
        "Countries Bordering 5+ Neighbors": [],
        "Countries with 'Land' in Name": [],
    }

    for country in countries:
        name = country.get("name", {}).get("common", "")
        subregion = country.get("subregion", "")
        borders = country.get("borders", [])
        landlocked = country.get("landlocked", False)

        if subregion == "South America": pools["Countries in South America"].append(name)
        if subregion == "South-Eastern Asia": pools["Countries in Southeast Asia"].append(name)
        if subregion == "Western Europe": pools["Countries in Western Europe"].append(name)
        if subregion == "Caribbean": pools["Countries in the Caribbean"].append(name)
        if landlocked: pools["Landlocked Countries"].append(name)
        if len(borders) == 0: pools["Island / Non-Bordering Nations"].append(name)
        if len(borders) >= 5: pools["Countries Bordering 5+ Neighbors"].append(name)
        if "land" in name.lower() and name != "Finland": pools["Countries with 'Land' in Name"].append(name)

    return {cat: items for cat, items in pools.items() if len(items) >= 4}

def generate_puzzle_round():
    raw_data = fetch_country_data()
    pools = build_category_pools(raw_data)

    if len(pools) < 4:
        raise ValueError("Not enough valid categories.")

    difficulties = ["yellow", "green", "blue", "purple"]
    selected_categories = random.sample(list(pools.keys()), 4)

    puzzle_groups = []
    used_countries = set()
    all_tiles = []

    for idx, cat_name in enumerate(selected_categories):
        available = [c for c in pools[cat_name] if c not in used_countries]
        if len(available) < 4:
            return generate_puzzle_round()

        chosen_4 = random.sample(available, 4)
        used_countries.update(chosen_4)

        puzzle_groups.append({
            "category": cat_name,
            "difficulty": difficulties[idx],
            "items": chosen_4
        })
        all_tiles.extend(chosen_4)

    random.shuffle(all_tiles)
    return {"tiles": all_tiles, "solution": puzzle_groups}
