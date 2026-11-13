# WorkIQ operational notes

Hard-won details about the `workiq` MCP server. Add to this rather than
rediscovering.

## `fetch_blob` is a generic Microsoft Graph proxy

It is not limited to binary content. Any Graph GET path works, and JSON
responses come back base64-encoded in `base64Content`.

**This matters because the operations fail independently.** Observed
2026-09-10: `ask`, `retrieve`, and `fetch` all returned
`An error occurred invoking '<tool>'` while `search_paths` and `fetch_blob`
worked normally.

When `ask` or `fetch` is down, retry the same Graph path through `fetch_blob`
before concluding the data is unreachable.

Errors surface properly through `fetch_blob` too, with a real `statusCode` and
Graph error `code` and `message`. That is far more debuggable than the opaque
failure the other tools return.

## Path formats that work

Sharing links must be converted to a Graph sharing token, not passed raw:

```bash
python3 -c "import base64,sys;print('u!'+base64.urlsafe_b64encode(sys.argv[1].encode()).decode().rstrip('='))" "<url>"
```

- `/shares/u!<token>/driveItem/content` — file content
- `/drives/{driveId}/items/{itemId}` — drive item metadata as JSON

Passing a raw URL after `/shares/` returns `Access denied for the requested
path`, which reads like a permissions problem but is a format problem.

## Meeting transcripts

`getAllTranscripts` requires the caller to be the organizer:

```
/users/{organizerId}/onlineMeetings/getAllTranscripts(meetingOrganizerUserId='{organizerId}',startDateTime=...,endDateTime=...)
```

Using `/me/` for a meeting someone else organized returns
`BadRequest: The userId must match organizerId`. Take `organizerId` from the
recap link and use it in **both** positions.

**An empty result does not mean there is no meeting content.** Before
concluding anything, try AI insights — see the next section. A meeting can
have no retrievable verbatim transcript and still have full AI-generated
notes and action items.

The recording's drive item exposes
`media.viewpoint.isTranscriptionAllowed`. Do **not** read `false` there as
"no meeting content exists." Observed on 2026-09-10: that flag was `false`,
`getAllTranscripts` returned empty, and AI insights nonetheless returned
five structured notes with twenty subpoints and ten action items. The flag's
exact meaning is unresolved; treat it as a weak signal only.

The recap link carries `driveId`, `driveItemId`, `organizerId`, `threadId` and
`callId` as query parameters. All are usable directly.

## Meeting AI insights (Copilot notes and action items)

This is the highest-yield path for meeting content, and it works when `ask`,
`fetch`, `retrieve`, and `getAllTranscripts` all fail.

Use **your own** user ID, not the organizer's — the opposite of
`getAllTranscripts`:

```
/copilot/users/{yourUserId}/onlineMeetings/{meetingId}/aiInsights
```

`{meetingId}` is the Base64 thread-based meeting ID. Derive it from the
recap link's `organizerId` and `threadId`:

```
MSo{...}  ==  base64("1*<organizerId>*0**<threadId>")
```

The list call returns one entry per occurrence with `id`, `callId`,
`contentCorrelationId`, and `createdDateTime`. Match `callId` against the
recap link's `callId` to select the right occurrence, then fetch it:

```
/copilot/users/{yourUserId}/onlineMeetings/{meetingId}/aiInsights/{insightId}
```

The entity response carries `meetingNotes` (each with `title`, `text`, and
nested `subpoints`), `actionItems` (with `title`, `text`,
`ownerDisplayName`), and sometimes `viewpoint.mentionEvents`.

These are AI paraphrases, not quotes. Say so in any note built from them and
do not present the text as verbatim.

## IRM-protected documents

A `.docx` that downloads as `CDFV2 Encrypted` with `DataSpaces` and
`EncryptedPackage` OLE streams is Purview/IRM protected. The bytes arrive but
cannot be decrypted locally. Fall back to `ask`, or to asking the author.

## Diagnosing a WorkIQ failure: test a known-good path

When a WorkIQ call fails, the error text doesn't distinguish a bad identifier
from a service problem. Both surface as the same opaque message, and a derived
identifier — a base64 meeting id, a sharing token — is the obvious suspect.

Test a path you know worked recently before you debug your own input. If a
previously successful call now fails the same way, the identifier is fine.

Escalate through paths of decreasing complexity until something succeeds:

1. The failing path through `fetch_blob` rather than `fetch`, since the
   operations fail independently.
2. A path that worked earlier in the session.
3. `/me?$select=id,displayName`, which is the cheapest possible authenticated
   read.

When `/me` returns `500`, the backend is down and nothing else is worth trying.
Observed 2026-09-15: `aiInsights`, `getAllTranscripts`, a drive-item metadata
read, and `/me` all returned `statusCode: 500` within two minutes, roughly 80
minutes after the same `aiInsights` path had succeeded.

Save the derived identifiers to `private/scratch/` before you stop. Rebuilding
a meeting id from a recap link is avoidable work, and the recap link may not
still be in the conversation when the service recovers.
