from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from types           import TracebackType
from typing          import Any, BinaryIO

import httpx

from ._resources import (
    AccountResource,
    AsyncAccountResource,
    AsyncCreatorResource,
    AsyncCryptoResource,
    AsyncDevicesResource,
    AsyncDouyinResource,
    AsyncFeedResource,
    AsyncHashtagResource,
    AsyncJobsResource,
    AsyncLiveResource,
    AsyncMusicResource,
    AsyncSearchResource,
    AsyncSeriesResource,
    AsyncShopResource,
    AsyncTakoResource,
    AsyncUserResource,
    AsyncVideoResource,
    CreatorResource,
    CryptoResource,
    DevicesResource,
    DouyinResource,
    FeedResource,
    HashtagResource,
    JobsResource,
    LiveResource,
    MusicResource,
    SearchResource,
    SeriesResource,
    ShopResource,
    TakoResource,
    UserResource,
    VideoResource,
)
from ._transport import (
    DEFAULT_BASE_URL,
    APIResponse,
    AppFlavour,
    AsyncTransport,
    OSName,
    SyncTransport,
)


class TikUltra:
    def __init__(
        self,
        api_key:     str | None              = None,
        *,
        base_url:    str                     = DEFAULT_BASE_URL,
        timeout:     float                   = 30.0,
        max_retries: int                     = 2,
        os:          OSName | str | None     = None,
        app_flavour: AppFlavour | str | None = None,
        app_version: str | None              = None,
        device_id:   str | None              = None,
        http_client: httpx.Client | None     = None,
    ) -> None:
        self._transport = SyncTransport(
            api_key     = api_key,
            base_url    = base_url,
            timeout     = timeout,
            max_retries = max_retries,
            os_name     = os,
            app_flavour = app_flavour,
            app_version = app_version,
            device_id   = device_id,
            http_client = http_client,
        )
        self.video   = VideoResource(self._transport)
        self.user    = UserResource(self._transport)
        self.feed    = FeedResource(self._transport)
        self.search  = SearchResource(self._transport)
        self.tako    = TakoResource(self._transport)
        self.creator = CreatorResource(self._transport)
        self.douyin  = DouyinResource(self._transport)
        self.shop    = ShopResource(self._transport)
        self.live    = LiveResource(self._transport)
        self.series  = SeriesResource(self._transport)
        self.music   = MusicResource(self._transport)
        self.hashtag = HashtagResource(self._transport)
        self.account = AccountResource(self._transport)
        self.devices = DevicesResource(self._transport)
        self.crypto  = CryptoResource(self._transport)
        self.jobs    = JobsResource(self._transport)

    def __enter__(self) -> TikUltra:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val:  BaseException | None,
        exc_tb:   TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self._transport.close()

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
        return self._transport.request(
            method,
            path,
            params       = params,
            json_body    = json_body,
            data         = data,
            files        = files,
            headers      = headers,
            apply_matrix = apply_matrix,
        )

    def resolve(self, input_value: str, *, fetch: bool | None = None, **extra: Any) -> APIResponse:
        return self._transport.request('GET', '/v1/resolve', params={'input': input_value, 'fetch': fetch, **extra})

    def id_converter(self, *, id: str | None = None, username: str | None = None) -> APIResponse:
        return self._transport.request('GET', '/v1/id-converter', params={'id': id, 'username': username}, apply_matrix=False)

    def translate(self, text: str, *, target: str = 'en', **extra: Any) -> APIResponse:
        return self._transport.request('GET', '/v1/translate', params={'text': text, 'target': target, **extra})

    def paginate(
        self,
        method_or_path: str,
        path:           str | None            = None,
        *,
        params:         dict[str, Any] | None = None,
        json_body:      dict[str, Any] | None = None,
        max_pages:      int                   = 100,
    ) -> Iterator[APIResponse]:
        if path is None:
            verb   = 'GET'
            target = method_or_path
        else:
            verb   = method_or_path.upper()
            target = path

        cur_params = dict(params) if params is not None else {}
        cur_json   = dict(json_body) if json_body is not None else {}
        seen_cur:  str | None = None

        for _ in range(max_pages):
            page = self._transport.request(
                verb,
                target,
                params    = cur_params if verb == 'GET' else (cur_params if params is not None else None),
                json_body = cur_json if verb != 'GET' else None,
            )
            yield page

            next_cur = page.cursor
            if not page.has_more or next_cur is None or next_cur == seen_cur:
                break
            seen_cur = next_cur
            if verb == 'GET':
                cur_params['cursor'] = next_cur
            else:
                cur_json['cursor'] = next_cur


class AsyncTikUltra:
    def __init__(
        self,
        api_key:     str | None                = None,
        *,
        base_url:    str                       = DEFAULT_BASE_URL,
        timeout:     float                     = 30.0,
        max_retries: int                       = 2,
        os:          OSName | str | None       = None,
        app_flavour: AppFlavour | str | None   = None,
        app_version: str | None                = None,
        device_id:   str | None                = None,
        http_client: httpx.AsyncClient | None  = None,
    ) -> None:
        self._transport = AsyncTransport(
            api_key     = api_key,
            base_url    = base_url,
            timeout     = timeout,
            max_retries = max_retries,
            os_name     = os,
            app_flavour = app_flavour,
            app_version = app_version,
            device_id   = device_id,
            http_client = http_client,
        )
        self.video   = AsyncVideoResource(self._transport)
        self.user    = AsyncUserResource(self._transport)
        self.feed    = AsyncFeedResource(self._transport)
        self.search  = AsyncSearchResource(self._transport)
        self.tako    = AsyncTakoResource(self._transport)
        self.creator = AsyncCreatorResource(self._transport)
        self.douyin  = AsyncDouyinResource(self._transport)
        self.shop    = AsyncShopResource(self._transport)
        self.live    = AsyncLiveResource(self._transport)
        self.series  = AsyncSeriesResource(self._transport)
        self.music   = AsyncMusicResource(self._transport)
        self.hashtag = AsyncHashtagResource(self._transport)
        self.account = AsyncAccountResource(self._transport)
        self.devices = AsyncDevicesResource(self._transport)
        self.crypto  = AsyncCryptoResource(self._transport)
        self.jobs    = AsyncJobsResource(self._transport)

    async def __aenter__(self) -> AsyncTikUltra:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val:  BaseException | None,
        exc_tb:   TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._transport.aclose()

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
        return await self._transport.request(
            method,
            path,
            params       = params,
            json_body    = json_body,
            data         = data,
            files        = files,
            headers      = headers,
            apply_matrix = apply_matrix,
        )

    async def resolve(self, input_value: str, *, fetch: bool | None = None, **extra: Any) -> APIResponse:
        return await self._transport.request('GET', '/v1/resolve', params={'input': input_value, 'fetch': fetch, **extra})

    async def id_converter(self, *, id: str | None = None, username: str | None = None) -> APIResponse:
        return await self._transport.request('GET', '/v1/id-converter', params={'id': id, 'username': username}, apply_matrix=False)

    async def translate(self, text: str, *, target: str = 'en', **extra: Any) -> APIResponse:
        return await self._transport.request('GET', '/v1/translate', params={'text': text, 'target': target, **extra})

    async def paginate(
        self,
        method_or_path: str,
        path:           str | None            = None,
        *,
        params:         dict[str, Any] | None = None,
        json_body:      dict[str, Any] | None = None,
        max_pages:      int                   = 100,
    ) -> AsyncIterator[APIResponse]:
        if path is None:
            verb   = 'GET'
            target = method_or_path
        else:
            verb   = method_or_path.upper()
            target = path

        cur_params = dict(params) if params is not None else {}
        cur_json   = dict(json_body) if json_body is not None else {}
        seen_cur:  str | None = None

        for _ in range(max_pages):
            page = await self._transport.request(
                verb,
                target,
                params    = cur_params if verb == 'GET' else (cur_params if params is not None else None),
                json_body = cur_json if verb != 'GET' else None,
            )
            yield page

            next_cur = page.cursor
            if not page.has_more or next_cur is None or next_cur == seen_cur:
                break
            seen_cur = next_cur
            if verb == 'GET':
                cur_params['cursor'] = next_cur
            else:
                cur_json['cursor'] = next_cur
