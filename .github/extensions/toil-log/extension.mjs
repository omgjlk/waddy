// toil-log: draft weekly "support and toil" log entries from Slack and GitHub activity.
//
// Work-specific settings (repo, Slack user ID, permalink base, categories,
// exclusions, cursor, current issue) live in private/toil/state.json, which is
// gitignored. This file stays generic. The workflow only drafts: it writes a
// markdown draft under private/toil/drafts/ and returns its path. Posting to
// GitHub and advancing the cursor happen in the calling session after the user
// approves the draft. See skills/toil-log/SKILL.md.

import { defineWorkflow, joinSession } from "@github/copilot-sdk/extension";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const REPO_ROOT = fileURLToPath(new URL("../../../", import.meta.url));
const STATE_PATH = join(REPO_ROOT, "private", "toil", "state.json");
const DRAFT_DIR = join(REPO_ROOT, "private", "toil", "drafts");
const WADDY_STATE_PATH = join(REPO_ROOT, "private", "state.json");
const STYLE_PATH = join(REPO_ROOT, "skills", "_lib", "writing-style.md");

const ITEM_SCHEMA = {
    type: "object",
    additionalProperties: false,
    required: ["items", "notes"],
    properties: {
        items: {
            type: "array",
            items: {
                type: "object",
                additionalProperties: false,
                required: ["date", "category", "line", "link", "excluded_reason"],
                properties: {
                    date: { type: "string" },
                    category: { type: "string" },
                    line: { type: "string" },
                    link: { type: "string" },
                    excluded_reason: { type: "string" },
                },
            },
        },
        notes: { type: "string" },
    },
};

const COMPOSE_SCHEMA = {
    type: "object",
    additionalProperties: false,
    required: ["current_additions", "next_items", "dropped", "summary"],
    properties: {
        current_additions: { type: "string" },
        next_items: { type: "string" },
        dropped: {
            type: "array",
            items: {
                type: "object",
                additionalProperties: false,
                required: ["line", "reason"],
                properties: { line: { type: "string" }, reason: { type: "string" } },
            },
        },
        summary: { type: "string" },
    },
};

function localDate(date, timeZone) {
    return new Intl.DateTimeFormat("en-CA", { timeZone, year: "numeric", month: "2-digit", day: "2-digit" }).format(date);
}

function daysInWindow(from, until, timeZone) {
    const days = [];
    for (let t = from.getTime(); t <= until.getTime(); t += 3600 * 1000) {
        const d = localDate(new Date(t), timeZone);
        if (!days.includes(d)) days.push(d);
    }
    return days;
}

function addDays(isoDate, n) {
    const d = new Date(`${isoDate}T12:00:00Z`);
    d.setUTCDate(d.getUTCDate() + n);
    return d.toISOString().slice(0, 10);
}

function itemRules(state) {
    return [
        "Item rules:",
        "- One line per item, past tense, starting with a verb, one sentence, terse.",
        "- Follow Google developer documentation style. No @-mentions; plain names sparingly. Never write \"root cause\".",
        `- Category must be one of: ${state.categories.join("; ")}. Add a new category only if none fit.`,
        `- Slack link format: ${state.slack_permalink_base}/<CHANNEL>/p<message_ts without the dot>?thread_ts=<parent_ts>&cid=<CHANNEL>, pointing at the user's own message.`,
        "- GitHub links are full https://github.com/... URLs.",
        "- Only support and toil: requests from other teams, quota and capacity moves, routing, reviews done as a favor, unblocking.",
        "- Only items with real effort: an investigation, several exchanges, or a concrete action (quota move, PR, review, change in Azure). Drop one-off replies that answer a question, point somewhere, or flag something in a message or two; return them with excluded_reason \"trivial\".",
        `- Exclude: ${state.exclusions.join("; ")}. For anything you find but exclude, still return it with excluded_reason set; leave excluded_reason empty for included items.`,
        "- Read-only: never post, react, or mark anything read. Never write files.",
    ].join("\n");
}

const toilLog = defineWorkflow({
    meta: {
        name: "toil-log",
        description:
            "Draft support-and-toil log entries since the last capture, from the user's Slack messages, GitHub activity, and waddy task touches. " +
            "Writes a draft under private/toil/drafts/ and returns its path; never posts. " +
            "args: { until?: ISO-8601 timestamp (default now), since?: ISO-8601 timestamp (default the cursor in private/toil/state.json) }.",
        phases: [
            { title: "Load", detail: "Read private/toil/state.json and work out the window" },
            { title: "Sweep", detail: "One subagent per day for Slack, one for GitHub" },
            { title: "Compose", detail: "Dedupe against the current issue and draft entries" },
            { title: "Write", detail: "Save the draft under private/toil/drafts/" },
        ],
        argsSchema: {
            type: "object",
            properties: {
                until: { type: "string" },
                since: { type: "string" },
            },
        },
    },
    run: async (ctx) => {
        ctx.phase("Load");
        const args = ctx.args && typeof ctx.args === "object" ? ctx.args : {};
        const state = await ctx.step("state-v1", async () => JSON.parse(await readFile(STATE_PATH, "utf8")));
        const since = new Date(typeof args.since === "string" ? args.since : state.cursor);
        const until = new Date(typeof args.until === "string" ? args.until : new Date().toISOString());
        if (Number.isNaN(since.getTime()) || Number.isNaN(until.getTime()) || since >= until) {
            throw new Error(`Bad window: since=${since.toISOString?.()} until=${until.toISOString?.()}`);
        }
        const days = daysInWindow(since, until, state.timezone);
        const current = state.current_issue;
        const nextStart = current.period_end;
        const nextEnd = addDays(nextStart, state.period_days);
        ctx.log(`Window ${since.toISOString()} to ${until.toISOString()} (${days.length} days: ${days.join(", ")})`);
        ctx.log(`Current issue ${state.repo}#${current.number} covers ${current.period_start} to ${current.period_end}; next period ${nextStart} to ${nextEnd}`);

        const touches = await ctx.step(`touches-${since.toISOString()}-${until.toISOString()}`, async () => {
            let waddy;
            try {
                waddy = JSON.parse(await readFile(WADDY_STATE_PATH, "utf8"));
            } catch {
                return [];
            }
            const out = [];
            for (const [id, task] of Object.entries(waddy.tasks ?? {})) {
                for (const t of task.touches ?? []) {
                    const at = new Date(t.at);
                    if (at >= since && at < until) {
                        out.push({ at: t.at, task: task.title ?? id, note: String(t.note ?? "").slice(0, 400) });
                    }
                }
            }
            return out.sort((a, b) => a.at.localeCompare(b.at));
        });
        ctx.log(`${touches.length} waddy task touches in the window`);

        ctx.phase("Sweep");
        const rules = itemRules(state);
        const sweeps = await ctx.parallel([
            ...days.map((day) => () =>
                ctx.agent(
                    [
                        `Find the Slack support and toil work done by Slack user ${state.slack_user_id} (GitHub handle ${state.user}) on ${day} (${state.timezone}).`,
                        `Only count messages between ${since.toISOString()} and ${until.toISOString()}.`,
                        `Search with the Slack MCP for messages from <@${state.slack_user_id}> on that day across public channels, private channels, and group DMs; page through every result.`,
                        "Read each work thread so you understand what the user actually did, not just what they said. Group a thread into one item even if the user posted several times.",
                        "For 1:1 DMs, don't report content; skip them.",
                        `Set date to ${day}.`,
                        rules,
                    ].join("\n"),
                    { label: `slack:${day}`, schema: ITEM_SCHEMA }
                )
            ),
            () =>
                ctx.agent(
                    [
                        `Find GitHub support and toil work by ${state.user} between ${since.toISOString()} and ${until.toISOString()}.`,
                        "Use github-mcp-server only (never gh, curl, or web_fetch). Look at: pull requests the user opened or merged, pull request reviews the user submitted on other people's PRs, issues the user opened, and substantive issue or PR comments the user wrote.",
                        `Skip the user's own toil-log issues in ${state.repo} and routine weekly status reports.`,
                        "Set date to the local date of the activity.",
                        rules,
                    ].join("\n"),
                    { label: "github", schema: ITEM_SCHEMA }
                ),
        ]);

        const candidates = [];
        const excluded = [];
        sweeps.forEach((s, i) => {
            const source = i < days.length ? `slack:${days[i]}` : "github";
            if (s === null) {
                ctx.log(`Sweep ${source} failed; its items are missing from this draft`);
                return;
            }
            for (const item of s.items ?? []) {
                (item.excluded_reason ? excluded : candidates).push({ ...item, source });
            }
        });
        ctx.log(`${candidates.length} candidate items, ${excluded.length} excluded by the sweeps`);

        ctx.phase("Compose");
        const composed = await ctx.agent(
            [
                `You're drafting additions to a support-and-toil log kept as GitHub issues in ${state.repo}.`,
                `First read the writing style guide at ${STYLE_PATH} and follow it.`,
                `Then read the current issue ${state.repo}#${current.number} (period ${current.period_start} to ${current.period_end}) with github-mcp-server, and the previous one if history lists it: ${JSON.stringify(state.history ?? [])}.`,
                "Drop any candidate already recorded in those issues, unless there was materially new work, in which case describe only the new part.",
                "Merge duplicates across sources into one line. Prefer the Slack thread link; use a PR or review link for GitHub-only work.",
                `Split by date: items dated before ${nextStart} go in current_additions; items dated ${nextStart} or later go in next_items.`,
                "Format both as markdown grouped under italic category headings like *Quota moves and capacity*, one '- ' bullet per item ending with ([thread](URL)), ([PR](URL)), or ([review](URL)). Use only categories that have items. Use an empty string when a group has no items.",
                "Waddy task touches are extra hints: add an item from them only if it is support or toil with a verifiable link, and you found the link.",
                "Put every candidate you didn't use in dropped with a short reason.",
                "summary: two or three sentences on what the window covered and anything uncertain.",
                "",
                "Candidates:",
                JSON.stringify(candidates, null, 1),
                "",
                "Waddy task touches in the window:",
                JSON.stringify(touches, null, 1),
                "",
                rules,
            ].join("\n"),
            { label: "compose", schema: COMPOSE_SCHEMA }
        );
        if (!composed) throw new Error("Compose step returned nothing");

        ctx.phase("Write");
        const stamp = localDate(until, state.timezone);
        const draftPath = join(DRAFT_DIR, `${stamp}.md`);
        await ctx.step(`write-${stamp}-v1`, async () => {
            await mkdir(DRAFT_DIR, { recursive: true });
            const nextTitle = state.title_template.replace("{start}", nextStart).replace("{end}", nextEnd);
            const body = [
                `# Toil log draft, ${since.toISOString()} to ${until.toISOString()}`,
                "",
                `## Additions for ${state.repo}#${current.number} (${current.period_start} to ${current.period_end})`,
                "",
                composed.current_additions || "_None._",
                "",
                `## Next issue: ${nextTitle}`,
                "",
                composed.next_items || "_None._",
                "",
                "## Summary",
                "",
                composed.summary,
                "",
                "## Dropped",
                "",
                ...[...composed.dropped, ...excluded.map((e) => ({ line: e.line, reason: e.excluded_reason }))].map(
                    (d) => `- ${d.line} (${d.reason})`
                ),
                "",
            ].join("\n");
            await writeFile(draftPath, body);
            return true;
        });
        ctx.log(`Draft written to ${draftPath}`);

        return {
            draftPath,
            window: { since: since.toISOString(), until: until.toISOString(), days },
            currentIssue: { repo: state.repo, number: current.number, periodEnd: current.period_end },
            nextPeriod: { start: nextStart, end: nextEnd },
            proposedCursor: until.toISOString(),
            counts: { candidates: candidates.length, excluded: excluded.length, dropped: composed.dropped.length },
            summary: composed.summary,
        };
    },
});

await joinSession({ workflows: [toilLog] });
