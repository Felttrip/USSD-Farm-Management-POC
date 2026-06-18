# BASED USSD POC

A Python proof-of-concept for delivering BASED agricultural advisories to smallholder farmers in East Africa via USSD, built for [Blooming World International](https://blwi.org/).

USSD lets farmers on basic feature phones (no smartphone, no internet, 2G only) dial a shortcode like `*384#` to access their farm advisories — the same technology behind M-Pesa. The server receives HTTP POST requests from Africa's Talking's USSD gateway and responds with menu screens.

## Features

- **Farm advisory delivery** — farmers browse advisories across all crops, with severity tags and action steps
- **Manage crops** — add or remove crops per farm; add flow collects crop category, specific crop, and planting date
- **Add farm** — collect farm name, GPS coordinates, and soil condition
- **Rate past advisories** — feedback flow to mark whether advice was helpful
- **Per-farmer in-memory state** — each phone number gets its own mutable copy of farm data; mutations (add/remove farm/crop) persist across dial-ins until server restart
- **Cross-dial-in session resume** — if a farmer hangs up mid-flow, the home screen offers a Resume option on their next dial-in (configurable TTL)
- **`0` / `00` navigation** — back one page / return home, available on every screen

## Menu Tree

```
Dial *XXX#
└── Home: Select Farm  (+ Add Farm, + Resume if session saved)
    │
    ├── Add Farm
    │   └── Enter name → Enter GPS coordinates → Select soil condition → Confirmation
    │
    └── Managing <Farm>
        ├── 1. See Advisories
        │   └── Advisory list (all crops, sorted by severity)
        │       └── Advisory detail (title + description)
        │           └── Action steps
        │
        ├── 2. Manage Crops
        │   ├── Select existing crop
        │   │   ├── Remove crop → Confirmation (END)
        │   │   └── View advisories for crop
        │   │       └── Advisory detail → Action steps
        │   └── Add Crop
        │       └── Select category (Cereals, Legumes, Roots & Tubers, Vegetables, Fruits, Oil Crops, Cash Crops)
        │           └── Select specific crop
        │               └── Select planting date (today / 1 day ago / 3 days ago / 7 days ago / 14 days ago / 30 days ago)
        │                   └── Confirmation (END)
        │
        └── 3. Rate Past Advisories
            └── Was recent advice helpful? (Yes / No / Call me) → Confirmation (END)
```

Navigation is available on every screen: `0` goes back one page, `00` returns home.

## Architecture

The route handler is split into two layers:

- **`ussd_callback()`** — thin wrapper bound to `POST /ussd`. Reads `text` and `phoneNumber`, applies session-resume splice logic, delegates to `render_screen()`, then saves or clears the session based on the response prefix (`CON`/`END`).
- **`render_screen(inputs, farms, saved, resume_key)`** — pure function with no side effects. Maps a resolved `inputs` list to a `CON`/`END` string.

### Navigation model

Africa's Talking resends the full `text` history on every request (e.g. `1*2*3`). `resolve_path()` replays this list, treating `0` as pop-back and `00` as reset-to-home, before routing. This means no server-side session storage is needed for navigation within a single call.

### Per-farmer state

`FARMER_STATE` is an in-memory dict keyed by phone number. On first contact, a deep copy of the shared `FARMS` seed data is created for that phone. Add/remove operations on farms and crops mutate only that phone's copy, so changes persist across dial-ins for the lifetime of the server process.

### Session resume

`ACTIVE_SESSIONS` stores the resolved navigation path and a human-readable label for each phone number on every `CON` response. When the farmer dials in again, the home screen shows a Resume option. Selecting it splices the saved path into the input replay before routing, landing the farmer on the screen they left. Entries expire after `SESSION_TTL_SECONDS` (default `50000`).

## Project Structure

```
.
├── app.py                    # Main Flask app — all USSD logic
├── requirements.txt          # Python dependencies (flask>=3.0)
├── CLAUDE.md                 # Developer notes and curl simulation examples
├── docs/
│   ├── ussd-flow.md          # Full flow documentation with Mermaid diagrams
│   └── proposed-final-flow.mmd  # Mermaid diagram of proposed production flow
└── sms-minimization/
    ├── bedrock_invoke.py     # AWS Bedrock invocation to compress advisories to SMS length
    ├── prompt.txt            # Compression prompt for the Bedrock model
    └── pyproject.toml        # Dependencies for the sms-minimization subproject
```

## Running Locally

**1. Create and activate a virtual environment**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Start the server**

```bash
python app.py
```

The server runs on `http://localhost:5000`. On macOS, port 5000 is used by AirPlay Receiver — use `python app.py` with a port override or disable AirPlay if needed.

**4. Expose it to Africa's Talking (for live testing)**

Africa's Talking needs a public URL to POST to. Use [ngrok](https://ngrok.com/):

```bash
ngrok http 5000
```

Set the callback URL in your Africa's Talking sandbox to `https://<your-ngrok-id>.ngrok.io/ussd`.

## Testing Without the Gateway

Simulate Africa's Talking POST requests with curl. Africa's Talking appends each new user input to the `text` field separated by `*`. The server resolves `0` (back) and `00` (home) by replaying the input history before routing.

```bash
# Initial dial-in — show farm list
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=s1&serviceCode=*384*1#&phoneNumber=+254712345678&text="

# Select farm 1 → farm menu
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=s1&serviceCode=*384*1#&phoneNumber=+254712345678&text=1"

# Farm 1 → See Advisories
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=s1&serviceCode=*384*1#&phoneNumber=+254712345678&text=1*1"

# Farm 1 → Advisory 1 → See action steps
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=s1&serviceCode=*384*1#&phoneNumber=+254712345678&text=1*1*1*1"

# Farm 1 → Manage Crops → Add Crop → Fruits (5) → first crop → planted today (1)
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=s1&serviceCode=*384*1#&phoneNumber=+254712345678&text=1*2*4*5*1*1"

# Farm 1 → Manage Crops → Remove crop 1
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=s1&serviceCode=*384*1#&phoneNumber=+254712345678&text=1*2*1*1"

# Add a new farm (select "Add Farm" option — key depends on how many farms exist)
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=s1&serviceCode=*384*1#&phoneNumber=+254712345678&text=3"

# Farm 1 → Rate Past Advisories
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=s1&serviceCode=*384*1#&phoneNumber=+254712345678&text=1*3*1"

# Back from advisories list → farm menu
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=s1&serviceCode=*384*1#&phoneNumber=+254712345678&text=1*1*0"

# Home from advisory detail
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=s1&serviceCode=*384*1#&phoneNumber=+254712345678&text=1*1*1*00"
```

## Africa's Talking Callback Fields

| Field | Description |
|---|---|
| `sessionId` | Unique session identifier |
| `serviceCode` | The dialled shortcode (e.g. `*384*1#`) |
| `phoneNumber` | Farmer's phone number in E.164 format |
| `text` | All inputs so far, joined by `*` (empty string on first request) |

Responses must be plain text prefixed with `CON ` (continue session) or `END ` (terminate session).

## SMS Minimization Subproject

`sms-minimization/` is a standalone experiment for compressing BASED advisories to SMS length (160 chars) using AWS Bedrock. See `sms-minimization/bedrock_invoke.py` and `sms-minimization/prompt.txt`.

## Project Context

This POC is part of the **BASED Last-Mile Delivery** engagement between [Blooming World International](https://blwi.org/) and the Twilio Builder Corps × Taproot Foundation volunteer team (June 2026). The goal is to design how BASED's AI-generated farm advisories can reach the ~75% of East African smallholder farmers who have feature phones only — no smartphone, no internet access.

The advisory data in `app.py` is sourced from real BASED engine output for farms in Kiambu and Thika, Kenya. For the full flow diagrams and routing documentation, see [`docs/ussd-flow.md`](docs/ussd-flow.md).
