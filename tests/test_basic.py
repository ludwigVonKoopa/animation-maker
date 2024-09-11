import anim


def test_imports():
    import anim  # noqa: F401


def test_version():
    assert anim.__version__ is not None
