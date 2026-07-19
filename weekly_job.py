"""
Run weekly (see .github/workflows/weekly.yml).

Pulls every subscriber tagged `life_weeks_subscriber`, recalculates their
weeks-lived count from the birth_year/birth_month/birth_day variables that
SendPulse already stores (collected natively by the flow's "User input"
steps - no custom webhook needed), and resends a fresh grid image.
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

        year = variables.get("birth_year")
        month = variables.get("birth_month")
        day = variables.get("birth_day")

        if not contact_id or not (year and month and day):
            skipped += 1
            continue

        try:
            dob = date(int(year), int(month), int(day))
            lived = weeks_lived(dob)
            lived_days = (date.today() - dob).days
            photo_url = f"{BASE_URL}/render.png?dob={dob.isoformat()}"

            intro_text = (
                f"Week {lived} lived! That's {lived_days} days total.\n"
                f"Here's your updated life calendar:"
            )
            sp.send_text(contact_id, intro_text)
            sp.send_photo(contact_id, photo_url)

            # optional bookkeeping - safe to remove if you don't need it
            try:
                sp.set_variable(contact_id, "weeks_lived", lived)
            except Exception as e:
                print(f"[WARN] could not update weeks_lived for {contact_id}: {e}")

            sent += 1
        except Exception as e:
            print(f"[FAILED] contact={contact_id}: {e}")
            failed += 1

    print(f"Done. sent={sent} skipped={skipped} failed={failed}")


if __name__ == "__main__":
    main()
