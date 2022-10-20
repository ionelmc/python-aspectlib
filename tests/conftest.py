def pytest_ignore_collect(path, config):
    basename = path.basename

    if 'pytestsupport' in basename:
        return True
