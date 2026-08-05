import asyncio

import httpx

from pluralmind._config import config

BASE_TIME = 1000000000


async def test_get_system_cache(client, monkeypatch, sample_systems, system_api):
    monkeypatch.setattr('time.time', lambda: BASE_TIME)

    # Make the first uncached request
    system = await client.get_system('moonlight')
    assert system['id'] == sample_systems['moonlight']['id']
    assert system_api.calls.call_count == 1

    # Request the same system again (cached)
    system = await client.get_system('moonlight')
    assert system['id'] == sample_systems['moonlight']['id']
    assert system_api.calls.call_count == 1

    # Request another system (uncached)
    system = await client.get_system('retrograde')
    assert system['id'] == sample_systems['retrograde']['id']
    assert system_api.calls.call_count == 2

    # Request a system that doesn't exist (uncached)
    system = await client.get_system('thesystemthatneverwas')
    assert system is None
    assert system_api.calls.call_count == 3

    # Request all the systems again and verify they're all still cached
    monkeypatch.setattr('time.time', lambda: BASE_TIME + config.cache_duration - 1)
    assert (await client.get_system('moonlight'))['id'] == sample_systems['moonlight']['id']
    assert (await client.get_system('retrograde'))['id'] == sample_systems['retrograde']['id']
    assert (await client.get_system('thesystemthatneverwas')) is None
    assert system_api.calls.call_count == 3

    # Time-travel until they'd be expired
    monkeypatch.setattr('time.time', lambda: BASE_TIME + config.cache_duration + 1)
    assert (await client.get_system('moonlight'))['id'] == sample_systems['moonlight']['id']
    assert (await client.get_system('retrograde'))['id'] == sample_systems['retrograde']['id']
    assert (await client.get_system('thesystemthatneverwas')) is None
    assert system_api.calls.call_count == 6


async def test_multiple_concurrent_requests(client, respx_mock, sample_systems):
    # Set up an API that blocks until we release it
    event = asyncio.Event()
    calls = 0

    async def delayed_response(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        await event.wait()
        return httpx.Response(200, json=sample_systems['moonlight'])

    api = respx_mock.get('https://pluralmind.chat/api/v2/system/moonlight').mock(side_effect=delayed_response)

    # Kick off a bunch of requests for the same system
    tasks = [asyncio.create_task(client.get_system('moonlight')) for _ in range(3)]

    # Let the loop run for a bit so all the requests can start
    for _ in range(10):
        await asyncio.sleep(0)

    # Verify that all the requests are pending, but only one call has been made
    assert not any(task.done() for task in tasks)
    assert calls == 1

    # Release the block and verify they all finish
    event.set()
    responses = await asyncio.gather(*tasks)
    assert all(response['id'] == sample_systems['moonlight']['id'] for response in responses)
    assert calls == 1
    assert api.calls.call_count == 1
