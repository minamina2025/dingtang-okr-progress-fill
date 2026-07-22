# Writeback Safety

Use this reference when the user asks to write progress into Dingteam OKR.

## Required Inputs

- Live OKR JSON from Dingteam for the target period.
- A progress plan JSON with one update per KR:

```json
{
  "title": "Q3 OKR progress",
  "period": "2026年3季度",
  "targetUser": "current user",
  "updates": [
    {
      "krId": "KR id from live OKR",
      "label": "O1 KR1",
      "progress": 20,
      "note": "Paste-ready sanitized progress text.",
      "evidence": [{"summary": "source fact", "url": "permissioned link"}],
      "risk": "remaining gap",
      "nextStep": "next action",
      "confidence": "medium"
    }
  ]
}
```

## Gate

Before writeback, run:

```bash
python3 scripts/okr_progress_toolkit.py validate-plan --plan plan.json --okr live_okr.json
python3 scripts/okr_progress_toolkit.py validate-presentation --plan plan.json
python3 scripts/dingteam_progress_writeback.py --plan plan.json --okr live_okr.json
```

Proceed only when validation passes and the user has approved the exact plan.

## Write Path Order

1. Official or tenant-supported OKR write command, if available.
2. Verified Dingteam Web UI automation in the user's authorized browser/session.
3. Dingteam private API only after the exact payload has been captured from a real same-version UI action and tested on a harmless single KR.

Write one KR at a time. After every update, reload or refetch the KR and verify both progress percentage and note/comment text. If verification fails, stop and report the exact KR that failed.

## Evidence Presentation

Dingteam-visible progress notes must be readable by the user's manager.

- Never leave local screenshot paths in the visible note. Local paths are audit-only.
- For screenshots, paste/upload the sanitized image into the Dingteam rich-text/comment field and verify the image renders.
- For permissioned links, use named rich links instead of raw URLs. The visible text should be a document or evidence name, not a long URL.
- If the API path can update percentages but cannot render images or named links, use verified UI automation for the comment/rich-text evidence section.
- After writing, verify not only that the note text exists, but also that screenshots are visible and links render as named anchors.
