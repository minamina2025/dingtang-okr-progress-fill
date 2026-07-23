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

## Screenshot And Link Reliability

Screenshot paste/upload and rich-link insertion can fail silently in Dingteam.
Treat image and link presentation as separate writeback targets, not as part of
plain text verification.

For every screenshot evidence item:

- Keep the local `path` only in the audit JSON.
- Add a human-readable `display` / `label` / `title`.
- Set `pasteIntoDingteam: true` when the plan expects UI paste/upload, or set
  `uploaded` / `dingteamEmbedded` / `attachmentId` only after the image is
  actually uploaded.
- After saving the KR, reopen or refresh the KR and confirm that an image node
  or attachment is visible in the manager-facing rich text. If it is missing,
  retry once with the alternate path: upload button instead of clipboard paste,
  or clipboard paste instead of upload button.
- If the retry still fails, do not claim the screenshot is attached. Write
  `待补内嵌截图` and report the failed KR and evidence label.

For every link evidence item:

- Add a human-readable `display` / `label` / `title`; it must not be a URL.
- Insert the evidence as a rich link/anchor when the editor supports it.
- After saving the KR, reopen or refresh and inspect that the visible title has
  a real `href` or Dingteam link object. Text that merely looks like a title is
  not enough.
- If the editor strips the link, retry once through the editor's link command or
  paste-as-rich-link path.
- If the retry still fails, write `待补可读链接` and report the failed KR and
  evidence label.

Run `validate-presentation` before writeback and again on the post-write
verification artifact. Warnings about unverified screenshot/link presentation
mean the KR still needs visual verification before it can be reported as fully
updated.
