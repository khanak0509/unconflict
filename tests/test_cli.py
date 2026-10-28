import subprocess

from unconflict import cli, conflict
from unconflict.structured import git_merge

from conftest import load_case, needs_mergiraf


def _conflicted_file(tmp_path, lang, case):
    base, ours, theirs, path = load_case(lang, case)
    text = git_merge(base, ours, theirs).text
    f = tmp_path / path.split("/")[-1]
    f.write_text(text)
    return f, text


@needs_mergiraf
def test_resolve_default_writes_resolved_file_and_keeps_original(tmp_path):
    f, original = _conflicted_file(tmp_path, "java", "structured_clean")
    assert cli.main(["resolve", str(f), "--no-llm", "-q"]) == 0
    assert f.read_text() == original
    out = f.with_name(f.name + ".resolved")
    assert not conflict.has_conflicts(out.read_text())


@needs_mergiraf
def test_resolve_in_place(tmp_path):
    f, _ = _conflicted_file(tmp_path, "python", "structured_clean")
    assert cli.main(["resolve", str(f), "--no-llm", "--in-place", "-q"]) == 0
    assert not conflict.has_conflicts(f.read_text())


def test_resolve_exit_code_1_when_conflicts_remain(tmp_path):
    f, original = _conflicted_file(tmp_path, "python", "llm_needed")
    assert cli.main(["resolve", str(f), "--no-llm", "--no-structured", "-q"]) == 1


@needs_mergiraf
def test_driver_writes_into_ours(tmp_path):
    base, ours, theirs, path = load_case("typescript", "structured_clean")
    for n, c in (("O", base), ("A", ours), ("B", theirs)):
        (tmp_path / n).write_text(c)
    rc = cli.main(["driver", str(tmp_path / "O"), str(tmp_path / "A"), str(tmp_path / "B"), "src/user.ts", "--no-llm"])
    assert rc == 0
    merged = (tmp_path / "A").read_text()
    assert "email: string;" in merged and "age: number;" in merged


def test_driver_conflict_exit_code(tmp_path):
    base, ours, theirs, path = load_case("python", "llm_needed")
    for n, c in (("O", base), ("A", ours), ("B", theirs)):
        (tmp_path / n).write_text(c)
    rc = cli.main(["driver", str(tmp_path / "O"), str(tmp_path / "A"), str(tmp_path / "B"), "g.py",
                   "-x", "HEAD", "-y", "feature", "--no-llm"])
    assert rc == 1
    assert "<<<<<<< HEAD" in (tmp_path / "A").read_text()


@needs_mergiraf
def test_driver_inside_real_git_merge(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git = lambda *a: subprocess.run(["git", *a], cwd=repo, check=True, capture_output=True)
    base, ours, theirs, _ = load_case("java", "structured_clean")
    git("init", "-q", "-b", "main")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "t")
    (repo / "Cart.java").write_text(base)
    (repo / ".gitattributes").write_text("*.java merge=unconflict\n")
    git("add", ".")
    git("commit", "-qm", "base")
    git("checkout", "-qb", "feature")
    (repo / "Cart.java").write_text(theirs)
    git("commit", "-qam", "theirs")
    git("checkout", "-q", "main")
    (repo / "Cart.java").write_text(ours)
    git("commit", "-qam", "ours")
    import sys
    driver = f"{sys.executable} -m unconflict.cli driver %O %A %B %P -s %S -x %X -y %Y --no-llm"
    git("config", "merge.unconflict.driver", driver)
    proc = subprocess.run(["git", "merge", "-q", "--no-edit", "feature"], cwd=repo, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    merged = (repo / "Cart.java").read_text()
    assert "isEmpty()" in merged and "clear()" in merged and "java.util.Set" in merged


def test_install_dry_run(tmp_path, capsys, monkeypatch):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["install", "--dry-run", "--patterns", "*.py"]) == 0
    out = capsys.readouterr().out
    assert "merge.unconflict.driver" in out and "*.py merge=unconflict" in out
    assert not (tmp_path / ".gitattributes").exists()
