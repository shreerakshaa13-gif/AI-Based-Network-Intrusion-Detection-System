def test_capture_file_exists():
    from pathlib import Path

    project_root = Path(__file__).resolve().parent.parent

    assert project_root.exists()
    assert (project_root / "capture").exists()
