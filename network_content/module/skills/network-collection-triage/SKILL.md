---
name: network-collection-triage
description: >-
  Triage bug reports, CI failures, and GitHub issues for Ansible network
  collections (cisco.ios, cisco.iosxr, cisco.nxos, arista.eos, junos,
  ansible.netcommon, ansible.utils). Two modes: scan mode for bulk weekly
  triage across all repos, and direct mode for deep triage of a single
  issue. Generates a visual HTML dashboard with prioritized actions.
  Use when asked to triage network issues, scan network issues, run
  triager, weekly triage, triage CI failure, or triage collection issue.
  Do not use for non-network collections or general Ansible questions.
---

# Skill: network-collection-triage

## Purpose

Triage bug reports, CI failures, and GitHub issues across Ansible network
collections. Categorize items, check known CI failure patterns, assess
severity with cross-collection cascade detection, and produce actionable
output including an HTML dashboard.

## When to Invoke

TRIGGER when:

- A user asks to triage network collection issues or CI failures
- A user asks to scan repos for unassigned bugs/PRs (scan mode)
- A user pastes a GitHub issue URL or CI failure link for a network collection
- A user asks for a weekly triage dashboard or triage report
- A user says "run triager", "triage network", or "scan network issues"

DO NOT TRIGGER when:

- The issue is in a non-network collection (use generic triage instead)
- The user is asking general Ansible questions unrelated to triage
- The user wants to fix a bug (use bugfix workflow instead)

## Mode Detection

This skill has TWO modes. Detect the mode from the user's trigger and
act accordingly. **Do NOT ask clarifying questions in scan mode.**

### Scan mode (no specific issue provided)

Any trigger that does NOT include a specific GitHub URL or issue number
runs scan mode. This includes: "triage network issues", "triage network",
"scan network issues", "run triager", "weekly triage", "generate triage
dashboard".

**When scan mode is triggered: immediately run the full pipeline end-to-end
without asking the user for any input.** Do NOT stop to ask "What would you
like me to triage?" — the whole point of scan mode is zero-input bulk triage.

### Direct mode (specific issue provided)

A user pastes a GitHub issue URL, CI failure link, error log, or describes
a specific bug symptom. In this mode (and ONLY this mode), ask the user
for additional context if needed (collection, platform, Ansible version).

---

## Setup

Before first use, run the setup script:

```bash
bash scripts/setup.sh
```

This clones the [ansible-network-triager](https://github.com/ansible-network/ansible-network-triager),
installs it, and validates your GitHub token. If the triager is already
installed, the script detects that and skips the install.

**Manual setup** (if you prefer):

1. Clone: `git clone https://github.com/ansible-network/ansible-network-triager.git`
2. Install: `cd ansible-network-triager && pip install -e .`
3. Set token: `export GITHUB_TOKEN="ghp_your_token"`

---

## Collections in Scope

| Collection | Platform | Connection |
|---|---|---|
| `ansible.netcommon` | Shared (connection plugins, base classes) | N/A |
| `ansible.utils` | Shared (utility filters, cli_parse) | N/A |
| `cisco.ios` | Cisco IOS / IOS-XE | network_cli |
| `cisco.iosxr` | Cisco IOS-XR | network_cli, netconf |
| `cisco.nxos` | Cisco NX-OS | network_cli, httpapi |
| `arista.eos` | Arista EOS | network_cli, httpapi |
| `junipernetworks.junos` | Juniper JunOS | network_cli, netconf |
| `cisco.asa` | Cisco ASA | network_cli |
| `vyos.vyos` | VyOS | network_cli |

---

## Scan Mode Pipeline

**Execute all steps automatically without stopping for user input.**

### Step 1 — Run the triager

```bash
python scripts/triager-json.py --bugs
python scripts/triager-json.py --ci
```

If the triager is not found, tell the user to run `setup.sh` and stop.
If `GITHUB_TOKEN` is not set, tell the user and stop.
Otherwise, proceed with the JSON output.

### Step 2 — Categorize every item

| Category | Base Severity | Rationale |
|---|---|---|
| Bug report | **Major** | User-facing issue, needs investigation |
| Downstream fix | **Major** | Upstream breakage actively affecting this collection |
| New feature PR | **Minor** | No urgency unless tied to release deadline |
| Test infrastructure | **Minor** | Strategic work enabling CI reliability |
| Chore / CI / Modernization | **Trivial** | No functional change, auto-merge candidate if CI green |

**Key distinction:** A Molecule/CISSHGO PR building mock-device test
scenarios is test INFRASTRUCTURE (Minor). A Dependabot bump or
pyproject.toml cleanup is a Chore (Trivial).

### Step 3 — Check for known CI failure patterns

Check whether the failure matches a known pattern (e.g. Galaxy version lag
where a dependency fix exists in main but hasn't been released, or
devel/milestone-only failures from ansible-core API changes). If a known
pattern matches, note it in the triage output and use the documented
resolution rather than investigating from scratch.

### Step 4 — Apply severity escalators

Escalators can only raise severity, never lower it.

| Condition | Action |
|---|---|
| Bug in `ansible.netcommon` or `ansible.utils` | **Always Critical** — cascade risk |
| Data loss or security issue | **Critical** |
| Multiple collections failing with same root cause | **Critical** — cascade event |

### Step 5 — Detect cross-collection signals

If the bug is in `ansible.netcommon` or `ansible.utils`:

- List all downstream collections importing the affected code
- Check if their CI is currently failing
- If multiple collections failing → cascade event
- Priority action: fix in netcommon → cut release → re-trigger downstream CI

Dependency chain:

```
ansible.netcommon ──→ cisco.ios, cisco.iosxr, cisco.nxos,
                      arista.eos, junipernetworks.junos,
                      cisco.asa, vyos.vyos
ansible.utils ────→ (same downstream consumers)
```

### Step 6 — Generate the dashboard

Read the template at `templates/triage-dashboard.html`, populate it with
ALL triage results, and save as `triage-report-YYYY-MM-DD.html`. See the
template file for placeholder reference and styling classes.

### Step 7 — Present the dashboard

Share the file link and a brief summary: total items, breakdown by
severity, any critical items or cross-collection signals that need
immediate attention.

---

## Direct Mode Steps

### Step 1 — Identify collection and component

Determine which collection, which module/plugin, and what connection type.

### Step 2 — Check for known CI failure patterns

Check whether the failure matches a known pattern (Galaxy version lag,
devel-only failures, cross-PR dependency issues, etc.). If a known
pattern matches, document it and skip to resolution.

### Step 3 — Cross-collection dependency check

If the bug is in `ansible.netcommon` or `ansible.utils`, check the
dependency chain (same as scan mode Step 5).

### Step 4 — Apply severity escalators

Same table as scan mode Step 4.

### Step 5 — Produce triage report

Use the output format below.

---

## Output Format

Every triage produces this structured report:

```markdown
## Network Collection Triage Report

**Date**: [date]
**Mode**: [Scan / Direct]

### Issue
[GitHub issue URL or CI failure link]

### Collection: [e.g. cisco.ios]
### Component: [module name, plugin, or CI infrastructure]
### Ansible Version: [e.g. stable-2.19 / devel]
### Connection Type: [network_cli / netconf / httpapi]

### Category
[Downstream fix / New feature / Bug report / Chore-CI / Test improvement]

### Severity: [Critical / Major / Minor / Trivial]
[Justification, including any escalators applied]

### Known Pattern Match
[Matched pattern name, OR "No known pattern — new issue"]

### Cross-Collection Impact
[None / List of affected collections / Cascade event detected]

### Root Cause
[Technical explanation if identified]

### Recommended Resolution
[Specific action: cut release, fix in PR #N, add meta: reset_connection, etc.]
```

---

## Dashboard Generation

After scan mode triage, generate a visual HTML dashboard.

1. Read the template: `templates/triage-dashboard.html`
2. Copy the entire file as a starting point
3. Replace `{{ PLACEHOLDER }}` values with real triage data
4. Duplicate commented template blocks for each item, signal, category, and priority action
5. Save as `triage-report-YYYY-MM-DD.html`

The template contains all CSS and JavaScript. Use these CSS classes:

- **Severity**: `sev-critical` (red), `sev-major` (orange), `sev-minor` (green), `sev-trivial` (blue)
- **Type**: `type-pr` (green link), `type-issue` (orange link)
- **Category**: `cat-test`, `cat-feature`, `cat-chore`, `cat-downstream`, `cat-bug`
- **Priority dots**: `dot-red`, `dot-orange`, `dot-yellow`, `dot-green`

Generate for scan mode always. Skip for single direct triage unless requested.

---

## File Structure

```
network-collection-triage/
├── SKILL.md                          ← this file
├── scripts/
│   ├── setup.sh                      ← one-command setup
│   └── triager-json.py               ← JSON wrapper for ansible-network-triager
└── templates/
    └── triage-dashboard.html         ← dashboard template
```
