"""
Run weekly (see .github/workflows/weekly.yml).
Pulls every subscriber tagged `life_weeks_subscriber`, recalculates their
weeks-lived count and resends a fresh grid image.
"""

import os
from datetime import date

from sendpulse_client import SendPulseClient
from life_calendar import weeks_lived, TOTAL_WEEKS

BASE_URL = os.environ["BASE_URL"]
SUBSCRIBER_TAG = "life_weeks_subscriber"


def main():
    sp = SendPulseClient()
    contacts = sp.get_contacts_by_tag(SUBSCRIBER_TAG)

    # Response shape can vary by API version - handle both a bare list and {"data": [...]}
    items = contacts.get("data", []) if isinstance(contacts, dict) else contacts

    sent, skipped, failed = 0, 0, 0

    for c in items:
        contact_id = c.get("id")
        variables = c.get("variables", {}) or {}
        dob_iso = variables.get("birth_date_iso")

        if not contact_id or not dob_iso:
            skipped += 1
            continue

        try:
            y, m, d = (int(p) for p in dob_iso.split("-"))
            dob = date(y, m, d)
            lived = weeks_lived(dob)
            caption = f"Lived {lived} of {TOTAL_WEEKS} weeks."
            photo_url = f"{BASE_URL}/render.png?dob={dob.isoformat()}"

            sp.send_photo(contact_id, photo_url, caption)
            sp.set_variable(contact_id, "weeks_lived", lived)
            sent += 1
        except Exception as e:
            print(f"[FAILED] contact={contact_id}: {e}")
            failed += 1

    print(f"Done. sent={sent} skipped={skipped} failed={failed}")


if __name__ == "__main__":
    main()
