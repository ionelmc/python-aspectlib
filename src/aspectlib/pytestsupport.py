import pytest
import aspectlib


@pytest.fixture
def weave(request):
    def autocleaned_weave(*args, **kwargs):
        entanglement = aspectlib.weave(*args, **kwargs)
        request.addfinalizer(entanglement.rollback)
        return entanglement

    return autocleaned_weave
