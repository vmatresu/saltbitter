#!/usr/bin/env python3
"""
Update agent status with test results from CI
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_junit_xml(xml_path: Path) -> dict:
    """Parse JUnit XML test results."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        total = int(root.attrib.get("tests", 0))
        failures = int(root.attrib.get("failures", 0))
        errors = int(root.attrib.get("errors", 0))
        skipped = int(root.attrib.get("skipped", 0))
        passed = total - failures - errors - skipped

        return {
            "total": total,
            "passed": passed,
            "failed": failures + errors,
            "skipped": skipped,
            "success": failures == 0 and errors == 0
        }
    except Exception as e:
        print(f"Error parsing JUnit XML: {e}", file=sys.stderr)
        return None


def parse_coverage_json(coverage_path: Path) -> float:
    """Parse coverage JSON."""
    try:
        with open(coverage_path) as f:
            data = json.load(f)
            return data.get("totals", {}).get("percent_covered", 0.0)
    except Exception as e:
        print(f"Error parsing coverage JSON: {e}", file=sys.stderr)
        return 0.0


def find_agent_for_branch(branch: str, agents_dir: Path) -> str:
    """Find the agent working on this branch."""
    status_dir = agents_dir / "status"
    if not status_dir.exists():
        return None

    for status_file in status_dir.glob("*.md"):
        with open(status_file) as f:
            content = f.read()
            if f"**Branch**: {branch}" in content:
                return status_file.stem

    return None


def update_agent_status(agent_id: str, test_results: dict, coverage: float, agents_dir: Path):
    """Update agent status file with test results."""
    status_file = agents_dir / "status" / f"{agent_id}.md"
    if not status_file.exists():
        print(f"Status file not found: {status_file}", file=sys.stderr)
        return

    with open(status_file) as f:
        content = f.read()

    # Update test results section
    test_section = f"""
## Test Results (Updated from CI)
- Total tests: {test_results['total']}
- Passed: {test_results['passed']} ✓
- Failed: {test_results['failed']} {'✗' if test_results['failed'] > 0 else ''}
- Skipped: {test_results['skipped']}
- Coverage: {coverage:.1f}%
- Status: {'✅ PASSING' if test_results['success'] else '❌ FAILING'}
"""

    # Replace existing test results section
    if "## Test Results" in content:
        parts = content.split("## Test Results")
        before = parts[0]
        after = parts[1] if len(parts) > 1 else ""
        # Find next section
        next_section_idx = after.find("\n## ")
        if next_section_idx != -1:
            after = after[next_section_idx:]
        else:
            after = ""
        content = before + test_section + after
    else:
        content += "\n" + test_section

    with open(status_file, "w") as f:
        f.write(content)

    print(f"Updated status for agent {agent_id}")


def main():
    parser = argparse.ArgumentParser(description="Update agent status with test results")
    parser.add_argument("--branch", required=True, help="Branch name")
    parser.add_argument("--results", required=True, help="Path to JUnit XML results")
    parser.add_argument("--coverage", help="Path to coverage JSON")
    args = parser.parse_args()

    # Find repo root
    repo_root = Path(__file__).parent.parent.parent
    agents_dir = repo_root / ".agents"

    # Parse test results
    results_path = Path(args.results)
    if not results_path.exists():
        print(f"Results file not found: {results_path}", file=sys.stderr)
        sys.exit(1)

    test_results = parse_junit_xml(results_path)
    if not test_results:
        sys.exit(1)

    # Parse coverage
    coverage = 0.0
    if args.coverage:
        coverage_path = Path(args.coverage)
        if coverage_path.exists():
            coverage = parse_coverage_json(coverage_path)

    # Find agent for this branch
    agent_id = find_agent_for_branch(args.branch, agents_dir)
    if not agent_id:
        print(f"No agent found for branch: {args.branch}", file=sys.stderr)
        sys.exit(0)

    # Update agent status
    update_agent_status(agent_id, test_results, coverage, agents_dir)


if __name__ == "__main__":
    main()
