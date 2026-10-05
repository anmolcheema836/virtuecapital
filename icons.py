from PIL import Image
from pathlib import Path

# ==========================================
# SETTINGS
# ==========================================

INPUT_FILE = "testimg.png"
OUTPUT_DIR = "food_icons"

COLUMNS = 10
ROWS = 5

# Names must match the AI-generated order
ICON_NAMES = [
    "burger",
    "pizza",
    "french-fries",
    "chicken-wings",
    "sandwich",
    "hot-dog",
    "tacos",
    "nachos",
    "burrito",
    "fried-chicken",

    "steak",
    "bbq-ribs",
    "grilled-chicken",
    "chicken-tikka",
    "kebab",
    "meatballs",
    "pasta",
    "noodles",
    "biryani",
    "fried-rice",

    "curry",
    "soup",
    "salad",
    "paneer-tikka",
    "samosa",
    "spring-rolls",
    "momos",
    "dosa",
    "idli",
    "omelette",

    "toast",
    "pancakes",
    "waffle",
    "croissant",
    "cake",
    "donut",
    "brownie",
    "cookie",
    "ice-cream",
    "cheesecake",

    "coffee",
    "espresso",
    "cappuccino",
    "latte",
    "tea",
    "masala-chai",
    "milkshake",
    "smoothie",
    "fresh-juice",
    "soft-drink"
]


# ==========================================
# LOAD IMAGE
# ==========================================

image = Image.open(INPUT_FILE).convert("RGBA")

width, height = image.size

cell_width = width // COLUMNS
cell_height = height // ROWS

print(f"Image size: {width} x {height}")
print(f"Cell size: {cell_width} x {cell_height}")


# ==========================================
# CREATE OUTPUT DIRECTORY
# ==========================================

output_path = Path(OUTPUT_DIR)
output_path.mkdir(exist_ok=True)


# ==========================================
# SPLIT IMAGE
# ==========================================

for index, name in enumerate(ICON_NAMES):

    row = index // COLUMNS
    column = index % COLUMNS

    left = column * cell_width
    top = row * cell_height

    right = left + cell_width
    bottom = top + cell_height

    icon = image.crop((left, top, right, bottom))

    filename = output_path / f"{name}.png"

    icon.save(filename)

    print(f"[{index + 1:02}] {name}.png")


print()
print("Done!")
print(f"Created {len(ICON_NAMES)} icons in: {OUTPUT_DIR}")