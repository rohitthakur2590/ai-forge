# Network Content

Module provides skills for network automation workflows specific to Ansible network collections.

## When to Use

### Skills

- **network-collection-triage skill**: Use the `network-collection-triage` skill to triage bug reports,
  CI failures, and GitHub issues across Ansible network collections (cisco.ios, cisco.iosxr, cisco.nxos,
  arista.eos, junipernetworks.junos, ansible.netcommon, ansible.utils). Supports two modes: scan mode
  for bulk weekly triage across all repos (generates an HTML dashboard), and direct mode for deep triage
  of a single issue. Invoke when asked to "triage network issues", "scan network issues", "run triager",
  "weekly triage", "triage CI failure", or "triage collection issue".

## Configuration

**Optional Dependencies:**

- `ansible-network-triager` — GitHub issue/PR scanner (installed via `scripts/setup.sh` inside the skill)
- `GITHUB_TOKEN` environment variable — required for GitHub API access

**Required Context:**

- Skills in this module are designed for Ansible network collection development and maintenance
- Network collection development follows standard Ansible collection conventions
- Network collections share common CI failure patterns (Galaxy version lag, cross-collection cascades)

## Notes

- All skills follow Ansible network collection conventions and best practices
- Skills are community-facing and should not contain internal business logic
- See SKILL_GUIDELINES.md for contribution criteria
