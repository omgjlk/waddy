# Datadog operational notes

Hard-won details about Datadog notebooks, the MCP server, and the v1 API. Add to
this rather than rediscovering.

## Never send cell ids when replacing notebook cells

**This is the most expensive lesson in this file.** It corrupted a shared team
notebook three times across two sessions before anyone identified it.

Markdown cell ids are **not stable across reads**. The same cell reports a
different id on each fetch, with no write in between. Graph and table ids are
stable.

So a payload built from an earlier read carries markdown ids that no longer
resolve. On a replace, Datadog does not recognise them and **creates** those
cells rather than replacing them. The originals stay. Every markdown cell
duplicates, and the stable graph and table cells duplicate alongside them.

Strip `id` from every cell before writing:

```python
cells = [{k: v for k, v in c.items() if k != 'id'} for c in cells]
```

The cost is comment marks, which a full replace destroys anyway.

### Why this is easy to miss

The write reports success and the response body echoes the correct cell count.
The duplication appears only in the persisted state, sometimes seconds later.
Both a `200` and a matching response body are consistent with a corrupted write.

### The verification that does not catch it

"All N cell definitions match the intended payload" passes even when the
notebook holds extra cells, because it only proves the intended cells are
present. **Assert the total count**, then assert that no id appears twice:

```python
assert len(cells) == expected
assert len({c['id'] for c in cells}) == len(cells)
```

### What the corruption looks like

Cell count is a multiple-ish of the intended count, plus exact duplicate
id-and-body pairs. Markdown cells may also have their text concatenated onto
themselves, heading first: `## Management` renders twice, then the body repeats,
with the first copy often truncated mid-sentence. Tell-tale fused words appear
at the seams, such as `tileEvaluated` or `excluded.mgmt-cus-01`.

## Metadata-only edits can add empty cells

A name-only `edit_datadog_notebook` call (no `cells`) inserted three empty
markdown cells between graph cells in a small notebook, taking it from 8 cells
to 11. Re-read the notebook after any edit, metadata included, and assert the
cell count.

## `modified` is the field to trust, not `modified_at`

The MCP read exposes `modified_at`, which does **not** advance after a
successful write. The v1 API returns `modified`, which does.

Use `modified` to tell your own write apart from someone else's. Polling it with
no write in flight is the cheapest way to answer "is another process editing
this?" — if it stays frozen at your own write's timestamp, nothing else is
touching the notebook and the problem is yours.

## The MCP tool cannot repair a large notebook safely

`edit_datadog_notebook` takes cells as inline arguments. There is no file upload
and no raw API passthrough; the `_dd_*` tools are marked do-not-call. Replacing
40 cells means reproducing about 40 KB of dense JSON by hand, which is how typos
and truncation get introduced. A truncated argument list is worse than the
corruption being fixed, because a full replace deletes every omitted cell.

Two safer routes:

- **A scoped application key** plus the v1 API, posting a payload file with
  `curl -d @file`. Byte-exact, atomic, no transcription.
- **Incremental build**: one call with `append_only: false` carrying the first
  few cells, then successive `append_only: true` calls. Each call is small
  enough that truncation is not a realistic failure. The first call truncates
  the notebook, so there is a window where it is a stub.

## Credentials

The notebooks API needs an application key; an org API key is also accepted
alongside it. Application keys are user-scoped and can be restricted — use
`notebooks_read` and `notebooks_write` and nothing else.

Pass credentials with `curl --config <file>`, never as `-H` on the command line.
Command-line arguments are visible in the process list to anyone on the machine.

## Metrics query syntax

Datadog accepts the positive `tag IN (a,b,c)` form but **rejects**
`NOT tag IN (a,b,c)` with `Rule 'or_op' didn't match at 'IN (...)'`. Write
exclusions as repeated `NOT tag:value` terms.

## Vega cell defects worth sweeping for

Two patterns are latent in any Vega cell and both produce intermittent, hard to
reproduce failures:

- Validating a cluster's **newest row** rather than its newest *complete* row.
  Source metrics land at different offsets within a minute, so the newest bucket
  is often partial at fetch time and whether it carries every field depends on
  when the browser fetched.
- Comparing `now()` against a data timestamp. Datadog re-renders more often than
  it refetches, so the result tracks render timing rather than data freshness.

## Markdown normalisation on write

Datadog rewrites `*italic*` to `_italic_` and escapes `~` to `\~`. It also compacts Markdown tables: `| a | b |` becomes `| a| b|` and `| --- |` becomes `|-|`. That is
normalisation, not corruption. Compare content with that undone before
concluding a write went wrong.

## Notebook cell live spans are a fixed set

`live_span` accepts only Datadog's fixed spans (for example `1d`, `2d`, `1w`).
The edit tool silently coerces anything else, such as `3d`, to the nearest
supported value and says so only in a note. Read the response before assuming
the span took.

## Appends can add `<br>` spacer cells too

On 2026-09-30 an `append_only` edit of one graph cell to a 4-cell notebook
left 8 cells: a markdown cell containing only `<br>` appeared before every
graph cell after the first. The notebook was open in a browser at the time,
so the UI may be the source. Either way, check the count after every write.

## Allocatable gaps poison headroom formulas

`kubernetes_state.node.cpu_allocatable` drops minutes during heavy deploys, when
kube-state-metrics is busiest. A formula such as `a - (g + o)` then interpolates
across the gap and can produce values tens of thousands of cores wrong. Add
`.fill(last, 900)` to allocatable queries in any headroom formula.

Org-specific Datadog notes live in `private/notes/datadog-internal.md`.

