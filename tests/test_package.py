from careecon_mania import __version__


def test_version() -> None:
    assert isinstance(__version__, str)
    assert __version__ == "0.1.0"
