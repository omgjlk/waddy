---
name: service-ownership
description: >
  "Who owns <service>?" lookup via the Port MCP. Resolves a service /
  artifact / app-role name to its owning team, managers, PM, sponsor,
  support Slack, PagerDuty escalation, repository, and the authoritative
  `ownership.yaml` source. Read-only — Port MCP runs in read-only mode.
---

# service-ownership

Trigger phrases: "who owns …", "ownership of …", "who's responsible for
… service", "who maintains …", "who do I contact for …", "find the team
for …".

## Mental model (READ FIRST — Port's catalog data model)

There is **no `service` blueprint** in this Port instance. A GitHub
Service Catalog "service" is stored in one of these blueprints — check in
this order:

1. **`artifact`** — *the primary one.* "Deployable unit, component, or
   code artifact produced from a repository." The catalog service page in
   the web UI (`.../artifactEntity?identifier=<name>`) is an artifact
   entity. Entity `$identifier` is usually the short service name
   (e.g. `payments`).
2. **`app_role`** — Puppet-configured **datacenter application roles**
   (e.g. `payments-fe`). Use when the target is an app-role / deploy unit
   rather than the top-level service.
3. **`functional_product`** — higher-level product groupings.
4. **`repository`** — falls back to repo-level ownership
   (`github.com/github/<name>`).

`artifact` and `app_role` share nearly identical ownership fields, so the
steps below work for either.

**Tip:** if the user pastes a Port web URL, the blueprint is in the path
segment before `Entity` (e.g. `artifactEntity` → blueprint `artifact`,
`app_roleEntity` → `app_role`) and the entity id is the `identifier=`
query param. Use those directly and skip discovery.

## Steps

1. **Confirm the MCP is available.** If no `port-*` tools are loaded,
   tell the user Port MCP isn't connected and stop. (It's read-only:
   `x-read-only-mode` — never attempt writes.)

2. **Find the entity.** Search the `artifact` blueprint first by
   identifier/title substring:

   ```
   port-list_entities
     blueprintIdentifier="artifact"
     limit=10
     query={"combinator":"or","rules":[
       {"operator":"contains","property":"$identifier","value":"<name>"},
       {"operator":"contains","property":"$title","value":"<name>"}]}
   ```

   - **Exactly one match** → use it.
   - **An exact-id match among several** (e.g. `payments` alongside
     `payments-notifier`, `payments-gateway`) → prefer the exact `$identifier`.
   - **No artifact match** → retry the same query against `app_role`,
     then `repository` (`github.com/github/<name>`), then
     `functional_product`.
   - **Multiple plausible matches and no exact id** → list them and ASK
     which one; don't guess.

3. **Fetch ownership fields.** Re-query with the entity id and an
   `include` list (works for `artifact`; for `app_role` drop the `sev*`
   fields — it doesn't have them):

   ```
   port-list_entities
     blueprintIdentifier="artifact"
     identifiers=["<id>"]
     include=["$title","$team","ownership_source","sponsor",
              "product_manager","owning_team_managers","repository",
              "team_slack_channel_name","support_squad_slack_channel_name",
              "support_doc_link","support_squad_gh_issues_link",
              "pagerduty_escalation"]
   ```

   Ownership lives in:
   - `$team` — Port native owning team (e.g. `<slug>_team`).
   - relation `owning_team_managers` → `_user` — the actual humans.
   - relation `sponsor` → `_user` — exec sponsor.
   - relation `product_manager` → `_user`.
   - relation `pagerduty_escalation` → escalation policy.
   - relation `repository` → the source repo.
   - property `team_slack_channel_name` / `support_squad_*` — contact.
   - property `ownership_source` — **the authoritative
     `github/ownership/.../ownership.yaml`** the rest is synced from.

4. **Output** a compact ownership card:

   ```
   🏔️ Who owns `<service>`

   Owning team        <$team>
   Team manager(s)    <owning_team_managers: Name (email)>
   Product Manager    <product_manager: Name (email)>
   Sponsor            <sponsor: Name (email)>
   Team Slack         #<team_slack_channel_name>
   PagerDuty          <pagerduty_escalation.title>
   Repository         <repository.identifier>

   Source of truth:  <ownership_source.url>
   Support docs:     <support_doc_link.url>
   ```

   Lead with the one-line answer ("**<service> is owned by <team/manager>**,
   PM <name>, sponsor <name> — reach them at #<channel>"), then the card.

## Hard rules

- **Read-only.** Port MCP is `x-read-only-mode`; never call write/action
  tools. This skill only reads.
- **`ownership.yaml` is the system of record.** Port data is synced from
  it — if the user needs to *change* ownership, point them at the
  `ownership_source` file, don't imply Port is editable.
- **Don't fabricate.** If a field is `null` (e.g. no support squad
  channel), say "not set" rather than inventing a contact.
- **Disambiguate, don't guess.** Many entities share a prefix
  (`payments`, `payments-fe`, `payments-notifier`, …). On ambiguity, ask.

## Notes / gotchas

- `port-list_entities` returns only `identifier`+`title` unless you pass
  `include` — always pass `include` in step 3.
- Blueprint discovery: `port-list_blueprints` (no args) lists all; grep
  identifiers for `artifact` / `app_role` / `functional_product` /
  `repository`. There is intentionally no `service` blueprint.
- To inspect available ownership fields on a blueprint, fetch it with
  `port-list_blueprints identifiers=["artifact"]` and read `relations`
  plus `schema.properties`.
