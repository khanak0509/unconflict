import pytest

from unconflict import conflict

DIFF3 = """import os
<<<<<<< ours
import sys
||||||| base
=======
import json
>>>>>>> theirs
x = 1
"""

TWO_WAY = "a\n<<<<<<< HEAD\nb\n=======\nc\n>>>>>>> 1234abc\nd\n"


def test_roundtrip_diff3():
    segs = conflict.parse(DIFF3)
    assert conflict.render(segs) == DIFF3
    (h,) = conflict.hunks(segs)
    assert h.ours == ["import sys\n"] and h.base == [] and h.theirs == ["import json\n"]
    assert (h.ours_label, h.base_label, h.theirs_label) == ("ours", "base", "theirs")


def test_roundtrip_two_way_has_no_base():
    segs = conflict.parse(TWO_WAY)
    assert conflict.render(segs) == TWO_WAY
    assert not conflict.all_have_base(segs)
    assert conflict.side(segs, "ours") == "a\nb\nd\n"
    assert conflict.side(segs, "theirs") == "a\nc\nd\n"
    with pytest.raises(ValueError):
        conflict.side(segs, "base")


def test_sides_from_diff3():
    segs = conflict.parse(DIFF3)
    assert conflict.side(segs, "base") == "import os\nx = 1\n"
    assert conflict.side(segs, "theirs") == "import os\nimport json\nx = 1\n"


def test_longer_markers_and_crlf():
    text = "a\r\n<<<<<<<<< L\r\nb\r\n=========\r\nc\r\n>>>>>>>>> R\r\n"
    segs = conflict.parse(text)
    assert conflict.render(segs) == text
    assert conflict.hunks(segs)[0].marker_size == 9


def test_unterminated_conflict_is_an_error():
    with pytest.raises(conflict.ConflictParseError):
        conflict.parse("<<<<<<< a\nx\n=======\ny\n")


def test_no_conflicts():
    assert not conflict.has_conflicts("print(1)\n# ======= not a marker in a comment\n")
