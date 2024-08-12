from pathlib import Path


def pytest_ignore_collect(collection_path: Path, config):
    if 'pytestsupport' in collection_path.__fspath__():
        return True
