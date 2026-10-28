import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "eval"))

from metrics import locate, normalize_code, region_text, score
from mine import hunk_specs
from run import split_dangling

from unconflict.structured import git_merge

TEXT = "a\nb\nc\nX1\nX2\nd\ne\n"


def test_locate_unique_region():
    r = locate(TEXT, ["b", "c"], ["d", "e"], False, False)
    assert region_text(TEXT, r) == "X1\nX2\n"


def test_locate_ambiguous_or_missing_is_none():
    text = "a\nX\nb\na\nY\nb\n"
    assert locate(text, ["a"], ["b"], False, False) is None
    assert locate(TEXT, ["zz"], ["d"], False, False) is None


def test_locate_file_edges():
    assert region_text(TEXT, locate(TEXT, [], ["c"], True, False)) == "a\nb\n"
    assert region_text(TEXT, locate(TEXT, ["d"], [], False, True)) == "e\n"
    assert locate(TEXT, [], ["c"], False, False) is None


def test_score_order_matches_merge_bench():
    assert score("x = 1\n", "x = 1", "python")["outcome"] == "exact"
    assert score("int  x;", "int x;", "java")["outcome"] == "semantic"
    assert score("x  = 1", "x = 1", "python")["ws"] and not score("x  = 1", "x = 1", "python")["semantic"]
    c = score("<<<<<<< a\nx\n=======\ny\n>>>>>>> b\n", "x\n", "python")
    assert c["outcome"] == "conflict" and c["abstained"]
    assert score("a\n<<<<<<< HEAD\n", "a\n<<<<<<< HEAD", "python")["outcome"] == "exact"


def test_vendored_normalizer():
    assert normalize_code("a = 1  # hi\n", "python") == "a = 1"
    assert normalize_code("int  a; // c\n/* x */", "java") == "int a;"


def test_split_dangling():
    snip = "a\n<<<<<<< H\nb\n=======\nc\n>>>>>>> T\nd\n<<<<<<< H\n\n"
    head, tail = split_dangling(snip)
    assert tail == "<<<<<<< H\n\n" and head.endswith("d\n")
    assert split_dangling("a\n") == ("a\n", "")


def test_hunk_specs_ground_truth():
    base = "p\nq\nr\ns\nt\nKEEP\nu\nv\nw\nx\ny\n"
    ours = base.replace("KEEP", "OURS")
    theirs = base.replace("KEEP", "THEIRS")
    merged = base.replace("KEEP", "OURS_AND_THEIRS")
    (spec,) = hunk_specs(git_merge(base, ours, theirs).text, merged)
    assert spec["gold"] == "OURS_AND_THEIRS\n" and spec["mb_size"]
