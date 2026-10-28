from unconflict import gate

PY_OURS = "import os\n\ndef a():\n    return 1\n"
PY_THEIRS = "import os\n\ndef b():\n    return 2\n"


def test_clean_merge_passes():
    cand = "import os\n\ndef a():\n    return 1\n\ndef b():\n    return 2\n"
    assert gate.check(cand, PY_OURS, PY_THEIRS, "python").ok


def test_leftover_marker_rejected():
    cand = "import os\n<<<<<<< ours\ndef a():\n    return 1\n"
    r = gate.check(cand, PY_OURS, PY_THEIRS, "python")
    assert not r.ok and r.issues[0].check == "markers"


def test_parse_error_rejected():
    cand = "import os\n\ndef a(:\n    return 1\n"
    r = gate.check(cand, PY_OURS, PY_THEIRS, "python")
    assert not r.ok and any(i.check == "parse" for i in r.issues)


def test_duplicate_function_rejected():
    cand = "import os\n\ndef a():\n    return 1\n\ndef a():\n    return 1\n"
    r = gate.check(cand, PY_OURS, PY_THEIRS, "python")
    assert [i.check for i in r.issues] == ["duplicates"]
    assert r.issues[0].line == 5


def test_duplicate_import_rejected():
    cand = "import os\nimport os\n\ndef a():\n    return 1\n"
    assert not gate.check(cand, PY_OURS, PY_THEIRS, "python").ok


def test_java_overloads_allowed_but_same_signature_rejected():
    ours = "class A {\n  void f(int x) {}\n}\n"
    theirs = "class A {\n  void f(String s) {}\n}\n"
    both = "class A {\n  void f(int x) {}\n  void f(String s) {}\n}\n"
    assert gate.check(both, ours, theirs, "java").ok
    dup = "class A {\n  void f(int x) {}\n  void f(int x) {}\n}\n"
    r = gate.check(dup, ours, theirs, "java")
    assert not r.ok and r.issues[0].check == "duplicates"


def test_js_duplicate_const_rejected():
    ours = "const a = 1;\nexport function f() {}\n"
    theirs = "const a = 2;\nexport function f() {}\n"
    assert gate.check("const a = 2;\nexport function f() {}\n", ours, theirs, "javascript").ok
    assert not gate.check("const a = 1;\nconst a = 2;\nexport function f() {}\n", ours, theirs, "javascript").ok


def test_errors_already_present_in_sides_are_tolerated():
    ours = "    x = 1\n  y = 2\n"
    theirs = "    x = 3\n  y = 2\n"
    assert gate.check("    x = 3\n  y = 2\n", ours, theirs, "python").ok


def test_unknown_language_skips_parse_but_checks_markers():
    r = gate.check("a\n", "a\n", "b\n", None)
    assert r.ok and r.skipped
    assert not gate.check("=======\n", "a\n", "b\n", None).ok


def test_parse_check_skipped_when_sides_dont_parse():
    ours, theirs = "def f(:\n    x = 1\n", "def f(:\n    x = 2\n"
    r = gate.check("def f(:\n    x = (2\n", ours, theirs, "python")
    assert r.ok and any("already have syntax errors" in s for s in r.skipped)
