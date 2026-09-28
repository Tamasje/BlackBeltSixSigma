"""The test oracle inventory/worked_examples.json may not change after the user approved it (tag oracle-approved).

CLAUDE.md: never edit the oracle to make a test pass. This test turns that rule into a failing build.
"""
from __future__ import annotations

import subprocess

from bbtools.constants import ROOT


def test_oracle_approved_tag_exists() -> None:
    # arrange / act
    result = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "-q", "--verify", "refs/tags/oracle-approved"],
                            capture_output=True, text=True)
    # assert -- the tag is set by the user's approval at the inventory-review STOP
    assert result.returncode == 0, "git tag 'oracle-approved' is missing"


def test_worked_examples_unchanged_since_oracle_approved() -> None:
    # arrange / act -- compares the working tree, so uncommitted edits count too
    result = subprocess.run(["git", "-C", str(ROOT), "diff", "oracle-approved", "--", "inventory/worked_examples.json"],
                            capture_output=True, text=True, check=True)
    # assert
    assert result.stdout == "", "inventory/worked_examples.json differs from tag oracle-approved:\n" + result.stdout
