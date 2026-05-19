#!/usr/bin/env python3
"""JSON wrapper for ansible-network-triager.

The triager tool outputs prettytable text. This wrapper calls the same
Python API and produces structured JSON for skill consumption.

Usage:
    # Auto-detect triager path (sibling dir, TRIAGER_PATH env, or flag)
    python triager-json.py --bugs
    python triager-json.py --ci

    # Explicit paths
    python triager-json.py --bugs --triager-path /path/to/ansible-network-triager
    python triager-json.py --ci --config /path/to/config.yaml

    # Save output to file
    python triager-json.py --bugs --output triage-data.json

    # Custom lookback period
    python triager-json.py --bugs --days 7
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Default repos to scan if REPO_CONFIG is not set
DEFAULT_REPO_CONFIG = {
    "ansible-collections": {
        "ci_and_bug_repos": [
            "cisco.ios",
            "cisco.iosxr",
            "cisco.nxos",
            "arista.eos",
            "junipernetworks.junos",
            "cisco.asa",
            "ansible.netcommon",
            "ansible.utils",
        ],
        "bug_specific_repos": [
            "community.yang",
        ],
    },
    "redhat-cop": {
        "ci_and_bug_repos": [
            "network.interfaces",
            "network.bgp",
            "network.base",
        ],
    },
}


def find_triager_path(explicit_path=None):
    """Resolve the triager install path.

    Search order:
    1. Explicit --triager-path argument
    2. TRIAGER_PATH environment variable
    3. Sibling directory relative to content-networking-skills repo
    4. ~/ansible-network-triager (common local dev location)
    """
    if explicit_path:
        if os.path.isdir(explicit_path):
            return explicit_path
        print(f"Warning: --triager-path {explicit_path} does not exist", file=sys.stderr)

    # Check env var
    env_path = os.environ.get("TRIAGER_PATH")
    if env_path and os.path.isdir(env_path):
        return env_path

    # Check sibling directory (content-networking-skills/../ansible-network-triager)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # scripts/ -> network-triage-workflow/ -> skills/ -> content-networking-skills/ -> ../
    repo_parent = os.path.normpath(os.path.join(script_dir, "..", "..", "..", ".."))
    sibling = os.path.join(repo_parent, "ansible-network-triager")
    if os.path.isdir(sibling):
        return sibling

    # Check home directory
    home_path = os.path.expanduser("~/ansible-network-triager")
    if os.path.isdir(home_path):
        return home_path

    return None


def ensure_repo_config():
    """Ensure REPO_CONFIG env var is set. Use defaults if not."""
    if not os.environ.get("REPO_CONFIG"):
        os.environ["REPO_CONFIG"] = json.dumps(DEFAULT_REPO_CONFIG)
        print("Using default REPO_CONFIG (network collections)", file=sys.stderr)


def run_bugs(config_path, triager_path, days=None):
    """Run bug triage and return structured JSON."""
    sys.path.insert(0, triager_path)
    ensure_repo_config()

    try:
        from triager.config import Config
        from triager.triager import triage
    except ImportError as e:
        return {
            "error": True,
            "message": f"Cannot import triager modules: {e}",
            "help": "Run: bash skills/network-triage-workflow/scripts/setup.sh",
        }

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv is optional

    config = Config(config_path)

    # Override lookback period if specified
    if days is not None:
        config.config_data["timedelta"] = days

    issues = triage(config, config.bug_repos)

    # Structure the output
    since_days = int(config.config_data.get("timedelta", 14))
    result = {
        "mode": "bugs",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "since_days": since_days,
        "repos": {},
        "summary": {
            "total_items": 0,
            "by_repo": {},
            "by_type": {"Pull Request": 0, "Issue": 0},
        },
    }

    for repo_name, items in issues.items():
        result["repos"][repo_name] = items
        count = len(items)
        result["summary"]["by_repo"][repo_name] = count
        result["summary"]["total_items"] += count
        for item in items:
            item_type = item.get("type", "Issue")
            result["summary"]["by_type"][item_type] = (
                result["summary"]["by_type"].get(item_type, 0) + 1
            )

    return result


def run_ci(config_path, triager_path):
    """Run CI report and return structured JSON."""
    sys.path.insert(0, triager_path)
    ensure_repo_config()

    try:
        from triager.ci_report import generate_ci_report
        from triager.config import Config
    except ImportError as e:
        return {
            "error": True,
            "message": f"Cannot import triager modules: {e}",
            "help": "Run: bash skills/network-triage-workflow/scripts/setup.sh",
        }

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    config = Config(config_path)
    report = generate_ci_report(config)

    if not report:
        return {
            "mode": "ci",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "error": True,
            "message": "No CI report generated — check GITHUB_TOKEN and network",
        }

    result = {
        "mode": "ci",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "overall_status": report.get("overall_status", "Unknown"),
        "repos": [],
        "summary": {
            "total_repos": len(report.get("data", [])),
            "passing": 0,
            "failing": 0,
        },
    }

    for entry in report.get("data", []):
        result["repos"].append(entry)
        if entry.get("status") == "success":
            result["summary"]["passing"] += 1
        else:
            result["summary"]["failing"] += 1

    return result


def main():
    parser = argparse.ArgumentParser(
        description="JSON wrapper for ansible-network-triager",
        epilog="Run setup.sh first if you haven't installed the triager yet.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bugs", action="store_true", help="Run bug scrub (issues and PRs)")
    group.add_argument("--ci", action="store_true", help="Run CI status report")

    parser.add_argument(
        "--triager-path",
        help="Path to ansible-network-triager repo (auto-detected if not set)",
    )
    parser.add_argument(
        "--config", "-c",
        default=None,
        help="Path to config.yaml (defaults to triager repo's config.yaml)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Write JSON output to file instead of stdout",
    )
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=None,
        help="Override lookback period in days (default: 14)",
    )

    args = parser.parse_args()

    triager_path = find_triager_path(args.triager_path)
    if not triager_path:
        error = {
            "error": True,
            "message": "Cannot find ansible-network-triager",
            "help": "Run: bash skills/network-triage-workflow/scripts/setup.sh",
            "search_paths": [
                "TRIAGER_PATH env var",
                "sibling directory to content-networking-skills",
                "~/ansible-network-triager",
            ],
        }
        print(json.dumps(error, indent=2))
        sys.exit(1)

    config_path = args.config or os.path.join(triager_path, "config.yaml")

    if args.bugs:
        result = run_bugs(config_path, triager_path, days=args.days)
    else:
        result = run_ci(config_path, triager_path)

    output = json.dumps(result, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
