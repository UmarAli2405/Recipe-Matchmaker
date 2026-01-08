from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pathlib import Path
import json
import os
import shutil
from recipe_matcher import get_recipe_matches, load_inventory, INVENTORY_PATH

app = Flask(__name__, static_folder="static")

CORS(app)

INVENTORY_FILE = "inventory.json"
RECIPES_FILE = "recipes.json"
FAVORITES_FILE = "favorites.json"

def normalize_name(name: str) -> str:
    return (name or "").strip().lower()

def api_json(data: dict, status: int=200):
    return jsonify(data), status

def load_data(file):
    if not os.path.exists(file):
        return []
    with open(file, "r") as f:
        return json.load(f)


def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)


@app.route("/")
def home():
    return send_from_directory(app.static_folder, "index.html")


# ---- Inventory ---- #

def load_inventory(path: Path) -> dict:
    if not path.exists():
        default = {
            "salt": {"quantity": 1, "unit": "tsp"},
            "pepper": {"quantity": 1, "unit": "tsp"}
        }
        path.write_text(json.dumps(default, indent=2), encoding="utf-8")
        return default
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        for item in raw.values():
            item["quantity"] = float(item.get("quantity", 0))
    except Exception as e:
        print(f"[warn] Could not parse inventory JSON: {e}")
        return {}
    return raw



def save_inventory(data):

    for item in data.values():
        item["quantity"] = float(item.get("quantity", 0))
    INVENTORY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

def _to_ui_shape(inv):
    out = {}
    for k, v in (inv or {}).items():
        if isinstance(v, dict):
            qty = float(v.get("quantity", 0) or 0)
            unit = (v.get("unit") or "").strip()
        else:
            qty = 1.0 if v else 0.0
            unit = ""
        out[k] = {"quantity": qty, "unit": unit}
    return out


@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    inv = load_inventory(INVENTORY_PATH)
    return jsonify(_to_ui_shape(inv))

@app.route("/api/inventory", methods=["POST"])
def add_inventory_item():
    data = request.json or {}
    name = normalize_name(data.get("name", ""))
    qty = data.get("quantity", 0)
    unit = (data.get("unit") or "").strip()


    if not name:
        return jsonify({"error": "name required"}), 400

    inv = load_inventory(INVENTORY_PATH) or {}


    inv[name] = {"quantity": qty, "unit": unit}
    save_inventory(inv)

    return jsonify({"message": "Item added/updated",
                    "item": {"quantity": qty, "unit": unit}}), 201


@app.route("/api/inventory/reset", methods=["POST"])
def reset_inventory():

    save_inventory({})
    return jsonify({"message": "Inventory reset"})


@app.route("/api/inventory/<name>", methods=["PUT"])
def update_inventory_item(name):
    name = normalize_name(name)
    inv = load_inventory(INVENTORY_PATH) or {}
    if name not in inv:
        return jsonify({"error": "Not found"}), 404

    data = request.json or {}
    qty = float(data.get("quantity", 0) or 0)
    unit = (data.get("unit") or "").strip() 

    inv[name] = {"quantity": qty, "unit": unit}
    save_inventory(inv)
    return jsonify({"message": "Updated", "item": {"quantity": qty, "unit": unit}})


@app.route("/api/inventory/<name>", methods=["DELETE"])
def delete_inventory_item(name):
    name = normalize_name(name)
    inv = load_inventory(INVENTORY_PATH)
    if name not in inv:
        return jsonify({"error": "Not found"}), 404

    removed = inv.pop(name)
    save_inventory(inv)
    return jsonify({"message": "Deleted", "item": removed})


@app.route("/api/inventory/recipes")
def api_inventory_recipes():
    raw = load_inventory(INVENTORY_PATH)
    inventory = _to_bool_inv(raw) 
    matches = get_recipe_matches(inventory)

    combined = matches["cookable"] + matches["near"]
    search = (request.args.get("search") or "").strip().lower()
    if search:
        combined = [r for r in combined if search in r.get("title", "").lower()]
    return jsonify({"recipes": combined})

# ---- Recipes ---- #

@app.route("/api/recipes", methods=["GET"])
def get_recipes():
    return jsonify(load_data(RECIPES_FILE))

@app.route("/api/recipes/match")
def api_match_recipes():
    raw = load_inventory(INVENTORY_PATH)
    inventory = _to_bool_inv(raw)
    matches = get_recipe_matches(inventory, max_missing=3, top=50)
    recipes = matches["cookable"] + matches["near"]

    search = request.args.get("search", "").lower()
    if search:
        recipes = [r for r in recipes if search in r["title"].lower()]

    return jsonify({"recipes": recipes})


# ---- Favorites ---- #

@app.route("/api/favorites", methods=["GET"])
def get_favorites():
    favorites = load_data(FAVORITES_FILE)
    return jsonify(favorites)


@app.route("/api/favorites", methods=["POST"])
def add_favorite():
    data = request.json
    favorites = load_data(FAVORITES_FILE)

    if data not in favorites:
        favorites.append(data)
        save_data(FAVORITES_FILE, favorites)

    return jsonify({"message": "Added to favorites"}), 201


@app.route("/api/favorites", methods=["DELETE"])
def delete_favorite():
    data = request.get_json()
    title_to_remove = data.get("title")
    
    if not title_to_remove:
        return jsonify({"error": "Title required"}), 400
    
    favorites = load_data(FAVORITES_FILE)

    favorites = [f for f in favorites if f.get("title") != title_to_remove]
    save_data(FAVORITES_FILE, favorites)
    
    return jsonify({"message": "Favorite removed"})


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

def _to_bool_inv(inv):
    out = {}
    for k, v in (inv or {}).items():
        if isinstance(v, dict):
            q = float(v.get("quantity", 0) or 0)
            out[k] = q > 0
        else:
            out[k] = bool(v)
    return out


if __name__ == "__main__":
    app.run()
