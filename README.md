# BASED USSD POC

A Python proof-of-concept for delivering BASED agricultural advisories to smallholder farmers in East Africa via USSD, built for [Blooming World International](https://blwi.org/).

USSD lets farmers on basic feature phones (no smartphone, no internet, 2G only) dial a shortcode like `*384#` to access their farm advisories — the same technology behind M-Pesa. The server receives HTTP POST requests from Africa's Talking's USSD gateway and responds with menu screens.

## Menu Flow

```
Dial *XXX#
└── Select Farm
    └── Managing <Farm>
        ├── See Advisories
        │   └── Advisory list (all crops, sorted by severity)
        │       └── Advisory detail (description)
        │           └── Action steps
        └── Manage Crops
            ├── Select existing crop
            │   ├── Remove crop
            │   └── View advisories for crop
            │       └── Advisory detail → Action steps
            └── Add Crop
                └── Select category (Cereals, Legumes, Roots & Tubers, etc.)
                    └── Select specific crop
                        └── Confirmation
```

Navigation is available on every screen: `0` goes back one page, `00` returns home.

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

The server runs on `http://localhost:5000`.

**4. Expose it to Africa's Talking (for live testing)**

Africa's Talking needs a public URL to POST to. Use [ngrok](https://ngrok.com/):

```bash
ngrok http 5000
```

Set the callback URL in your Africa's Talking sandbox to `https://<your-ngrok-id>.ngrok.io/ussd`.

## Testing Without the Gateway

Simulate Africa's Talking POST requests with curl:

```bash
# Initial dial-in — show farm list
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=s1&serviceCode=*384*1#&phoneNumber=+254712345678&text="

# Select farm 1, go to advisories
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=s1&serviceCode=*384*1#&phoneNumber=+254712345678&text=1*1"

# Select farm 1, advisory 1, see action steps
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=s1&serviceCode=*384*1#&phoneNumber=+254712345678&text=1*1*1*1"

# Select farm 2, manage crops, add crop, category 5 (Fruits), crop 2 (Mango)
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=s1&serviceCode=*384*1#&phoneNumber=+254712345678&text=2*2*3*5*2"
```

Africa's Talking appends each new user input to the `text` field separated by `*`. The server resolves `0` (back) and `00` (home) by replaying the input path before routing.

## Africa's Talking Callback Fields

| Field | Description |
|---|---|
| `sessionId` | Unique session identifier |
| `serviceCode` | The dialled shortcode (e.g. `*384*1#`) |
| `phoneNumber` | Farmer's phone number in E.164 format |
| `text` | All inputs so far, joined by `*` (empty string on first request) |

Responses must be plain text prefixed with `CON ` (continue session) or `END ` (terminate session).

## Project Context

This POC is part of the **BASED Last-Mile Delivery** engagement between [Blooming World International](https://blwi.org/) and the Twilio Builder Corps × Taproot Foundation volunteer team (June 2026). The goal is to design how BASED's AI-generated farm advisories can reach the ~75% of East African smallholder farmers who have feature phones only — no smartphone, no internet access.

The advisory data in `app.py` is sourced from real BASED engine output for farms in Kiambu and Thika, Kenya.
