from __future__ import annotations

import ast
from pathlib import Path

LAYER_INDEX = {
    "shared": 0,
    "entities": 1,
    "api": 2,
    "features": 3,
    "runtime": 4,
    "app": 5,
}


def test_layer_dependencies_point_downward() -> None:
    package = Path("src/nique")
    violations: list[str] = []
    for path in package.rglob("*.py"):
        relative = path.relative_to(package)
        source_layer = relative.parts[0]
        if source_layer not in LAYER_INDEX:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.module is None:
                continue
            parts = node.module.split(".")
            if len(parts) < 2 or parts[0] != "nique":
                continue
            target_layer = parts[1]
            points_upward = (
                target_layer in LAYER_INDEX
                and LAYER_INDEX[target_layer] > LAYER_INDEX[source_layer]
            )
            if points_upward:
                violations.append(f"{path}:{node.lineno} imports {target_layer}")
    assert not violations, "\n".join(violations)
