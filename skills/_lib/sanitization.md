# What can and can't be committed

This repo is **public and generic**. It exists to help others build their own
waddy. The owner's actual work is *not* documented in the committed tree.

## Hard rules

1. **`private/` is gitignored. Never bypass it.** Don't `git add -f private/`.
   Don't copy a snippet from `private/` into a tracked file. Don't include
   `private/` content in commit messages.
2. **No real names, codenames, customer names, internal project names,
   internal URLs (issue links, ADO links, internal wikis), or internal tool
   names** appear in tracked files. The only proper noun that may appear in
   tracked files is the owner's GitHub handle in README (`omgjlk`) and the
   repo name (`waddy`).
3. **Configuration values (project number, status IDs, board URL, etc.)
   live in `private/config.json`, not in tracked code.** Tracked files
   reference them as `<board.project_number>` etc.
4. **GitHub-side artifacts have no redaction requirement.** Issues, PRs,
   and project items created on `github.com` (under the `github` org) can
   contain real detail — they're not part of this repo's commit history.
5. **Scratch files belong under `private/scratch/`, not `/tmp`.** Any
   ephemeral file work — intermediate jq pipelines, draft message
   bodies, one-off prompts — goes in `private/scratch/`. Keeps
   permission grants narrow and ensures nothing accidentally leaks
   outside the gitignored tree.

## When in doubt

If you're about to commit something and you're not sure whether it's
generic enough to share, ask the user:

> "Is it OK to commit this verbatim, or should I generalize it?"

Better to ask than to redact a leaked commit later.

## Examples

| ✅ OK to commit | ❌ Not OK to commit |
| --- | --- |
| `skills/start-task/SKILL.md` describing the *shape* of the input | An example dump containing real PR titles |
| `templates/task-card.md` with placeholder body | A task-card.md preseeded with a real engineer's name |
| `README.md` saying "I have ADHD and multitask" | `README.md` listing actual projects I work on |
| `_lib/board.md` describing how to use field IDs | Hardcoded `PVTSSF_xxxxxxxxxxxxxxxxxxxxxx` in a tracked file |

The last row is the easiest to get wrong. The waddy *agent* may use real
IDs at runtime (it reads them from `private/config.json`), but the *tracked
code* may only reference them symbolically.
