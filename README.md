# Life-in-Weeks Telegram Bot (SendPulse + Python)

Grid: 90 years (horizontal) x 52 weeks (vertical) = 4680 cells.
Red = lived, white = remaining. Updates automatically every week.

## How it works

- **SendPulse Flow Builder** — only collects the birth date (day/month/year) via chat
  and calls our webhook.
- **Flask server** (`server.py`) — has two jobs:
  - `/render.png?dob=YYYY-MM-DD` renders the grid on the fly (no storage needed at all —
    SendPulse just fetches this URL and forwards the bytes to Telegram).
  - `/sendpulse/webhook` receives the birth date from the Flow, calculates weeks lived,
    saves it back into SendPulse contact variables/tag, and sends the photo.
- **GitHub Actions cron** (`weekly_job.py` + `.github/workflows/weekly.yml`) — once a week,
  pulls every subscriber by tag and resends a fresh image. 100% free, no server needed for this part.

No external database — SendPulse's own contact variables + tags are the only storage.

---

## 1. Create the SendPulse Telegram chatbot

1. In SendPulse: **Chatbots → Create Chatbot → Telegram**, connect it to your Telegram bot
   (get a token from @BotFather first).
2. Go to **Settings → API** and grab your **Client ID / Client Secret** (`SENDPULSE_CLIENT_ID`,
   `SENDPULSE_CLIENT_SECRET`). Also note your **bot_id** (`SENDPULSE_BOT_ID`) — visible in the
   bot's URL/settings inside SendPulse.

## 2. Build the Flow

In **Chatbots → Flows**, create a flow triggered by `/start`:

1. **Send message**: "Hi! Let's build your life calendar. What year were you born? (e.g. 1995)"
   → save reply to variable `birth_year`.
2. **Send message**: "Which month? (1–12)" → save reply to variable `birth_month`.
3. **Send message**: "Which day? (1–31)" → save reply to variable `birth_day`.
4. **Webhook element**: POST to `https://<your-app>.onrender.com/sendpulse/webhook`
   (this sends the contact + variables to our Flask server, which replies with the picture).

You don't need to build the "add tag" or "send photo" steps inside the Flow — the webhook
handler does that via the API, which keeps all logic in one place (easier to change later).

## 3. Deploy the Flask server for free (Render.com)

1. Push this folder to a GitHub repo.
2. On [render.com](https://render.com): **New → Web Service**, connect the repo.
3. Build command: `pip install -r requirements.txt`
   Start command: `gunicorn server:app`
4. Add environment variables in Render's dashboard:
   - `SENDPULSE_CLIENT_ID`
   - `SENDPULSE_CLIENT_SECRET`
   - `SENDPULSE_BOT_ID`
   - `BASE_URL` = the URL Render gives you, e.g. `https://life-weeks-bot.onrender.com`
     (you'll only know it after the first deploy — redeploy once you have it, or set it manually
     in advance if you pick the service name yourself).
5. Deploy. Test: open `https://<your-app>.onrender.com/render.png?dob=1995-03-20` in a browser —
   you should see the grid image.

**Free-tier caveat**: Render's free web services sleep after ~15 min of inactivity and take
~30–60s to wake up on the next request. That's fine for `/render.png` (SendPulse will just wait
a bit longer to fetch the photo) but can cause the *first* `/start` after a long idle period to
feel slow. Alternatives if that's a problem: Fly.io free allowance, or a small always-on VPS.
PythonAnywhere's free tier is not recommended here because its free plan restricts outbound
requests to a domain whitelist, which usually blocks calls to `api.sendpulse.com`.

## 4. Set up the weekly cron (GitHub Actions, free forever)

1. In your GitHub repo: **Settings → Secrets and variables → Actions**, add:
   - `SENDPULSE_CLIENT_ID`, `SENDPULSE_CLIENT_SECRET`, `SENDPULSE_BOT_ID`, `BASE_URL`
2. The workflow in `.github/workflows/weekly.yml` runs every Monday 08:00 UTC automatically,
   and can also be triggered manually from the **Actions** tab (`workflow_dispatch`).
3. It calls `sp.get_contacts_by_tag("life_weeks_subscriber")`, recalculates weeks for each,
   and resends the image.

## 5. Before going live — verify the API shapes

I built this against SendPulse's currently published docs, but double-check these two calls
against your account's live API reference (Settings → API, or
`https://api.sendpulse.com/.well-known/openapi/`) since exact field names occasionally change:

- `sendpulse_client.py :: set_variable()` — the `/telegram/contacts/setVariable` body.
- `sendpulse_client.py :: add_tag()` and `get_contacts_by_tag()` — tag endpoint names/response shape.

If a call fails, print `resp.text` from `requests` to see SendPulse's exact error message and
adjust the field name accordingly — the rest of the code (OAuth, image rendering, `contacts/send`)
doesn't need to change.

## Local testing

```bash
pip install -r requirements.txt
export SENDPULSE_CLIENT_ID=xxx SENDPULSE_CLIENT_SECRET=xxx SENDPULSE_BOT_ID=xxx BASE_URL=http://localhost:5000
python server.py
# open http://localhost:5000/render.png?dob=1995-03-20
```
