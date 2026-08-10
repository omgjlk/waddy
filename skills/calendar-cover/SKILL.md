---
name: calendar-cover
description: >
  Keep the work (Outlook) calendar honest about personal commitments.
  Pulls the personal (Google) calendar and the work (Outlook via workiq)
  calendar for a window, finds personal commitments during work hours
  that have no matching "busy" block on the work calendar, and — with
  confirmation — creates private "Busy" blocks (and extends partial ones)
  so colleagues don't schedule over personal time. Personal details never
  leave the personal calendar.
---

# calendar-cover

Trigger phrases: "cover my calendar", "block my work calendar for personal
stuff", "add busy blocks", "protect my personal time", "calendar cover",
"sync my personal appointments to work".

## Why this exists

Colleagues schedule against free/busy on the **work** calendar. Personal
appointments live on the **personal** (Google) calendar, invisible to them.
Without a matching "busy" block on work, people book over doctor visits,
family commitments, etc. This skill finds the gaps and (with a confirm step)
fills them with generic, private busy blocks.

## Capability note — this can be fully automated

**workiq can read *and* write the work calendar.** Creating/extending busy
blocks is real, not advisory:
- Read work calendar: `workiq-fetch` on `/me/calendarView?startDateTime=…&endDateTime=…&$select=subject,start,end,showAs,isAllDay,sensitivity`.
- Create a busy block: `workiq-create_entity` `parentUrl=/me/events`.
- Extend/adjust one: `workiq-update_entity` `entityUrl=/me/events/{id}`.

Writes take effect immediately and are visible to colleagues, so **confirm
before creating or editing** (propose-don't-autopilot).

## Input

Optional window (default: **rest of the current work week**, Mon–Fri, through
Friday). Accept "today", "this week", "next week", or an explicit range.

## Steps

1. **Resolve the window** in the user's local timezone (Pacific). Get "now"
   from `google-calendar-get-current-time`.

2. **Pull personal calendar (Google).** `google-calendar-list-events`,
   `calendarId=primary` (or `private/config.json` → `google_calendar.calendar_id`),
   over the window.

   **Filter out non-commitments** — do NOT cover:
   - events the user **declined** (`attendees[self].responseStatus == "declined"`),
   - events marked **free** (`transparency == "transparent"`),
   - all-day informational events unless clearly a commitment.

   **Watch for mis-zoned events.** Google entries sometimes carry a wrong
   `timeZone` (e.g. a noon appointment stored as `12:00 UTC` → shows 5 AM PT).
   If a time looks implausible (pre-dawn appointment, etc.), **flag it and ask**
   rather than covering the wrong slot.

3. **Pull work calendar (Outlook via workiq).** `workiq-fetch` on
   `/me/calendarView` for the same window with
   `$select=subject,start,end,showAs,isAllDay,sensitivity`. Treat an event as
   coverage only when `showAs` is `busy`/`tentative`/`oof` (ignore `free`,
   and ignore `Canceled:`/`Declined:` subjects).

4. **Diff.** For each personal commitment, check whether a work busy block
   **fully contains** its time range.
   - **No overlap** → gap.
   - **Partial overlap** → partial gap; note the exposed sub-range and the
     covering event's id (candidate to *extend* rather than create new).
   - **Fully covered** → skip.

   **Default to work-hours only** (~08:00–17:00 local). List after-hours
   personal items separately as optional (colleagues in other timezones may
   still book late) — don't cover them unless asked.

5. **Propose.** Show a table: personal item · local time · coverage status
   (❌ none / ⚠️ partial / ✅ covered). Group work-hours gaps vs optional
   after-hours. Ask which to create/extend (offer: work-hours gaps only /
   include partial-extends / include after-hours / none).

6. **Write (after confirmation).**
   - **New block** — `workiq-create_entity` `/me/events` with:
     ```json
     {
       "subject": "Busy",
       "showAs": "busy",
       "sensitivity": "private",
       "isReminderOn": false,
       "start": {"dateTime": "YYYY-MM-DDTHH:MM:SS", "timeZone": "Pacific Standard Time"},
       "end":   {"dateTime": "YYYY-MM-DDTHH:MM:SS", "timeZone": "Pacific Standard Time"}
     }
     ```
     Use the windows zone name `"Pacific Standard Time"` with local wall-clock
     times — it is DST-safe (handles PDT automatically). `subject` stays
     generic ("Busy"); never put the personal event's real title/details in it.
   - **Extend a partial cover** — `workiq-update_entity`
     `/me/events/{id}` with just the changed `start`/`end` to span the
     personal item. (You may pass the `@odata.etag` via an `If-Match` header
     from the latest read.)

7. **Report** what was created/extended (time ranges only), and re-list any
   flagged/odd items still needing the user's decision.

## Privacy — hard rules

- Busy blocks on the work calendar carry **no personal details**: subject
  `"Busy"`, `sensitivity: "private"`. Never copy the personal event's title,
  location, attendees, or notes into the work event.
- **Never** write personal-calendar content into any tracked file. If you
  cache a run, it goes under `private/` (e.g. `private/scratch/`), not the repo.
- Surface personal items to the user by **subject + time only** in output.

## Notes / gotchas

- **Confirm before every write** — creates/edits are immediate and visible to
  colleagues.
- **Don't duplicate** — if the user already made a busy block (even a rough
  one), prefer extending it over adding an overlapping second block.
- **Idempotency** — re-running should detect existing "Busy" blocks as
  coverage and not stack duplicates.
- **Declined ≠ attending** — a declined personal invite is not a commitment;
  skip it.
