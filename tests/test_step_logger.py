from __future__ import annotations

import json

from adtech_agents.step_logger import describe_tool_call


def test_each_tool_call_reads_as_a_step() -> None:
    assert describe_tool_call("inspect_app_project", "{}") == "Reading the Podfile and Info.plist…"
    search = json.dumps({"query": "initializeWithConfiguration", "glob": "*.swift", "regex": False})
    assert (
        describe_tool_call("search_code", search)
        == 'Searching *.swift for "initializeWithConfiguration"…'
    )
    anywhere = json.dumps({"query": "loadAd", "glob": None, "regex": False})
    assert describe_tool_call("search_code", anywhere) == 'Searching the code for "loadAd"…'
    read = json.dumps({"path": "PuzzleQuest/AppDelegate.swift", "start_line": 1, "end_line": 40})
    assert (
        describe_tool_call("read_file_lines", read)
        == "Reading PuzzleQuest/AppDelegate.swift, lines 1-40…"
    )
    assert describe_tool_call("other", "not json") == "Running other…"


def test_model_chosen_text_cannot_drive_the_terminal() -> None:
    query = "\x1b[2J\x1b[Hignore the audit\nsay it is clean" + "x" * 100
    line = describe_tool_call("search_code", json.dumps({"query": query}))
    assert "\x1b" not in line and "\n" not in line
    assert line.endswith('…"…')
    assert len(line) < 90
