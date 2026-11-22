from __future__ import annotations

import asyncio
import httpx
import pytest

from tikultra import AsyncTikUltra, TikUltra


def _sync_client(seen_paths: list[str]) -> TikUltra:
    def handler(req: httpx.Request) -> httpx.Response:
        seen_paths.append(req.url.raw_path.decode('ascii'))
        return httpx.Response(200, json={'ok': True})

    raw = httpx.Client(base_url='https://api.tikultra.com', transport=httpx.MockTransport(handler))
    return TikUltra(api_key='tu_test_key', http_client=raw)


def _async_client(seen_paths: list[str]) -> AsyncTikUltra:
    def handler(req: httpx.Request) -> httpx.Response:
        seen_paths.append(req.url.raw_path.decode('ascii'))
        return httpx.Response(200, json={'ok': True})

    raw = httpx.AsyncClient(base_url='https://api.tikultra.com', transport=httpx.MockTransport(handler))
    return AsyncTikUltra(api_key='tu_test_key', http_client=raw)


@pytest.mark.parametrize(
    'malicious_id',
    [
        '../admin/keys',
        '../../internal/v1/keys',
        '..',
        '.',
        'ctx_123/../../admin',
        'ctx_123\\..\\admin',
        '',
        '   ',
        'ctx\x00null',
    ],
)
def test_sync_path_traversal_ids_rejected(malicious_id: str) -> None:
    seen: list[str] = []
    client = _sync_client(seen)

    with pytest.raises(ValueError, match='Invalid device_id'):
        client.devices.get(malicious_id)
    with pytest.raises(ValueError, match='Invalid device_id'):
        client.devices.bootstrap(malicious_id)
    with pytest.raises(ValueError, match='Invalid device_id'):
        client.devices.report(malicious_id)
    with pytest.raises(ValueError, match='Invalid device_id'):
        client.devices.warm(malicious_id, niche='gaming')
    with pytest.raises(ValueError, match='Invalid job_id'):
        client.jobs.get(malicious_id)

    assert seen == []


@pytest.mark.parametrize('malicious_id', ['../admin/keys', 'job/../../internal', '', '..'])
def test_async_path_traversal_ids_rejected(malicious_id: str) -> None:
    seen: list[str] = []
    client = _async_client(seen)

    async def _run() -> None:
        with pytest.raises(ValueError, match='Invalid device_id'):
            await client.devices.get(malicious_id)
        with pytest.raises(ValueError, match='Invalid device_id'):
            await client.devices.bootstrap(malicious_id)
        with pytest.raises(ValueError, match='Invalid job_id'):
            await client.jobs.get(malicious_id)

    asyncio.run(_run())
    assert seen == []


def test_special_characters_percent_encoded_in_single_segment() -> None:
    seen: list[str] = []
    client = _sync_client(seen)

    client.devices.get('ctx_123?admin=1#frag')
    client.jobs.get('job 456%2e%2e')

    assert seen == [
        '/v1/devices/ctx_123%3Fadmin%3D1%23frag',
        '/v1/jobs/job%20456%252e%252e',
    ]
