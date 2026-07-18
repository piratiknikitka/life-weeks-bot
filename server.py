import os
from datetime import date
from io import BytesIO

from flask import Flask, request, send_file, jsonify, abort

from life_calendar import draw_life_grid, weeks_lived, TOTAL_WEEKS
from sendpulse_client import SendPulseClient

app = Flask(__name__)
sp = SendPulseClient()

# Public base URL of THIS service once deployed, e.g. https://life-weeks-bot.onrender.com
BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")
SUBSCRIBER_TAG = "life_weeks_subscriber"


def parse_dob(day, month, year) -> date:
    return date(int(year), int(month), int(day))


@app.route("/render.png")
def render_png():
    """Renders the grid on the fly. Example: /render.png?dob=1990-05-14"""
    dob_str = request.args.get("dob")
    if not dob_str:
        abort(400, "dob query param required, format YYYY-MM-DD")
    try:
        y, m, d = (int(p) for p in dob_str.split("-"))
        dob = date(y, m, d)
    except Exception:
        abort(400, "invalid dob format, expected YYYY-MM-DD")

    png_bytes = draw_life_grid(dob)
    return send_file(BytesIO(png_bytes), mimetype="image/png")


@app.route("/sendpulse/webhook", methods=["POST"])
def sendpulse_webhook():
    """
    Called by the SendPulse Flow Builder's "Webhook" element right after
    birth_day / birth_month / birth_year variables are collected from the user.
    """
    payload = request.get_json(force=True, silent=True) or {}
    event = payload[0] if isinstance(payload, list) else payload

    contact = event.get("contact", {}) if isinstance(event, dict) else {}
    contact_id = contact.get("id") or event.get("contact_id")
    variables = contact.get("variables", {}) or {}

    day = variables.get("birth_day")
    month = variables.get("birth_month")
    year = variables.get("birth_year")

    if not contact_id or not (day and month and year):
        return jsonify({"status": "ignored", "reason": "missing contact_id or dob parts"}), 200

    try:
        dob = parse_dob(day, month, year)
        if dob > date.today():
            raise ValueError("dob is in the future")
    except Exception:
        sp.send_text(
            contact_id,
            "That date doesn't look valid. Please tell me your birth year, "
            "month and day again (numbers only).",
        )
        return jsonify({"status": "invalid_date"}), 200

    lived = weeks_lived(dob)
    caption = f"Lived {lived} of {TOTAL_WEEKS} weeks."
    photo_url = f"{BASE_URL}/render.png?dob={dob.isoformat()}"

    # persist state on the SendPulse side (no external DB needed)
    sp.set_variable(contact_id, "birth_date_iso", dob.isoformat())
    sp.set_variable(contact_id, "weeks_lived", lived)
    sp.add_tag(contact_id, SUBSCRIBER_TAG)

    sp.send_photo(contact_id, photo_url, caption)

    return jsonify({"status": "ok", "weeks_lived": lived}), 200


@app.route("/health")
def health():
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
