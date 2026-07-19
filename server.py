import os
from io import BytesIO

from flask import Flask, request, send_file, abort, jsonify

from life_calendar import draw_life_grid, weeks_lived, TOTAL_WEEKS

app = Flask(__name__)


def _parse_dob_from_request():
    from datetime import date

    dob_str = request.args.get("dob")
    year = request.args.get("year")
    month = request.args.get("month")
    day = request.args.get("day")

    if dob_str:
        y, m, d = (int(p) for p in dob_str.split("-"))
    elif year and month and day:
        y, m, d = int(year), int(month), int(day)
    else:
        abort(400, "Provide either ?dob=YYYY-MM-DD or ?year=&month=&day=")
    return date(y, m, d)


@app.route("/life_stats")
def life_stats():
    """
    Returns plain numbers so the SendPulse flow can show a text message
    BEFORE sending the picture, e.g.:
    /life_stats?dob={{birth_year}}-{{birth_month}}-{{birth_day}}

    Response: {"weeks_lived": 1551, "days_lived": 10857,
               "total_weeks": 4680, "remaining_weeks": 3129}
    """
    try:
        dob = _parse_dob_from_request()
    except Exception:
        abort(400, "Invalid date. Use ?dob=YYYY-MM-DD or ?year=&month=&day=")

    from datetime import date as _date
    lived_weeks = weeks_lived(dob)
    lived_days = (_date.today() - dob).days

    return jsonify({
        "weeks_lived": lived_weeks,
        "days_lived": lived_days,
        "total_weeks": TOTAL_WEEKS,
        "remaining_weeks": TOTAL_WEEKS - lived_weeks,
    })


@app.route("/render.png")
def render_png():
    """
    Renders the life-in-weeks grid on the fly. No storage, no state -
    SendPulse (or a browser) just fetches this URL and gets a PNG back.

    Called directly from the SendPulse flow's Image block, e.g.:
    https://<your-app>.onrender.com/render.png?dob={{birth_year}}-{{birth_month}}-{{birth_day}}

    Also accepts separate year/month/day params if that's more convenient
    to wire up in the flow than building a single "dob" string:
    /render.png?year={{birth_year}}&month={{birth_month}}&day={{birth_day}}
    """
    try:
        dob = _parse_dob_from_request()
    except Exception:
        abort(400, "Invalid date. Use ?dob=YYYY-MM-DD or ?year=&month=&day=")

    png_bytes = draw_life_grid(dob)
    return send_file(BytesIO(png_bytes), mimetype="image/png")


@app.route("/health")
def health():
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
