#!/usr/bin/env python3
"""Differential-output oracle for methodfinder behavior-preservation.

Runs a broad battery of ``find(...) == expected`` queries plus direct ``_find``
calls, captures the exact observable output, and writes it to a file. Run it
against the baseline (committed) source, then again against candidate edits; a
byte-identical diff certifies the edits are behavior-preserving on this
interpreter.

Usage (from the repo root, inside the container where methodfinder is
installed):

    python3 tasks/adhoc/study-source-behavior-preserving-recommendations/diff_output.py \
        tasks/adhoc/study-source-behavior-preserving-recommendations/data/baseline.txt

Output is interpreter-version-sensitive (the search enumerates whatever the
running Python exposes), so baseline and candidate MUST run on the same
interpreter (the dev container's Python 3.14).
"""

import contextlib
import io
import sys

import numpy as np

# The package is editable-installed; the underscore helpers live in the submodule.
from methodfinder.methodfinder import _find, find


def capture_find(objects: list[object], expected: object) -> list[str]:
    """Return the exact lines ``find(*objects) == expected`` prints."""
    buffer: io.StringIO = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        find(*objects) == expected  # noqa: B015 -- the == IS the query (DSL)
    return buffer.getvalue().splitlines()


# (objects, expected) battery. Deliberately wide: every sweep, operator,
# value-attribute, __contains__, prefix/infix rendering, the bool-coercion
# block, nested-iterable equality, permutations, and the numpy path.
CASES: list[tuple[list[object], object]] = [
    ([[1, 2, 3]], 6),
    (["1 + 1"], 2),
    ([0.0], 1.0),
    ([0], 1),
    ([1, 1], 1),
    ([1, 2], 3),
    ([3, 2], 1),
    ([3, 2], 1.5),
    ([3, 2], 9),
    ([3, 2], 6),
    ([2, 3], 8),
    ([10, 3], 1),
    ([10, 3], 3),
    ([5], 5),
    ([-5], 5),
    ([5], -5),
    ([-1], 1),
    (["hello"], 5),
    (["hello"], "HELLO"),
    (["HELLO"], "hello"),
    ([[3, 1, 2]], [1, 2, 3]),
    ([[1, 2]], [[1, 2], [2, 1]]),
    ([[1, 2], [3, 4]], [(1, 3), (2, 4)]),
    ([{1, 2}, {2, 3}], {2}),
    ([{1, 2}, {2, 3}], {1, 2, 3}),
    ([[1, 2, 3], 2], True),
    (["abc", "b"], True),
    ([[]], 0),
    ([3.14159, 2], 3.14),
    ([True, True], True),
    ([0, False], True),
    ([np, 3], np.eye(3)),
    (["a", "b"], "ab"),
    ([", ", ["a", "b"]], "a, b"),
]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: diff_output.py <output-file>", file=sys.stderr)
        return 2
    out_path: str = sys.argv[1]
    lines: list[str] = []
    for objects, expected in CASES:
        lines.append(f"### find({objects!r}) == {expected!r}")
        try:
            for match in capture_find(objects, expected):
                lines.append(f"    {match}")
        except Exception as exc:  # noqa: BLE001 -- record, don't abort the battery
            lines.append(f"    <RAISED {type(exc).__name__}: {exc}>")
        # also exercise the un-sugared _find directly (no default-module inject)
        try:
            direct: list[str] = list(_find(objects, expected))
            lines.append(f"    _find -> {direct!r}")
        except Exception as exc:  # noqa: BLE001
            lines.append(f"    _find <RAISED {type(exc).__name__}: {exc}>")
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {len(CASES)} cases to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
