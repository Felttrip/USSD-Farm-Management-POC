from flask import Flask, request

app = Flask(__name__)

# Mock data sourced from BASED advisory engine output (crop_advisories_sample_2026-06-18).
# Emoji stripped from titles — feature phones do not render unicode emoji.
FARMS = {
    "1": {
        "name": "Kiambu Kikuy",
        "crops": ["Avocado", "Maize", "Kale"],
        "advisories": [
            {
                "crop": "Avocado",
                "severity": "CRITICAL",
                "type": "irrigation",
                "title": "Avocado Seedlings: 19mm Water Deficit",
                "description": (
                    "Seedlings are 2 days old with tiny roots. Forecast shows "
                    "3.4mm rainfall vs 22.5mm evapotranspiration. "
                    "1,530 kg future yield at risk."
                ),
                "steps": [
                    "Apply 10-12mm to root zone today via drip or watering can",
                    "Do not irrigate again until June 25-27 (7-day interval on clay)",
                    "Check soil at 5cm depth before each irrigation",
                    "Clear drainage channels — waterlogging kills roots in 48hrs",
                ],
                "valid_days": 7,
            },
            {
                "crop": "Maize",
                "severity": "HIGH",
                "type": "irrigation",
                "title": "Maize Seedlings: 19mm Water Deficit",
                "description": (
                    "Maize is 8 days old. Forecast shows only 3.4mm rainfall "
                    "vs 22.5mm evapotranspiration — 19.1mm deficit. "
                    "2,280 kg at risk."
                ),
                "steps": [
                    "Irrigate 15-18mm today slowly over 2-3 hours",
                    "Clear drainage channels before irrigating",
                    "Do not irrigate again for 7-9 days unless wilting before noon",
                    "Apply water before 9am to reduce evaporation",
                ],
                "valid_days": 7,
            },
            {
                "crop": "Kale",
                "severity": "HIGH",
                "type": "fertilizer",
                "title": "Kale: First Nitrogen Top-Dress Due",
                "description": (
                    "At 17 days after planting, kale needs first nitrogen "
                    "top-dress for rapid leaf expansion. "
                    "Delaying past 3 weeks causes stunted leaf growth."
                ),
                "steps": [
                    "Apply CAN 100kg/ha (6,000kg total for 60ha)",
                    "Broadcast between rows, not on stems",
                    "Incorporate 3-5cm into soil with hand hoe",
                    "Irrigate same day to move nitrogen to root zone",
                    "Second dose at day 35-40 at same rate",
                ],
                "valid_days": 7,
            },
            {
                "crop": "Maize",
                "severity": "HIGH",
                "type": "fertilizer",
                "title": "Maize: Apply Starter Nitrogen Now",
                "description": (
                    "At 8 days after planting, seedlings need early nitrogen "
                    "for leaf and root establishment. "
                    "Mild temps (22-24C) create ideal uptake conditions."
                ),
                "steps": [
                    "Apply CAN 50kg/ha in band 5cm beside row, 5cm deep",
                    "Apply morning after irrigation when soil is moist",
                    "Do not broadcast on clay — risk of runoff",
                    "Reserve main nitrogen (DAP 150kg/ha) for V6 stage in late July",
                ],
                "valid_days": 10,
            },
            {
                "crop": "Kale",
                "severity": "MEDIUM",
                "type": "pest",
                "title": "Kale: Scout for Aphids & Caterpillars",
                "description": (
                    "Humidity 83-99% creates ideal conditions for aphid "
                    "build-up on young kale. Scout 10% of farm this week."
                ),
                "steps": [
                    "Walk W-pattern through 10% of farm, check leaf undersides",
                    "Look for aphid clusters and holes from caterpillars",
                    "If 3 in 10 plants infested, spray soap solution 5ml per litre",
                    "Re-scout every 7 days through establishment phase",
                ],
                "valid_days": 10,
            },
            {
                "crop": "Maize",
                "severity": "MEDIUM",
                "type": "frost",
                "title": "Maize: Monitor Night Temps as June Cools",
                "description": (
                    "At 1,674m altitude nights can approach 10C in June-July. "
                    "Forecast shows 13.9-15.8C this week — acceptable but "
                    "trending downward. Seedlings cannot recover from chilling."
                ),
                "steps": [
                    "Check thermometer at 6am daily",
                    "If 3 consecutive nights below 12C, mulch between rows 3-5cm",
                    "Avoid afternoon or evening irrigation during cold spells",
                    "Watch for yellowing or purple-tinged leaves at morning check",
                ],
                "valid_days": 21,
            },
        ],
    },
    "2": {
        "name": "Sunright",
        "crops": ["Potatoes", "Beans"],
        "advisories": [
            {
                "crop": "Potatoes",
                "severity": "CRITICAL",
                "type": "disease",
                "title": "Late Blight Risk - Spray by June 19",
                "description": (
                    "Beaumont criteria met 3 consecutive days: humidity above "
                    "85% and temps 11-15C. Blight can destroy entire field "
                    "in 5-7 days. 94,260 kg yield at risk."
                ),
                "steps": [
                    "Scout all 50ha TODAY for dark water-soaked lesions on lower leaves",
                    "Spray Mancozeb 80WP 2.0kg per 100L water on June 19",
                    "If active lesions found, switch to Cymoxanil+Mancozeb 2.5kg/ha",
                    "Repeat spray every 7 days while humidity stays above 79%",
                    "Remove and bury infected material — do NOT compost",
                ],
                "valid_days": 7,
            },
            {
                "crop": "Beans",
                "severity": "CRITICAL",
                "type": "irrigation",
                "title": "Beans Seedlings: 20.6mm Water Deficit",
                "description": (
                    "Beans planted 2 days ago. Only 3.1mm forecast vs 23.7mm "
                    "evapotranspiration. Loamy topsoil dries in 2-3 days. "
                    "470 kg yield at risk."
                ),
                "steps": [
                    "Irrigate 10-12mm TODAY morning across all 50ha",
                    "Apply 8-10mm again on June 21 (forecast shows zero rain)",
                    "Check soil at 5cm daily — should feel like a firm handshake",
                    "Use low pressure — heavy drops compact loamy soil and block emergence",
                ],
                "valid_days": 7,
            },
            {
                "crop": "Potatoes",
                "severity": "HIGH",
                "type": "irrigation",
                "title": "Potatoes: 20.6mm Water Deficit",
                "description": (
                    "Only 3.1mm rainfall forecast vs 23.7mm crop demand over "
                    "7 days. 5,740 kg yield already at risk. "
                    "Loamy soil does not buffer water stress well."
                ),
                "steps": [
                    "Irrigate 20-22mm before June 21, early morning or evening only",
                    "Avoid wetting foliage — increases late blight risk",
                    "Check soil every 3 days by digging 15cm with trowel",
                    "Target 32mm per week total from rain plus irrigation",
                ],
                "valid_days": 7,
            },
            {
                "crop": "Beans",
                "severity": "HIGH",
                "type": "frost",
                "title": "Beans: Cold Night Risk at 1744m",
                "description": (
                    "Min temps forecast 11.8C on June 21 — near 10C absolute "
                    "limit for beans. First-week seedlings are most cold-sensitive. "
                    "High humidity also raises damping-off risk."
                ),
                "steps": [
                    "Apply 3-4cm dry grass mulch between rows before sunset June 20",
                    "Do NOT irrigate evenings of June 20 or 21",
                    "Scout for damping-off daily — look for stem pinching at soil level",
                    "Apply copper fungicide if over 5% of stands show symptoms",
                ],
                "valid_days": 7,
            },
            {
                "crop": "Potatoes",
                "severity": "MEDIUM",
                "type": "fertilizer",
                "title": "Potatoes: First Nitrogen Top-Dress Due",
                "description": (
                    "At 17 days after planting, potato crop needs first nitrogen "
                    "top-dress. Split application essential — single large dose "
                    "will leach below roots on loamy soil."
                ),
                "steps": [
                    "Apply CAN 150kg/ha (7,500kg total) between rows within 5 days",
                    "Broadcast between rows, do not put on stems or leaves",
                    "Time application just before irrigation to move into soil",
                    "Plan second top-dress at tuber initiation (day 35-45) at 100-120kg/ha",
                ],
                "valid_days": 5,
            },
            {
                "crop": "Beans",
                "severity": "MEDIUM",
                "type": "pest",
                "title": "Beans: Caterpillar Risk from Butterflies",
                "description": (
                    "Painted Lady and Plain Tiger butterflies observed within 100km. "
                    "Larvae feed on bean foliage. Even partial defoliation at "
                    "seedling stage permanently sets back development."
                ),
                "steps": [
                    "Scout 10 plants per hectare, check leaf undersides for eggs or larvae",
                    "If over 5% of plants infested, spray Lambda-cyhalothrin 5EC 10ml/15L",
                    "Do not spray broad-spectrum if below threshold — protects pollinators",
                    "Set 3-5 yellow sticky traps around farm perimeter as early warning",
                ],
                "valid_days": 14,
            },
        ],
    },
}

CROP_CATEGORIES = {
    "1": {
        "name": "Cereals",
        "crops": ["Maize", "Wheat", "Sorghum", "Millet", "Rice"],
    },
    "2": {
        "name": "Legumes",
        "crops": ["Beans", "Soybeans", "Groundnuts", "Cowpeas", "Lentils"],
    },
    "3": {
        "name": "Roots & Tubers",
        "crops": ["Potatoes", "Sweet Potatoes", "Cassava", "Yams", "Arrowroot"],
    },
    "4": {
        "name": "Vegetables",
        "crops": ["Kale", "Tomatoes", "Spinach", "Cabbage", "Onions"],
    },
    "5": {
        "name": "Fruits",
        "crops": ["Avocado", "Mango", "Banana", "Passion Fruit", "Papaya"],
    },
    "6": {
        "name": "Oil Crops",
        "crops": ["Sunflower", "Sesame", "Canola", "Palm", "Safflower"],
    },
    "7": {
        "name": "Cash Crops",
        "crops": ["Coffee", "Tea", "Sugarcane", "Cotton", "Tobacco"],
    },
}

SEVERITY_TAG = {
    "CRITICAL": "[CRIT]",
    "HIGH": "[HIGH]",
    "MEDIUM": "[MED]",
    "LOW": "[LOW]",
}

NAV = "\n0. Back  00. Home"


def resolve_path(raw_inputs):
    """Replay inputs, treating 0 as back and 00 as go-to-home."""
    path = []
    for inp in raw_inputs:
        if inp == "00":
            path = []
        elif inp == "0":
            if path:
                path.pop()
        else:
            path.append(inp)
    return path


# ---------------------------------------------------------------------------
# Screen renderers — advisories flow
# ---------------------------------------------------------------------------

def farm_list_screen():
    lines = ["CON Select your farm:"]
    for key, farm in FARMS.items():
        lines.append(f"{key}. {farm['name']}")
    return "\n".join(lines)


def farm_menu_screen(farm):
    return (
        f"CON Managing {farm['name']}:\n"
        f"1. See Advisories\n"
        f"2. Manage Crops"
        f"{NAV}"
    )


def advisories_list_screen(farm):
    advisories = farm["advisories"]
    if not advisories:
        return f"CON No active advisories for this farm.{NAV}"
    lines = ["CON Active Advisories:"]
    for i, adv in enumerate(advisories, 1):
        tag = SEVERITY_TAG.get(adv["severity"], "")
        lines.append(f"{i}. {tag} {adv['crop']}: {adv['title'][:22]}")
    lines.append("0. Back  00. Home")
    return "\n".join(lines)


def advisory_detail_screen(adv):
    tag = SEVERITY_TAG.get(adv["severity"], "")
    desc = adv["description"][:120]
    return (
        f"CON {tag} {adv['crop']} - {adv['title']}\n"
        f"{desc}\n"
        f"1. See action steps"
        f"{NAV}"
    )


def advisory_steps_screen(adv):
    steps = "\n".join(f"{i}. {s}" for i, s in enumerate(adv["steps"], 1))
    return (
        f"CON {adv['crop']} - Actions:\n"
        f"{steps}\n"
        f"Valid: {adv['valid_days']} days"
        f"{NAV}"
    )


# ---------------------------------------------------------------------------
# Screen renderers — manage crops flow
# ---------------------------------------------------------------------------

def crops_list_screen(farm):
    crops = farm["crops"]
    lines = [f"CON {farm['name']} Crops:"]
    for i, crop in enumerate(crops, 1):
        lines.append(f"{i}. {crop}")
    add_option = len(crops) + 1
    lines.append(f"{add_option}. Add Crop")
    lines.append("0. Back  00. Home")
    return "\n".join(lines)


def crop_manage_screen(farm, crop_name):
    return (
        f"CON Managing {crop_name}:\n"
        f"1. Remove {crop_name}\n"
        f"2. View advisories for {crop_name}"
        f"{NAV}"
    )


def crop_advisories_screen(farm, crop_name):
    matching = [a for a in farm["advisories"] if a["crop"] == crop_name]
    if not matching:
        return f"CON No advisories for {crop_name}.{NAV}"
    lines = [f"CON {crop_name} Advisories:"]
    for i, adv in enumerate(matching, 1):
        tag = SEVERITY_TAG.get(adv["severity"], "")
        lines.append(f"{i}. {tag} {adv['title'][:28]}")
    lines.append("0. Back  00. Home")
    return "\n".join(lines)


def add_crop_category_screen():
    lines = ["CON Add Crop - Select Category:"]
    for key, cat in CROP_CATEGORIES.items():
        lines.append(f"{key}. {cat['name']}")
    lines.append("0. Back  00. Home")
    return "\n".join(lines)


def add_crop_select_screen(category):
    lines = [f"CON {category['name']} - Select Crop:"]
    for i, crop in enumerate(category["crops"], 1):
        lines.append(f"{i}. {crop}")
    lines.append("0. Back  00. Home")
    return "\n".join(lines)


def crop_added_screen(crop_name, farm_name):
    return (
        f"END {crop_name} has been added to {farm_name}! "
        f"You will now receive advisories for this crop."
    )


def crop_removed_screen(crop_name, farm_name):
    return (
        f"END {crop_name} has been removed from {farm_name}."
    )


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

@app.route("/ussd", methods=["POST"])
def ussd_callback():
    text = request.form.get("text", "")
    raw_inputs = text.split("*") if text else []
    inputs = resolve_path(raw_inputs)
    level = len(inputs)

    # Level 0 — home: show farm list
    if level == 0:
        return farm_list_screen()

    farm_key = inputs[0]
    farm = FARMS.get(farm_key)
    if not farm:
        return "END Invalid selection. Please try again."

    # Level 1 — farm selected: show farm management menu
    if level == 1:
        return farm_menu_screen(farm)

    menu_choice = inputs[1]

    # ---- Advisories branch (menu_choice == "1") ----------------------------

    if menu_choice == "1":
        if level == 2:
            return advisories_list_screen(farm)

        # Level 3 — advisory selected from all-advisories list
        if level == 3:
            try:
                adv = farm["advisories"][int(inputs[2]) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            return advisory_detail_screen(adv)

        # Level 4 — action steps from all-advisories detail
        if level == 4 and inputs[3] == "1":
            try:
                adv = farm["advisories"][int(inputs[2]) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            return advisory_steps_screen(adv)

    # ---- Manage Crops branch (menu_choice == "2") --------------------------

    elif menu_choice == "2":
        crops = farm["crops"]
        add_option = str(len(crops) + 1)

        # Level 2 — crop list
        if level == 2:
            return crops_list_screen(farm)

        crop_choice = inputs[2]

        # Level 3 — crop selected or add crop chosen
        if level == 3:
            if crop_choice == add_option:
                return add_crop_category_screen()
            try:
                crop_name = crops[int(crop_choice) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            return crop_manage_screen(farm, crop_name)

        # Level 4
        if level == 4:
            if crop_choice == add_option:
                # Category selected — show crops in that category
                cat = CROP_CATEGORIES.get(inputs[3])
                if not cat:
                    return "END Invalid category. Please try again."
                return add_crop_select_screen(cat)
            else:
                # Action on existing crop: 1=remove, 2=view advisories
                try:
                    crop_name = crops[int(crop_choice) - 1]
                except (ValueError, IndexError):
                    return "END Invalid selection. Please try again."
                action = inputs[3]
                if action == "1":
                    return crop_removed_screen(crop_name, farm["name"])
                elif action == "2":
                    return crop_advisories_screen(farm, crop_name)
                else:
                    return "END Invalid option. Please try again."

        # Level 5 — specific crop selected from category to add
        if level == 5 and crop_choice == add_option:
            cat = CROP_CATEGORIES.get(inputs[3])
            if not cat:
                return "END Invalid category. Please try again."
            try:
                new_crop = cat["crops"][int(inputs[4]) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            return crop_added_screen(new_crop, farm["name"])

        # Level 5 — advisory detail from crop-specific advisory list
        if level == 5 and inputs[3] == "2":
            try:
                crop_name = crops[int(crop_choice) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            matching = [a for a in farm["advisories"] if a["crop"] == crop_name]
            try:
                adv = matching[int(inputs[4]) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            return advisory_detail_screen(adv)

        # Level 6 — action steps from crop-specific advisory detail
        if level == 6 and inputs[3] == "2" and inputs[5] == "1":
            try:
                crop_name = crops[int(crop_choice) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            matching = [a for a in farm["advisories"] if a["crop"] == crop_name]
            try:
                adv = matching[int(inputs[4]) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            return advisory_steps_screen(adv)

    return "END Invalid option. Please try again."


if __name__ == "__main__":
    app.run(debug=True, port=5000)
