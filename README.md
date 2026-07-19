# Life-in-Weeks Telegram Bot (SendPulse + Python)

Grid: 90 years (horizontal) x 52 weeks (vertical) = 4680 cells.
Red = lived, white = remaining. Directional arrows show the fill order
(years left→right, weeks top→bottom). Updates automatically every week.

## How it works

- **SendPulse Flow Builder**:
  - asks for birth year / month / day (native "User input" steps, stored
    automatically as contact variables);
  - tags the contact (native **Add tag** action);
  - calls `/life_stats` (an **API request** element) to fetch the weeks/days
    count as plain numbers, and maps them into flow variables;
  - sends a **Text message** with that count;
  - sends a separate **Image message** with the rendered grid.
- **Flask server** (`server.py`) has two read-only endpoints, both stateless
  (no database, nothing stored — everything is computed on each request):
  - `/render.png?dob=YYYY-MM-DD` → the grid image.
  - `/life_stats?dob=YYYY-MM-DD` → `{"weeks_lived": 1551, "days_lived": 10857,
    "total_weeks": 4680, "remaining_weeks": 3129}`.
- **GitHub Actions cron** (`weekly_job.py`) — once a week, pulls every
  subscriber by tag via the SendPulse API and sends a fresh text + image pair.

---

## 1. Create the SendPulse Telegram chatbot

Same as before: **Chatbots → Create Chatbot → Telegram**, connect your bot
token from @BotFather. Grab **Client ID / Client Secret** and **bot_id**
from **Settings → API** (only needed for the weekly cron job).

## 2. Build the Flow

In **Chatbots → Flows**, build a flow triggered by `/start`:

1. **Message** — "Hi! Let's build your life calendar. What year were you
   born? (e.g. 1995)" → **Wait for subscriber's response**, validate as
   Number, save to variable `birth_year`.
2. **Message** — "Which month? (1–12)" → save to `birth_month`.
3. **Message** — "Which day? (1–31)" → save to `birth_day`.
4. **Action** → **Add tag** → `life_weeks_subscriber`.
5. **API request** element — this is the step that was misconfigured before,
   configure it exactly like this:
   - **Method**: `GET`
   - **URL**:
     ```
     https://<your-app>.onrender.com/life_stats?dob={{birth_year}}-{{birth_month}}-{{birth_day}}
     ```
   - Open the **Save values / Response** tab (name may vary slightly in the
     UI) and map the JSON response fields to new flow variables, e.g.:
     - `weeks_lived` → variable `life_weeks_lived`
     - `days_lived` → variable `life_days_lived`
   - Connect the **Done** output to the next step (below). Leave **Error**
     unconnected for now, or route it to a fallback "Something went wrong,
     try /start again" message.
6. **Message** (text only) — this becomes its own chat bubble, sent
   *before* the picture:
   ```
   Week {{life_weeks_lived}} lived! That's {{life_days_lived}} days total.
   Here's your updated life calendar:
   ```
7. **Message** with an **Image** block — **important**: use the dedicated
   *Image* attachment inside the Message element (usually an image icon /
   "Add attachment" option), **not** a Text block containing the raw URL.
   If you paste the URL into a Text block, Telegram shows it as a clickable
   link with a preview card instead of an actual inline photo — that's
   exactly what happened in your last test. The Image block's URL:
   ```
   https://<your-app>.onrender.com/render.png?dob={{birth_year}}-{{birth_month}}-{{birth_day}}
   ```
8. Save the flow.

Result: two separate bot messages arrive back to back — a short text with
the numbers, then the grid image right below it, no visible link.

## 3. Deploy the Flask server for free (Render.com)

Unchanged from before:

1. Push this folder to your GitHub repo, replacing the old files.
2. On [render.com](https://render.com): **New → Web Service**, connect the repo.
3. Build command: `pip install -r requirements.txt`
   Start command: `gunicorn server:app`
4. No environment variables needed for the server — both endpoints are
   fully self-contained.
5. Test in a browser once deployed:
   - `https://<your-app>.onrender.com/render.png?dob=1995-03-20` → image
   - `https://<your-app>.onrender.com/life_stats?dob=1995-03-20` → JSON

**Free-tier caveat**: Render's free web services sleep after ~15 min of
inactivity (~30–60s wake-up delay on the next request). Fine for occasional
chatbot use; consider Fly.io's free tier or a small always-on VPS if this
becomes annoying.

## 4. Set up the weekly cron (GitHub Actions, free forever)

1. In your GitHub repo: **Settings → Secrets and variables → Actions**, add:
   `SENDPULSE_CLIENT_ID`, `SENDPULSE_CLIENT_SECRET`, `SENDPULSE_BOT_ID`,
   `BASE_URL` (e.g. `https://life-weeks-bot.onrender.com`).
2. `.github/workflows/weekly.yml` runs every Monday 08:00 UTC, or manually
   via the **Actions** tab → **Run workflow**.
3. It reads each subscriber's `birth_year`/`birth_month`/`birth_day`
   variables (already stored by the flow), sends a text message with the
   updated count, then a separate photo message — mirroring steps 6–7 above.

## 5. Double-check before relying on it

- `sendpulse_client.py :: get_contacts_by_tag()` — confirm the response
  actually contains a `variables` object per contact with `birth_year` /
  `birth_month` / `birth_day`. Adjust `weekly_job.py` if the shape differs.
- `send_photo()` / `send_text()` are already confirmed against the current
  `POST /telegram/contacts/send` docs.
- Test the weekly job on demand: repo → **Actions** tab → select the
  workflow → **Run workflow** → check the log output.

## What changed in this version

- Onboarding no longer relies on a webhook/`contact_id` round-trip — the
  flow calls `/life_stats` directly (a **GET** request, properly configured
  this time with a response mapping) purely to get numbers for the text
  message, and `/render.png` directly for the image, exactly like before.
- The grid image now has arrows showing the reading direction (years →,
  weeks ↓) so the layout is self-explanatory.
- Text and image are now sent as two separate messages (both in the flow
  and in the weekly job), matching the "text bubble, then picture below"
  style you wanted — and the image is attached as a real photo instead of
  a plain-text link, which is what was causing the link-preview look.

## Local testing

```bash
pip install -r requirements.txt
python server.py
# http://localhost:5000/render.png?dob=1995-03-20
# http://localhost:5000/life_stats?dob=1995-03-20
```
