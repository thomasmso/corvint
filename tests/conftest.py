from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SUITE = Path(__file__).resolve().parent / "evals" / "cases.jsonl"

MakeRepo = Callable[[dict[str, str]], Path]


@pytest.fixture
def make_repo(tmp_path: Path) -> MakeRepo:
    """
    Create a throwaway repository from `{relative_path: content}`.
    """

    def build(files: dict[str, str]) -> Path:
        root = tmp_path / "repo"
        for rel, content in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return root.resolve()

    return build
