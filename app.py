import copy
import os
import time
import africastalking
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

AT_USERNAME = os.getenv("AT_USERNAME")
AT_API_KEY = os.getenv("AT_API_KEY")
print(f"[CONFIG] AT_USERNAME={AT_USERNAME!r}  AT_API_KEY={AT_API_KEY[:8] + '...' if AT_API_KEY else None!r}")

africastalking.initialize(AT_USERNAME, AT_API_KEY)

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Session store (in-memory POC — no Redis)
# ---------------------------------------------------------------------------
ACTIVE_SESSIONS = {}
SESSION_TTL_SECONDS = 50000


def get_saved_session(phone):
    entry = ACTIVE_SESSIONS.get(phone)
    if not entry:
        return None
    if time.time() - entry["saved_at"] > SESSION_TTL_SECONDS:
        ACTIVE_SESSIONS.pop(phone, None)
        return None
    return entry


def save_session(phone, path, label):
    if not phone:
        return
    ACTIVE_SESSIONS[phone] = {"path": list(path), "label": label, "saved_at": time.time()}


def clear_saved_session(phone):
    ACTIVE_SESSIONS.pop(phone, None)


# Per-farmer state keyed by phone number.
# Seeded on first contact from the shared FARMS mock data.
FARMER_STATE = {}


def get_farmer_farms(phone):
    if phone not in FARMER_STATE:
        FARMER_STATE[phone] = copy.deepcopy(FARMS)
    return FARMER_STATE[phone]


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

SOIL_CONDITIONS = {
    "1": "Clay",
    "2": "Loamy",
    "3": "Sandy",
    "4": "Silt",
    "5": "Peaty",
    "6": "Chalky",
}

SEVERITY_TAG = {
    "CRITICAL": "[CRIT]",
    "HIGH": "[HIGH]",
    "MEDIUM": "[MED]",
    "LOW": "[LOW]",
}

NAV = "\n0. Back  00. Home"

FEEDBACK = []


def store_feedback(farm_key, adv_index, rating_input, source):
    rating = "good" if rating_input == "1" else "not_good"
    entry = {"farm": farm_key, "adv_index": adv_index, "rating": rating, "source": source}
    FEEDBACK.append(entry)
    print(f"[FEEDBACK] {entry}")
    return rating


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

def home_screen(farms, saved, resume_key):
    """Farm list with Add Farm and optional Resume appended."""
    lines = ["CON Select your farm:"]
    for key, farm in farms.items():
        lines.append(f"{key}. {farm['name']}")
    add_option = len(farms) + 1
    lines.append(f"{add_option}. Add Farm")
    if saved:
        lines.append(f"{resume_key}. Resume: {saved['label']}")
    return "\n".join(lines)


def describe_screen(inputs, farms):
    """Coarse human-readable label for the current screen, for the resume hint."""
    farm = farms.get(inputs[0]) if inputs else None
    if not farm:
        return "your session"
    if len(inputs) == 1:
        return farm["name"]
    if inputs[1] == "1":
        return f"{farm['name']} Advisories"
    if inputs[1] == "2":
        add_option = str(len(farm["crops"]) + 1)
        if len(inputs) >= 3 and inputs[2] == add_option:
            return "Add Crop"
        return f"{farm['name']} Crops"
    return farm["name"]


def add_farm_name_screen():
    return "CON Enter farm name:"


def add_farm_gps_screen(farm_name):
    return f"CON {farm_name}\nEnter GPS coordinates:\n(e.g. -1.2921,36.8219)"


def add_farm_soil_screen(farm_name):
    lines = [f"CON {farm_name}\nSelect soil condition:"]
    for key, soil in SOIL_CONDITIONS.items():
        lines.append(f"{key}. {soil}")
    lines.append("0. Back  00. Home")
    return "\n".join(lines)


def farm_added_screen(farm_name, gps, soil):
    return (
        f"END {farm_name} has been added! "
        f"GPS: {gps}. Soil: {soil}. "
        f"You can now add crops and receive advisories for this farm."
    )


def farm_menu_screen(farm):
    return (
        f"CON Managing {farm['name']}:\n"
        f"1. See Advisories\n"
        f"2. Manage Crops\n"
        f"3. Rate Past Advisories"
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
        f"1. See action steps\n"
        f"2. Rate this advisory\n"
        f"3. Send to SMS"
        f"{NAV}"
    )


def advisory_steps_screen(adv):
    steps = "\n".join(f"{i}. {s}" for i, s in enumerate(adv["steps"], 1))
    return (
        f"CON {adv['crop']} - Actions:\n"
        f"{steps}\n"
        f"Valid: {adv['valid_days']} days\n"
        f"Rate: 1-Good  2-Not good"
        f"{NAV}"
    )


def rate_advisory_screen(adv):
    tag = SEVERITY_TAG.get(adv["severity"], "")
    return (
        f"CON {tag} {adv['crop']} - {adv['title'][:30]}\n"
        f"Rate this advisory:\n"
        f"1. Good advice\n"
        f"2. Not good advice"
        f"{NAV}"
    )


def feedback_received_screen(adv):
    tag = SEVERITY_TAG.get(adv["severity"], "")
    return (
        f"CON Thank you! Feedback recorded for:\n"
        f"{tag} {adv['crop']} - {adv['title'][:30]}"
        f"{NAV}"
    )


def sms_sent_screen(phone_number):
    return (
        f"CON Advisory sent to {phone_number}."
        f"{NAV}"
    )


def send_advisory_sms(phone_number, adv):
    steps = "\n".join(f"{i}. {s}" for i, s in enumerate(adv["steps"], 1))
    body = (
        f"{adv['crop']} - {adv['title']}\n"
        f"{adv['description']}\n\n"
        f"Steps:\n{steps}\n"
        f"Valid: {adv['valid_days']} days"
    )
    africastalking.SMS.send(body, [phone_number])


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


PLANTING_DATES = {
    "1": "0 days ago",
    "2": "1 day ago",
    "3": "3 days ago",
    "4": "7 days ago",
    "5": "14 days ago",
    "6": "30 days ago",
}


def planting_date_screen(crop_name):
    lines = [f"CON When did you plant {crop_name}?"]
    for key, label in PLANTING_DATES.items():
        lines.append(f"{key}. {label.capitalize()}")
    lines.append("0. Back  00. Home")
    return "\n".join(lines)


def crop_added_screen(crop_name, farm_name, planted):
    return (
        f"END {crop_name} has been added to {farm_name}! "
        f"Planted: {planted}. "
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
    phone = request.form.get("phoneNumber", "unknown")
    raw_inputs = text.split("*") if text else []

    farms = get_farmer_farms(phone)
    saved = get_saved_session(phone)
    resume_key = str(len(farms) + 2)

    is_resume = bool(saved and raw_inputs and raw_inputs[0] == resume_key)
    if is_resume:
        raw_inputs = list(saved["path"]) + raw_inputs[1:]

    inputs = resolve_path(raw_inputs)
    response = render_screen(inputs, farms, saved, resume_key)

    if response.startswith("CON"):
        if inputs and not is_resume:
            save_session(phone, inputs, describe_screen(inputs, farms))
        elif is_resume:
            save_session(phone, saved["path"], saved["label"])
    else:
        clear_saved_session(phone)

    return response


def render_screen(inputs, farms, saved=None, resume_key=None):
    """Pure router: resolved inputs -> CON/END string. No session side effects."""
    level = len(inputs)

    # Level 0 — home: farm list with Add Farm and optional Resume
    if level == 0:
        return home_screen(farms, saved, resume_key)

    farm_key = inputs[0]
    add_farm_option = str(len(farms) + 1)

    # ---- Add Farm branch ---------------------------------------------------

    if farm_key == add_farm_option:
        if level == 1:
            return add_farm_name_screen()
        farm_name = inputs[1]
        if level == 2:
            return add_farm_gps_screen(farm_name)
        gps = inputs[2]
        if level == 3:
            return add_farm_soil_screen(farm_name)
        soil_key = inputs[3]
        soil = SOIL_CONDITIONS.get(soil_key)
        if not soil:
            return "END Invalid selection. Please try again."
        new_key = str(len(farms) + 1)
        farms[new_key] = {"name": farm_name, "gps": gps, "soil": soil, "crops": [], "advisories": []}
        return farm_added_screen(farm_name, gps, soil)

    # ---- Existing farm branch ----------------------------------------------

    farm = farms.get(farm_key)
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

        # Level 4 — action steps or rate screen from all-advisories detail
        if level == 4 and inputs[3] == "1":
            try:
                adv = farm["advisories"][int(inputs[2]) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            return advisory_steps_screen(adv)

        if level == 4 and inputs[3] == "2":
            try:
                adv = farm["advisories"][int(inputs[2]) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            return rate_advisory_screen(adv)

        if level == 4 and inputs[3] == "3":
            try:
                adv = farm["advisories"][int(inputs[2]) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            send_advisory_sms(phone_number, adv)
            return sms_sent_screen(phone_number)

        # Level 5 — feedback from detail rate screen (Path A)
        if level == 5 and inputs[3] == "2" and inputs[4] in ("1", "2"):
            try:
                adv_index = int(inputs[2]) - 1
                adv = farm["advisories"][adv_index]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            store_feedback(farm_key, adv_index, inputs[4], "immediate")
            return feedback_received_screen(adv)

        # Level 5 — immediate feedback from all-advisories action steps
        if level == 5 and inputs[3] == "1" and inputs[4] in ("1", "2"):
            try:
                adv_index = int(inputs[2]) - 1
                adv = farm["advisories"][adv_index]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            store_feedback(farm_key, adv_index, inputs[4], "immediate")
            return feedback_received_screen(adv)

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
                    farm["crops"].remove(crop_name)
                    return crop_removed_screen(crop_name, farm["name"])
                elif action == "2":
                    return crop_advisories_screen(farm, crop_name)
                else:
                    return "END Invalid option. Please try again."

        # Level 5 — specific crop selected from category: ask planting date
        if level == 5 and crop_choice == add_option:
            cat = CROP_CATEGORIES.get(inputs[3])
            if not cat:
                return "END Invalid category. Please try again."
            try:
                new_crop = cat["crops"][int(inputs[4]) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            return planting_date_screen(new_crop)

        # Level 6 — planting date selected: confirm crop added
        if level == 6 and crop_choice == add_option:
            cat = CROP_CATEGORIES.get(inputs[3])
            if not cat:
                return "END Invalid category. Please try again."
            try:
                new_crop = cat["crops"][int(inputs[4]) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            planted = PLANTING_DATES.get(inputs[5])
            if not planted:
                return "END Invalid selection. Please try again."
            if new_crop not in farm["crops"]:
                farm["crops"].append(new_crop)
            return crop_added_screen(new_crop, farm["name"], planted)

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

        # Level 6 — action steps or rate screen from crop-specific advisory detail
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

        if level == 6 and inputs[3] == "2" and inputs[5] == "2":
            try:
                crop_name = crops[int(crop_choice) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            matching = [a for a in farm["advisories"] if a["crop"] == crop_name]
            try:
                adv = matching[int(inputs[4]) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            return rate_advisory_screen(adv)

        if level == 6 and inputs[3] == "2" and inputs[5] == "3":
            try:
                crop_name = crops[int(crop_choice) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            matching = [a for a in farm["advisories"] if a["crop"] == crop_name]
            try:
                adv = matching[int(inputs[4]) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            send_advisory_sms(phone_number, adv)
            return sms_sent_screen(phone_number)

        # Level 7 — feedback from detail rate screen (Path B)
        if level == 7 and inputs[3] == "2" and inputs[5] == "2" and inputs[6] in ("1", "2"):
            try:
                crop_name = crops[int(crop_choice) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            matching = [a for a in farm["advisories"] if a["crop"] == crop_name]
            try:
                adv_index_in_matching = int(inputs[4]) - 1
                adv = matching[adv_index_in_matching]
                adv_index = farm["advisories"].index(adv)
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            store_feedback(farm_key, adv_index, inputs[6], "immediate")
            return feedback_received_screen(adv)

        # Level 7 — immediate feedback from crop-specific advisory action steps
        if level == 7 and inputs[3] == "2" and inputs[5] == "1" and inputs[6] in ("1", "2"):
            try:
                crop_name = crops[int(crop_choice) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            matching = [a for a in farm["advisories"] if a["crop"] == crop_name]
            try:
                adv_index_in_matching = int(inputs[4]) - 1
                adv = matching[adv_index_in_matching]
                adv_index = farm["advisories"].index(adv)
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            store_feedback(farm_key, adv_index, inputs[6], "immediate")
            return feedback_received_screen(adv)

    # ---- Rate Past Advisories branch (menu_choice == "3") ------------------

    elif menu_choice == "3":
        # Level 2 — list all advisories to rate
        if level == 2:
            return advisories_list_screen(farm)

        # Level 3 — show rating screen for selected advisory
        if level == 3:
            try:
                adv = farm["advisories"][int(inputs[2]) - 1]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            return rate_advisory_screen(adv)

        # Level 4 — record past feedback
        if level == 4 and inputs[3] in ("1", "2"):
            try:
                adv_index = int(inputs[2]) - 1
                adv = farm["advisories"][adv_index]
            except (ValueError, IndexError):
                return "END Invalid selection. Please try again."
            store_feedback(farm_key, adv_index, inputs[3], "past")
            return feedback_received_screen(adv)

    return "END Invalid option. Please try again."


if __name__ == "__main__":
    app.run(debug=True, port=5000)
