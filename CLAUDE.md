# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
# Install dependency
pip install -r requirements.txt

# Start the dev server on port 5000
python3 app.py
```

## Simulating USSD sessions

The `/ussd` endpoint accepts POST requests with a `text` field. Inputs are `*`-delimited and accumulate across the session (Africa's Talking gateway convention):

```bash
# Home screen (no input yet)
curl -X POST http://localhost:5000/ussd -d "text="

# Select farm 1
curl -X POST http://localhost:5000/ussd -d "text=1"

# Farm 1 → Advisories
curl -X POST http://localhost:5000/ussd -d "text=1*1"

# Farm 1 → Advisories → Advisory 2
curl -X POST http://localhost:5000/ussd -d "text=1*1*2"

# Navigate back (0) or home (00) — resolved server-side
curl -X POST http://localhost:5000/ussd -d "text=1*1*0"
```

## Architecture

**Single file:** `app.py` contains all routing, screen renderers, and mock data.

### Navigation model

`resolve_path(raw_inputs)` replays the full `*`-split input history on every request, treating `0` as pop-back and `00` as reset-to-home. The resulting `inputs` list and its `len()` (`level`) drive all branching in `ussd_callback()`.

### Response format

- `CON …` — session continues; user will see a menu and can reply
- `END …` — session terminates; no further input expected

### Screen renderers

Pure functions that take farm/advisory data and return a `CON`/`END` string. They live above the route handler, grouped by flow:
- **Advisories flow** — `farm_list_screen`, `farm_menu_screen`, `advisories_list_screen`, `advisory_detail_screen`, `advisory_steps_screen`
- **Manage Crops flow** — `crops_list_screen`, `crop_manage_screen`, `crop_advisories_screen`, `add_crop_category_screen`, `add_crop_select_screen`, `crop_added_screen`, `crop_removed_screen`

### Mock data

`FARMS` and `CROP_CATEGORIES` are hardcoded dicts. Advisory data is sourced from BASED advisory engine output (`crop_advisories_sample_2026-06-18`). Emojis are intentionally stripped — feature phones don't render Unicode.

`SEVERITY_TAG` maps severity strings to `[CRIT]`/`[HIGH]`/`[MED]`/`[LOW]` prefixes, kept short to fit USSD character limits.

### USSD character limits

USSD screens are constrained to ~182 characters per response on most networks. Titles are truncated (e.g. `[:22]`, `[:28]`) and descriptions capped at 120 characters in `advisory_detail_screen` to stay within limits.
