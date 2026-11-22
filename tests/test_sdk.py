from __future__ import annotations

import asyncio
import inspect
import json
import pathlib
from typing import Any

import httpx
import pytest

from tikultra import (
    AsyncTikUltra,
    AuthenticationError,
    BadRequestError,
    InsufficientCreditsError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    TikUltra,
    TikUltraError,
    UpstreamError,
)


def _mock_sync_client(
    handler: Any,
    **kwargs: Any,
) -> TikUltra:
    transport = httpx.MockTransport(handler)
    raw_http  = httpx.Client(base_url='https://api.tikultra.com', transport=transport)
    return TikUltra(
        api_key     = 'tu_test_key_123',
        http_client = raw_http,
        **kwargs,
    )


def _mock_async_client(
    handler: Any,
    **kwargs: Any,
) -> AsyncTikUltra:
    transport = httpx.MockTransport(handler)
    raw_http  = httpx.AsyncClient(base_url='https://api.tikultra.com', transport=transport)
    return AsyncTikUltra(
        api_key     = 'tu_test_key_123',
        http_client = raw_http,
        **kwargs,
    )


def test_missing_api_key_raises_auth_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('TIKULTRA_KEY', raising=False)
    monkeypatch.delenv('TIKULTRA_API_KEY', raising=False)
    with pytest.raises(AuthenticationError) as exc_info:
        TikUltra()
    assert exc_info.value.code == 'missing_api_key'
    assert exc_info.value.status_code == 401


def test_env_api_key_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('TIKULTRA_KEY', 'tu_env_secret')
    seen_key = ''

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal seen_key
        seen_key = req.headers.get('x-api-key', '')
        return httpx.Response(200, json={'devices': []})

    transport = httpx.MockTransport(handler)
    raw_http  = httpx.Client(base_url='https://api.tikultra.com', transport=transport)
    client    = TikUltra(http_client=raw_http)
    res       = client.devices.list()
    assert seen_key == 'tu_env_secret'
    assert res['devices'] == []


def test_matrix_defaults_and_per_call_overrides() -> None:
    captured: list[tuple[str, str, dict[str, str], dict[str, Any]]] = []

    def handler(req: httpx.Request) -> httpx.Response:
        body: dict[str, Any] = {}
        if req.content:
            body = json.loads(req.content.decode('utf-8'))
        captured.append((req.method, req.url.path, dict(req.url.params), body))
        return httpx.Response(
            200,
            headers = {
                'x-credits-cost'      : '5',
                'x-credits-charged'   : '5',
                'x-credits-tier'      : 'Standard',
                'x-credits-remaining' : '2495',
                'x-request-id'        : 'req_abc123',
            },
            json    = {'aweme_id': '7705852133855161377', 'status_code': 0},
        )

    client = _mock_sync_client(
        handler,
        os          = 'ios',
        app_flavour = 'pro',
        app_version = '47.5.0',
    )

    res1 = client.video.get('7705852133855161377')
    assert res1['aweme_id'] == '7705852133855161377'
    assert res1.data['aweme_id'] == '7705852133855161377'
    assert res1.credits_cost == 5
    assert res1.credits_remaining == 2495
    assert res1.credits_tier == 'Standard'
    assert res1.request_id == 'req_abc123'

    _, path1, params1, _ = captured[0]
    assert path1 == '/v1/video'
    assert params1['os'] == 'ios'
    assert params1['app_flavour'] == 'pro'
    assert params1['app_version'] == '47.5.0'
    assert 'region' not in params1
    assert 'city' not in params1

    client.tako.ask('Best switches?', os='android', app_flavour='tiktok')
    _, path2, _, body2 = captured[1]
    assert path2 == '/v1/tako/ask'
    assert body2['os'] == 'android'
    assert body2['app_flavour'] == 'tiktok'
    assert body2['app_version'] == '47.5.0'
    assert 'region' not in body2
    assert 'city' not in body2
    assert body2['query'] == 'Best switches?'

    client.devices.list()
    _, path3, params3, _ = captured[2]
    assert path3 == '/v1/devices'
    assert params3 == {}


def test_sync_pagination_and_loop_guard() -> None:
    calls = 0

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        cur = req.url.params.get('cursor')
        if cur is None:
            return httpx.Response(200, json={'items': [{'id': 1}], 'cursor': 'c_page_2', 'has_more': True})
        if cur == 'c_page_2':
            return httpx.Response(200, json={'items': [{'id': 2}], 'cursor': 'c_page_3', 'has_more': True})
        return httpx.Response(200, json={'items': [{'id': 3}], 'cursor': None, 'has_more': False})

    client = _mock_sync_client(handler)
    pages  = list(client.paginate('GET', '/v1/video/comments', params={'aweme_id': '123', 'count': 1}))
    assert len(pages) == 3
    assert [p['items'][0]['id'] for p in pages] == [1, 2, 3]
    assert calls == 3


def test_async_client_and_async_pagination() -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == '/v1/resolve':
            return httpx.Response(200, json={'kind': 'video', 'aweme_id': '7705852133855161377'})
        cur = req.url.params.get('cursor')
        if cur is None:
            return httpx.Response(200, json={'items': ['a'], 'cursor': 'next_1', 'has_more': True})
        return httpx.Response(200, json={'items': ['b'], 'cursor': 'next_1', 'has_more': True})

    async def run() -> None:
        client   = _mock_async_client(handler, os='android', app_flavour='tiktok')
        resolved = await client.resolve('https://vm.tiktok.com/ZMh7Kx2Qp/')
        assert resolved['kind'] == 'video'

        collected: list[str] = []
        async for page in client.paginate('/v1/feed', params={'type': 'foryou'}):
            collected.extend(page['items'])
        # Duplicate cursor 'next_1' halts cleanly instead of looping forever
        assert collected == ['a', 'b']
        await client.aclose()

    asyncio.run(run())


def test_multipart_upload_video_and_slideshow(tmp_path: pathlib.Path) -> None:
    seen_requests: list[tuple[str, str, bytes]] = []

    def handler(req: httpx.Request) -> httpx.Response:
        seen_requests.append((req.url.path, req.headers.get('content-type', ''), req.content))
        return httpx.Response(200, json={'aweme_id': '7705852133855161377', 'status': 'published'})

    mp4_file = tmp_path / 'clip.mp4'
    mp4_file.write_bytes(b'\x00\x00\x00\x18ftypmp42')

    client = _mock_sync_client(handler, os='ios', app_flavour='tiktok')
    res_v  = client.account.upload_video(
        'acc_123',
        file       = mp4_file,
        caption    = 'Launch clip',
        hashtags   = ['tech', 'ai'],
        visibility = 'public',
    )
    assert res_v['status'] == 'published'
    path_v, ctype_v, raw_v = seen_requests[0]
    assert path_v == '/v1/account/upload/video'
    assert 'multipart/form-data' in ctype_v
    assert b'clip.mp4' in raw_v
    assert b'tech,ai' in raw_v

    res_s = client.account.upload_slideshow(
        'acc_123',
        files   = [('slide1.jpg', b'\xff\xd8\xff\xe0img1'), ('slide2.png', b'\x89PNGimg2')],
        caption = 'Carousel',
    )
    assert res_s['status'] == 'published'
    path_s, ctype_s, raw_s = seen_requests[1]
    assert path_s == '/v1/account/upload/slideshow'
    assert 'multipart/form-data' in ctype_s
    assert b'slide1.jpg' in raw_s
    assert b'slide2.png' in raw_s


@pytest.mark.parametrize(
    ('status_code', 'err_cls'),
    [
        (400, BadRequestError),
        (401, AuthenticationError),
        (402, InsufficientCreditsError),
        (403, PermissionDeniedError),
        (404, NotFoundError),
        (429, RateLimitError),
        (502, UpstreamError),
    ],
)
def test_error_mapping_and_zero_cost_on_upstream_failure(
    status_code: int,
    err_cls:     type[Exception],
) -> None:
    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code,
            headers = {
                'x-credits-cost'    : '5',
                'x-credits-charged' : '0',
                'x-request-id'      : 'req_err_99',
                'retry-after'       : '0.01',
            },
            json    = {'error': {'code': f'err_{status_code}', 'message': 'simulated failure'}},
        )

    client = _mock_sync_client(handler, max_retries=0)
    with pytest.raises(err_cls) as exc_info:
        client.video.get('7705852133855161377')

    err = exc_info.value
    assert isinstance(err, TikUltraError)
    assert err.status_code == status_code
    assert err.credits_cost == 0
    assert err.request_id == 'req_err_99'


def test_retry_on_503_recovers() -> None:
    attempts = 0

    def handler(_req: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            return httpx.Response(503, headers={'retry-after': '0.01'}, json={'error': {'code': 'busy', 'message': 'retry'}})
        return httpx.Response(200, json={'ok': True})

    client = _mock_sync_client(handler, max_retries=2)
    res    = client.crypto.sign('https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/?aid=1233')
    assert res['ok'] is True
    assert attempts == 2


def test_decrypt_helpers() -> None:
    seen: list[tuple[str, dict[str, Any]]] = []

    def handler(req: httpx.Request) -> httpx.Response:
        body = json.loads(req.content.decode('utf-8'))
        seen.append((req.url.path, body))
        return httpx.Response(200, json={'ok': True, 'path': req.url.path})

    client = _mock_sync_client(handler, os='android', app_flavour='tiktok')
    r1     = client.crypto.mssdk_decrypt('report', 'AQIDBA==')
    r2     = client.crypto.x_cylons_decrypt('AQIDBA==', query_string='aid=1233')
    assert r1['ok'] is True
    assert r2['ok'] is True
    assert seen[0][0] == '/v1/crypto/mssdk/decrypt'
    assert seen[0][1]['operation'] == 'report'
    assert seen[0][1]['os'] == 'android'
    assert seen[1][0] == '/v1/crypto/x-cylons/decrypt'
    assert seen[1][1]['x_cylons'] == 'AQIDBA=='


def test_smm_lifecycle_and_username_claiming() -> None:
    seen: list[tuple[str, str, dict[str, str], dict[str, Any]]] = []

    def handler(req: httpx.Request) -> httpx.Response:
        body = json.loads(req.content.decode('utf-8')) if req.content else {}
        seen.append((req.method, req.url.path, dict(req.url.params), body))
        return httpx.Response(200, json={'status': 'ok', 'is_available': True})

    client = _mock_sync_client(handler, os='ios')
    client.user.check_username('@nova_hq')
    client.user.bulk_check(['nova_hq', 'nova_labs'])
    client.account.session_warm_reopen('acc_7Hq2')
    client.account.warm_niche('acc_7Hq2', 'b2b saas', duration_sec=45)
    client.account.warm_seed_accounts('acc_7Hq2', ['acme', 'linear'])
    client.account.upload_precheck('acc_7Hq2')
    client.account.claim_username('acc_7Hq2', '@nova_hq')

    assert seen[0][1] == '/v1/user/check-username'
    assert seen[0][2]['unique_id'] == 'nova_hq'
    assert seen[1][1] == '/v1/user/bulk-check'
    assert seen[1][3]['usernames'] == ['nova_hq', 'nova_labs']
    assert seen[2][1] == '/v1/account/session/warm-reopen'
    assert seen[3][1] == '/v1/account/warm/niche'
    assert seen[4][1] == '/v1/account/warm/seed-accounts'
    assert seen[5][1] == '/v1/account/upload/precheck'
    assert seen[6][1] == '/v1/account/profile/username'
    assert seen[6][3]['username'] == 'nova_hq'
    assert seen[6][3]['full_flow'] is True


def test_sync_async_resource_method_and_signature_parity() -> None:
    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={'ok': True})

    sync_client  = _mock_sync_client(handler)
    async_client = _mock_async_client(handler)
    namespaces   = (
        'video',
        'user',
        'feed',
        'search',
        'tako',
        'creator',
        'douyin',
        'shop',
        'live',
        'series',
        'music',
        'hashtag',
        'account',
        'devices',
        'crypto',
        'jobs',
    )
    for ns in namespaces:
        sync_res  = getattr(sync_client, ns)
        async_res = getattr(async_client, ns)
        sync_methods  = {m for m in dir(sync_res) if not m.startswith('_')}
        async_methods = {m for m in dir(async_res) if not m.startswith('_')}
        assert sync_methods == async_methods, f'Method mismatch on {ns}: sync={sync_methods ^ async_methods}'
        for method_name in sorted(sync_methods):
            sync_fn  = getattr(sync_res, method_name)
            async_fn = getattr(async_res, method_name)
            assert inspect.iscoroutinefunction(async_fn), f'AsyncTikUltra.{ns}.{method_name} must be async'
            assert list(inspect.signature(sync_fn).parameters.items()) == list(
                inspect.signature(async_fn).parameters.items()
            ), f'Signature mismatch on {ns}.{method_name}'


def test_jobs_wait_polls_state_until_done() -> None:
    calls = 0

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        state = 'queued' if calls < 2 else 'done'
        return httpx.Response(200, json={'id': 'job_1', 'state': state, 'credits_charged': 4})

    client = _mock_sync_client(handler)
    done   = client.jobs.wait('job_1', poll_interval=0.05, timeout=2.0)
    assert done['state'] == 'done'
    assert calls == 2

    calls = 0

    async def run_async_wait() -> None:
        aclient = _mock_async_client(handler)
        res     = await aclient.jobs.wait('job_1', poll_interval=0.05, timeout=2.0)
        assert res['state'] == 'done'
        await aclient.aclose()

    asyncio.run(run_async_wait())
    assert calls == 2
