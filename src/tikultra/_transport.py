from __future__ import annotations

import asyncio
import os
import pathlib
import time
from typing import Any, BinaryIO, Literal

import httpx

from ._errors import (
    AuthenticationError,
    BadRequestError,
    InsufficientCreditsError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    TikUltraError,
    UpstreamError,
)

OSName     = Literal['android', 'ios']
AppFlavour = Literal[
    'tiktok',
    'tiktok_asia',
    'lite',
    'tiktok_lite',
    'lite_coin',
    'tiktok_lite_go',
    'pro',
    'studio',
    'tiktok_studio',
    'tiktok_business',
    'shop',
    'tikseller',
    'tv',
    'douyin',
]
FileInput  = str | pathlib.Path | bytes | BinaryIO | tuple[str, bytes | BinaryIO] | tuple[str, bytes | BinaryIO, str]

DEFAULT_BASE_URL = 'https://api.tikultra.com'
RETRYABLE_CODES  = frozenset({429, 502, 503, 504})
MATRIX_KEYS      = ('os', 'app_flavour', 'app_version', 'device_id')


class APIResponse(dict[str, Any]):
    status_code:       int
    credits_cost:      int
    credits_tier:      str
    credits_remaining: int | None
    request_id:        str
    headers:           dict[str, str]

    def __init__(
        self,
        payload:           dict[str, Any],
        *,
        status_code:       int            = 200,
        credits_cost:      int            = 0,
        credits_tier:      str            = '',
        credits_remaining: int | None     = None,
        request_id:        str            = '',
        headers:           dict[str, str] | None = None,
    ) -> None:
        super().__init__(payload)
        self.status_code       = status_code
        self.credits_cost      = credits_cost
        self.credits_tier      = credits_tier
        self.credits_remaining = credits_remaining
        self.request_id        = request_id
        self.headers           = headers if headers is not None else {}

    @property
    def data(self) -> dict[str, Any]:
        return dict(self)

    @property
    def cursor(self) -> str | None:
        val = self.get('cursor')
        if val is None or val == '':
            return None
        return str(val)

    @property
    def has_more(self) -> bool:
        val = self.get('has_more')
        return bool(val)


def resolve_api_key(explicit_key: str | None) -> str:
    if explicit_key is not None and explicit_key.strip() != '':
        return explicit_key.strip()
    for env_name in ('TIKULTRA_KEY', 'TIKULTRA_API_KEY'):
        env_val = os.environ.get(env_name, '').strip()
        if env_val != '':
            return env_val
    raise AuthenticationError(
        'Missing TikUltra API key: pass api_key=... or set TIKULTRA_KEY in your environment.',
        status_code = 401,
        code        = 'missing_api_key',
    )


def clean_params(raw: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, val in raw.items():
        if val is None:
            continue
        if isinstance(val, bool):
            out[key] = 'true' if val else 'false'
        elif isinstance(val, (list, tuple)):
            out[key] = ','.join(str(item) for item in val)
        else:
            out[key] = val
    return out


def clean_body(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        key: val
        for key, val in raw.items()
        if val is not None
    }


def prepare_file(field_name: str, item: FileInput) -> tuple[str, tuple[str, bytes | BinaryIO, str]]:
    if isinstance(item, (str, pathlib.Path)):
        path = pathlib.Path(item)
        data = path.read_bytes()
        mime = _guess_mime(path.name)
        return (field_name, (path.name, data, mime))
    if isinstance(item, bytes):
        name = 'upload.mp4' if field_name == 'file' else 'upload.jpg'
        return (field_name, (name, item, _guess_mime(name)))
    if isinstance(item, tuple):
        if len(item) == 2:
            filename, stream = item
            return (field_name, (filename, stream, _guess_mime(filename)))
        if len(item) == 3:
            filename, stream, mime = item
            return (field_name, (filename, stream, mime))
    item_name = item.name if hasattr(item, 'name') and isinstance(item.name, str) else 'upload.bin'
    return (field_name, (os.path.basename(item_name), item, _guess_mime(item_name)))


def _guess_mime(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith('.mp4'):
        return 'video/mp4'
    if lower.endswith('.mov'):
        return 'video/quicktime'
    if lower.endswith(('.jpg', '.jpeg')):
        return 'image/jpeg'
    if lower.endswith('.png'):
        return 'image/png'
    if lower.endswith('.webp'):
        return 'image/webp'
    return 'application/octet-stream'


def _parse_int_header(headers: httpx.Headers, *names: str) -> int | None:
    for name in names:
        raw = headers.get(name)
        if raw is not None and raw.strip().lstrip('-').isdigit():
            return int(raw.strip())
    return None


def parse_response(res: httpx.Response) -> APIResponse:
    hdrs              = {k.lower(): v for k, v in res.headers.items()}
    charged           = _parse_int_header(res.headers, 'x-credits-charged', 'x-credits-cost')
    credits_cost      = charged if charged is not None else 0
    credits_remaining = _parse_int_header(res.headers, 'x-credits-remaining')
    credits_tier      = res.headers.get('x-credits-tier', '')
    request_id        = res.headers.get('x-request-id', '')

    body_dict: dict[str, Any]
    try:
        parsed = res.json()
        if isinstance(parsed, dict):
            body_dict = parsed
        else:
            body_dict = {'data': parsed}
    except ValueError:
        body_dict = {'raw': res.text}

    if 200 <= res.status_code < 300:
        return APIResponse(
            body_dict,
            status_code       = res.status_code,
            credits_cost      = credits_cost,
            credits_tier      = credits_tier,
            credits_remaining = credits_remaining,
            request_id        = request_id,
            headers           = hdrs,
        )

    err_obj = body_dict.get('error')
    if isinstance(err_obj, dict):
        code    = str(err_obj.get('code', f'http_{res.status_code}'))
        message = str(err_obj.get('message', res.reason_phrase))
    else:
        code    = str(body_dict.get('code', f'http_{res.status_code}'))
        message = str(body_dict.get('message', err_obj if isinstance(err_obj, str) else res.text[:240]))

    common = {
        'status_code'  : res.status_code,
        'code'         : code,
        'request_id'   : request_id,
        'credits_cost' : credits_cost,
        'body'         : body_dict,
    }
    if res.status_code in (400, 422):
        raise BadRequestError(message, **common)
    if res.status_code == 401:
        raise AuthenticationError(message, **common)
    if res.status_code == 402:
        raise InsufficientCreditsError(message, **common)
    if res.status_code == 403:
        raise PermissionDeniedError(message, **common)
    if res.status_code == 404:
        raise NotFoundError(message, **common)
    if res.status_code == 429:
        retry_raw   = res.headers.get('retry-after', '')
        retry_after = float(retry_raw) if retry_raw.replace('.', '', 1).isdigit() else None
        raise RateLimitError(message, retry_after=retry_after, **common)
    if res.status_code >= 500:
        raise UpstreamError(message, **common)
    raise TikUltraError(message, **common)


def _retry_delay(attempt: int, res: httpx.Response | None) -> float:
    if res is not None:
        ra = res.headers.get('retry-after', '')
        if ra.replace('.', '', 1).isdigit():
            return min(float(ra), 30.0)
    return min(0.35 * (2 ** attempt), 8.0)


class BaseTransportConfig:
    def __init__(
        self,
        *,
        api_key:     str | None = None,
        base_url:    str        = DEFAULT_BASE_URL,
        timeout:     float      = 30.0,
        max_retries: int        = 2,
        os_name:     OSName | str | None     = None,
        app_flavour: AppFlavour | str | None = None,
        app_version: str | None              = None,
        device_id:   str | None              = None,
    ) -> None:
        self.api_key     = resolve_api_key(api_key)
        self.base_url    = base_url.rstrip('/')
        self.timeout     = timeout
        self.max_retries = max_retries
        self.defaults    = {
            'os'          : os_name,
            'app_flavour' : app_flavour,
            'app_version' : app_version,
            'device_id'   : device_id,
        }

    def merge_matrix(self, target: dict[str, Any], apply_matrix: bool = True) -> dict[str, Any]:
        merged = dict(target)
        if not apply_matrix:
            return merged
        for key in MATRIX_KEYS:
            val = self.defaults.get(key)
            if val is not None and merged.get(key) is None:
                merged[key] = val
        return merged

    def default_headers(self) -> dict[str, str]:
        return {
            'x-api-key'  : self.api_key,
            'accept'     : 'application/json',
            'user-agent' : 'tikultra-python/1.0.0',
        }


class SyncTransport(BaseTransportConfig):
    def __init__(
        self,
        *,
        http_client: httpx.Client | None = None,
        **kwargs:    Any,
    ) -> None:
        super().__init__(**kwargs)
        self._owns_client = http_client is None
        self._client      = http_client if http_client is not None else httpx.Client(
            base_url = self.base_url,
            timeout  = self.timeout,
            headers  = self.default_headers(),
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def request(
        self,
        method:       str,
        path:         str,
        *,
        params:       dict[str, Any] | None = None,
        json_body:    dict[str, Any] | None = None,
        data:         dict[str, Any] | None = None,
        files:        list[tuple[str, tuple[str, bytes | BinaryIO, str]]] | None = None,
        headers:      dict[str, str] | None = None,
        apply_matrix: bool                  = True,
    ) -> APIResponse:
        verb      = method.upper()
        req_hdrs  = self.default_headers()
        if headers is not None:
            req_hdrs.update(headers)

        q_params:  dict[str, Any] | None = None
        body_json: dict[str, Any] | None = None
        form_data: dict[str, Any] | None = None

        if verb == 'GET':
            q_params = clean_params(self.merge_matrix(params if params is not None else {}, apply_matrix))
        else:
            if params is not None:
                q_params = clean_params(params)
            if files is not None:
                merged_form = self.merge_matrix(data if data is not None else {}, apply_matrix)
                form_data   = clean_params(merged_form)
            else:
                merged_json = self.merge_matrix(json_body if json_body is not None else {}, apply_matrix)
                body_json   = clean_body(merged_json)

        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                res = self._client.request(
                    verb,
                    path,
                    params  = q_params,
                    json    = body_json,
                    data    = form_data,
                    files   = files,
                    headers = req_hdrs,
                )
            except httpx.TransportError as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    time.sleep(_retry_delay(attempt, None))
                    continue
                raise UpstreamError(
                    f'Network transport error calling {verb} {path}: {exc}',
                    status_code = 503,
                    code        = 'transport_error',
                ) from exc

            if res.status_code in RETRYABLE_CODES and attempt < self.max_retries:
                time.sleep(_retry_delay(attempt, res))
                continue
            return parse_response(res)

        raise UpstreamError(
            f'Exhausted retries calling {verb} {path}: {last_exc}',
            status_code = 503,
            code        = 'retries_exhausted',
        )


class AsyncTransport(BaseTransportConfig):
    def __init__(
        self,
        *,
        http_client: httpx.AsyncClient | None = None,
        **kwargs:    Any,
    ) -> None:
        super().__init__(**kwargs)
        self._owns_client = http_client is None
        self._client      = http_client if http_client is not None else httpx.AsyncClient(
            base_url = self.base_url,
            timeout  = self.timeout,
            headers  = self.default_headers(),
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def request(
        self,
        method:       str,
        path:         str,
        *,
        params:       dict[str, Any] | None = None,
        json_body:    dict[str, Any] | None = None,
        data:         dict[str, Any] | None = None,
        files:        list[tuple[str, tuple[str, bytes | BinaryIO, str]]] | None = None,
        headers:      dict[str, str] | None = None,
        apply_matrix: bool                  = True,
    ) -> APIResponse:
        verb      = method.upper()
        req_hdrs  = self.default_headers()
        if headers is not None:
            req_hdrs.update(headers)

        q_params:  dict[str, Any] | None = None
        body_json: dict[str, Any] | None = None
        form_data: dict[str, Any] | None = None

        if verb == 'GET':
            q_params = clean_params(self.merge_matrix(params if params is not None else {}, apply_matrix))
        else:
            if params is not None:
                q_params = clean_params(params)
            if files is not None:
                merged_form = self.merge_matrix(data if data is not None else {}, apply_matrix)
                form_data   = clean_params(merged_form)
            else:
                merged_json = self.merge_matrix(json_body if json_body is not None else {}, apply_matrix)
                body_json   = clean_body(merged_json)

        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                res = await self._client.request(
                    verb,
                    path,
                    params  = q_params,
                    json    = body_json,
                    data    = form_data,
                    files   = files,
                    headers = req_hdrs,
                )
            except httpx.TransportError as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    await asyncio.sleep(_retry_delay(attempt, None))
                    continue
                raise UpstreamError(
                    f'Network transport error calling {verb} {path}: {exc}',
                    status_code = 503,
                    code        = 'transport_error',
                ) from exc

            if res.status_code in RETRYABLE_CODES and attempt < self.max_retries:
                await asyncio.sleep(_retry_delay(attempt, res))
                continue
            return parse_response(res)

        raise UpstreamError(
            f'Exhausted retries calling {verb} {path}: {last_exc}',
            status_code = 503,
            code        = 'retries_exhausted',
        )
