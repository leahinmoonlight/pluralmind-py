import pytest

from pluralmind._client import AsyncPluralmindClient

from .fixtures import make_sample_systems


@pytest.fixture
def sample_systems():
    return make_sample_systems()


@pytest.fixture
async def system_api(sample_systems, respx_mock):
    for system_key, system in sample_systems.items():
        respx_mock.get(f'https://pluralmind.chat/api/v2/system/{system_key}').respond(json=system)
        respx_mock.get(f'https://pluralmind.chat/api/v2/system/{system["id"]}').respond(json=system)

    respx_mock.get('https://pluralmind.chat/api/v2/system/thesystemthatneverwas').respond(status_code=404)

    return respx_mock


@pytest.fixture
async def client():
    async with AsyncPluralmindClient() as client:
        yield client
