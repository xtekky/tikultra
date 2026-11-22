from __future__ import annotations

import asyncio
import time
import urllib.parse
from collections.abc import Sequence
from typing          import Any

from ._errors    import TikUltraError
from ._transport import (
    APIResponse,
    AsyncTransport,
    FileInput,
    SyncTransport,
    prepare_file,
)

_TERMINAL_JOB_STATES = frozenset({'completed', 'succeeded', 'done', 'failed', 'cancelled', 'canceled', 'error'})


def _path_seg(val: str, name: str) -> str:
    s = (val or '').strip()
    if not s or s in ('.', '..') or '/' in s or '\\' in s or '\x00' in s:
        raise ValueError(f'Invalid {name}: must be a single non-empty path segment')
    return urllib.parse.quote(s, safe='')


def _video_target(
    aweme_id: str | None = None,
    url:      str | None = None,
    **extra:  Any,
) -> dict[str, Any]:
    out = dict(extra)
    if aweme_id is not None:
        out['aweme_id'] = aweme_id
    if url is not None:
        out['url'] = url
    return out


def _user_target(
    username: str | None = None,
    sec_uid:  str | None = None,
    uid:      str | None = None,
    url:      str | None = None,
    **extra:  Any,
) -> dict[str, Any]:
    out = dict(extra)
    if username is not None:
        out['username'] = username
    if sec_uid is not None:
        out['sec_uid'] = sec_uid
    if uid is not None:
        out['uid'] = uid
    if url is not None:
        out['url'] = url
    return out


class VideoResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def get(self, aweme_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/video', params=_video_target(aweme_id, url, **extra))

    def batch(self, aweme_ids: Sequence[str], **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/video/batch', json_body={'aweme_ids': list(aweme_ids), **extra})

    def comments(
        self,
        aweme_id:      str | None = None,
        *,
        url:           str | None = None,
        cursor:        str | None = None,
        count:         int | None = None,
        sort_strategy: str | None = None,
        **extra:       Any,
    ) -> APIResponse:
        params = _video_target(aweme_id, url, cursor=cursor, count=count, sort_strategy=sort_strategy, **extra)
        return self._t.request('GET', '/v1/video/comments', params=params)

    def comment_replies(
        self,
        aweme_id:   str,
        comment_id: str,
        *,
        cursor:     str | None = None,
        count:      int | None = None,
        **extra:    Any,
    ) -> APIResponse:
        params = {'aweme_id': aweme_id, 'comment_id': comment_id, 'cursor': cursor, 'count': count, **extra}
        return self._t.request('GET', '/v1/video/comments/replies', params=params)

    def comments_by_ids(self, comment_ids: Sequence[str] | str, **extra: Any) -> APIResponse:
        joined = comment_ids if isinstance(comment_ids, str) else ','.join(comment_ids)
        return self._t.request('GET', '/v1/video/comments/by-ids', params={'comment_ids': joined, **extra})

    def danmaku(
        self,
        aweme_id:      str,
        *,
        start_time_ms: int | None = None,
        end_time_ms:   int | None = None,
        **extra:       Any,
    ) -> APIResponse:
        params = {'aweme_id': aweme_id, 'start_time_ms': start_time_ms, 'end_time_ms': end_time_ms, **extra}
        return self._t.request('GET', '/v1/video/danmaku', params=params)

    def transcript(
        self,
        aweme_id: str | None = None,
        *,
        url:      str | None = None,
        lang:     str | None = None,
        **extra:  Any,
    ) -> APIResponse:
        return self._t.request('GET', '/v1/video/transcript', params=_video_target(aweme_id, url, lang=lang, **extra))

    def no_watermark(self, aweme_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/video/no-watermark', params=_video_target(aweme_id, url, **extra))

    def slideshow(self, aweme_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/video/slideshow', params=_video_target(aweme_id, url, **extra))

    def duets(self, aweme_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/video/duets', params={'aweme_id': aweme_id, 'cursor': cursor, 'count': count, **extra})

    def anchors(self, aweme_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/video/anchors', params={'aweme_id': aweme_id, **extra})

    def upvotes(self, aweme_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/video/upvotes', params={'aweme_id': aweme_id, 'cursor': cursor, 'count': count, **extra})

    def share_info(self, aweme_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/video/share-info', params={'aweme_id': aweme_id, **extra})

    def gifts(self, aweme_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/video/gifts', params={'aweme_id': aweme_id, **extra})

    def forensics(self, aweme_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/video/forensics', params=_video_target(aweme_id, url, **extra))

    def fyp_velocity(self, aweme_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/video/fyp-velocity', params=_video_target(aweme_id, url, **extra))

    def comment_leads(self, aweme_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/video/comment-leads', params=_video_target(aweme_id, url, **extra))


class UserResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def profile(
        self,
        username: str | None = None,
        *,
        sec_uid:  str | None = None,
        uid:      str | None = None,
        url:      str | None = None,
        **extra:  Any,
    ) -> APIResponse:
        return self._t.request('GET', '/v1/user', params=_user_target(username, sec_uid, uid, url, **extra))

    get = profile

    def posts(
        self,
        username: str | None = None,
        *,
        sec_uid:  str | None = None,
        cursor:   str | None = None,
        count:    int | None = None,
        sort:     str | None = None,
        **extra:  Any,
    ) -> APIResponse:
        params = _user_target(username, sec_uid, cursor=cursor, count=count, sort=sort, **extra)
        return self._t.request('GET', '/v1/user/posts', params=params)

    def with_posts(self, username: str | None = None, *, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/user/with-posts', params=_user_target(username, sec_uid, **extra))

    def stories(
        self,
        username: str | None = None,
        *,
        sec_uid:  str | None = None,
        uid:      str | None = None,
        cursor:   str | None = None,
        count:    int | None = None,
        **extra:  Any,
    ) -> APIResponse:
        return self._t.request('GET', '/v1/user/stories', params=_user_target(username, sec_uid, uid, cursor=cursor, count=count, **extra))

    def stories_batch(self, usernames: Sequence[str], **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/user/stories/batch', json_body={'usernames': list(usernames), **extra})

    def reposts(
        self,
        username: str | None = None,
        *,
        sec_uid:  str | None = None,
        cursor:   str | None = None,
        count:    int | None = None,
        **extra:  Any,
    ) -> APIResponse:
        return self._t.request('GET', '/v1/user/reposts', params=_user_target(username, sec_uid, cursor=cursor, count=count, **extra))

    def favorites(
        self,
        username: str | None = None,
        *,
        sec_uid:  str | None = None,
        cursor:   str | None = None,
        count:    int | None = None,
        **extra:  Any,
    ) -> APIResponse:
        return self._t.request('GET', '/v1/user/favorites', params=_user_target(username, sec_uid, cursor=cursor, count=count, **extra))

    def playlists(
        self,
        username: str | None = None,
        *,
        sec_uid:  str | None = None,
        cursor:   str | None = None,
        count:    int | None = None,
        **extra:  Any,
    ) -> APIResponse:
        return self._t.request('GET', '/v1/user/playlists', params=_user_target(username, sec_uid, cursor=cursor, count=count, **extra))

    def followers(
        self,
        username: str | None = None,
        *,
        sec_uid:  str | None = None,
        cursor:   str | None = None,
        count:    int | None = None,
        **extra:  Any,
    ) -> APIResponse:
        return self._t.request('GET', '/v1/user/followers', params=_user_target(username, sec_uid, cursor=cursor, count=count, **extra))

    def followings(
        self,
        username: str | None = None,
        *,
        sec_uid:  str | None = None,
        cursor:   str | None = None,
        count:    int | None = None,
        **extra:  Any,
    ) -> APIResponse:
        return self._t.request('GET', '/v1/user/followings', params=_user_target(username, sec_uid, cursor=cursor, count=count, **extra))

    def followers_search(self, keyword: str, *, username: str | None = None, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/user/followers/search', params=_user_target(username, sec_uid, keyword=keyword, **extra))

    def followings_search(self, keyword: str, *, username: str | None = None, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/user/followings/search', params=_user_target(username, sec_uid, keyword=keyword, **extra))

    def similar(self, username: str | None = None, *, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/user/similar', params=_user_target(username, sec_uid, **extra))

    def collections(
        self,
        username: str | None = None,
        *,
        sec_uid:  str | None = None,
        cursor:   str | None = None,
        count:    int | None = None,
        **extra:  Any,
    ) -> APIResponse:
        return self._t.request('GET', '/v1/user/collections', params=_user_target(username, sec_uid, cursor=cursor, count=count, **extra))

    def collection_videos(self, collection_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/user/collections/videos', params={'collection_id': collection_id, 'cursor': cursor, 'count': count, **extra})

    def locate_post(self, aweme_id: str, *, username: str | None = None, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/user/locate-post', params=_user_target(username, sec_uid, aweme_id=aweme_id, **extra))

    def series(self, username: str | None = None, *, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/user/series', params=_user_target(username, sec_uid, **extra))

    def audit(self, username: str | None = None, *, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/user/audit', params=_user_target(username, sec_uid, **extra))

    def visibility(self, username: str | None = None, *, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/user/visibility', params=_user_target(username, sec_uid, **extra))

    def compare(self, usernames: Sequence[str] | str, **extra: Any) -> APIResponse:
        joined = usernames if isinstance(usernames, str) else ','.join(usernames)
        return self._t.request('GET', '/v1/user/compare', params={'usernames': joined, **extra})

    def check_username(self, unique_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/user/check-username', params={'unique_id': unique_id.lstrip('@'), **extra})

    def bulk_check(self, usernames: Sequence[str], **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/user/bulk-check', json_body={'usernames': list(usernames), **extra})


class FeedResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def get(
        self,
        feed_type: str        = 'foryou',
        *,
        cursor:    str | None = None,
        count:     int | None = None,
        **extra:   Any,
    ) -> APIResponse:
        return self._t.request('GET', '/v1/feed', params={'type': feed_type, 'cursor': cursor, 'count': count, **extra})

    def fyp(self, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self.get('foryou', cursor=cursor, count=count, **extra)

    def persona_fyp(
        self,
        niche:   str | None = None,
        *,
        region:  str | None = None,
        city:    str | None = None,
        cursor:  str | None = None,
        count:   int | None = None,
        **extra: Any,
    ) -> APIResponse:
        params = {'niche': niche, 'region': region, 'city': city, 'cursor': cursor, 'count': count, **extra}
        return self._t.request('GET', '/v1/feed/persona-fyp', params=params)

    def persona_cities(self, *, region: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/feed/persona-fyp/cities', params={'region': region, **extra}, apply_matrix=False)

    def stories(self, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/feed/stories', params=extra)

    def landscape(self, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/feed/landscape', params={'cursor': cursor, 'count': count, **extra})


class SearchResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def query(
        self,
        keyword:      str,
        *,
        search_type:  str        = 'videos',
        sort_type:    str | None = None,
        publish_time: str | None = None,
        cursor:       str | None = None,
        count:        int | None = None,
        **extra:      Any,
    ) -> APIResponse:
        params = {
            'keyword'      : keyword,
            'type'         : search_type,
            'sort_type'    : sort_type,
            'publish_time' : publish_time,
            'cursor'       : cursor,
            'count'        : count,
            **extra,
        }
        return self._t.request('GET', '/v1/search', params=params)

    def suggestions(self, keyword: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/search/suggestions', params={'keyword': keyword, **extra})

    def vision(
        self,
        *,
        image_url:    str | None = None,
        image_base64: str | None = None,
        mode:         str        = 'both',
        **extra:      Any,
    ) -> APIResponse:
        body = {'image_url': image_url, 'image_base64': image_base64, 'mode': mode, **extra}
        return self._t.request('POST', '/v1/vision/ecom-search', json_body=body)


class TakoResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def ask(self, query: str, *, aweme_id: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/tako/ask', json_body={'query': query, 'aweme_id': aweme_id, **extra})

    def chat(self, messages: Sequence[dict[str, Any]], **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/tako/chat', json_body={'messages': list(messages), **extra})

    def suggestions(self, query: str | None = None, *, aweme_id: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/tako/sug', params={'aweme_id': aweme_id, 'query': query, **extra})

    def conversation(self, account_id: str, conversation_id: str, **extra: Any) -> APIResponse:
        params = {'account_id': account_id, 'conversation_id': conversation_id, **extra}
        return self._t.request('GET', '/v1/tako/conversation', params=params)

    def inbox(self, account_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/tako/inbox', params={'account_id': account_id, **extra})

    def memory(self, account_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/tako/memory', params={'account_id': account_id, **extra})


class CreatorResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def search_insights(
        self,
        keyword: str,
        *,
        cursor:  str | None = None,
        count:   int | None = None,
        **extra: Any,
    ) -> APIResponse:
        return self._t.request('GET', '/v1/creator/search-insights', params={'keyword': keyword, 'cursor': cursor, 'count': count, **extra})

    def insight_detail(self, topic_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/creator/search-insights/detail', params={'topic_id': topic_id, **extra})

    def insight_trend(self, topic_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/creator/search-insights/trend', params={'topic_id': topic_id, **extra})

    def insight_videos(self, topic_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/creator/search-insights/videos', params={'topic_id': topic_id, 'cursor': cursor, 'count': count, **extra})

    def recommended_terms(self, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/creator/recommended-terms', params=extra)


class DouyinResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def hot(self, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/douyin/hot', params=extra)

    def search(self, keyword: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/douyin/search', params={'keyword': keyword, **extra})

    def brand(self, *, category: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/douyin/brand', params={'category': category, **extra})

    def music(self, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/douyin/music', params=extra)


class ShopResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def pdp(self, product_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/product-page', params={'product_id': product_id, 'url': url, **extra})

    def live_bag(self, room_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/live-bag', params={'room_id': room_id, **extra})

    def search(self, keyword: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/search', params={'keyword': keyword, 'cursor': cursor, 'count': count, **extra})

    def browse(self, *, keyword: str | None = None, product_id: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/shop/browse', json_body={'keyword': keyword, 'product_id': product_id, **extra})

    def seller(self, seller_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/seller', params={'seller_id': seller_id, 'cursor': cursor, 'count': count, **extra})

    def seller_categories(self, seller_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/seller/categories', params={'seller_id': seller_id, **extra})

    def seller_reviews(self, seller_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/seller/reviews', params={'seller_id': seller_id, 'cursor': cursor, 'count': count, **extra})

    def showcase(self, username: str | None = None, *, sec_uid: str | None = None, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/showcase', params=_user_target(username, sec_uid, cursor=cursor, count=count, **extra))

    def reviews(self, product_id: str | None = None, *, url: str | None = None, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/reviews', params={'product_id': product_id, 'url': url, 'cursor': cursor, 'count': count, **extra})

    def anchors(self, aweme_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/anchors', params={'aweme_id': aweme_id, **extra})

    def mall(self, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/mall', params=extra)

    def tab(self, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/tab', params=extra)

    def live_products(self, room_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/live-products', params={'room_id': room_id, **extra})

    def live_room(self, room_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/live-room', params={'room_id': room_id, **extra})

    def suggestions(self, keyword: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/suggestions', params={'keyword': keyword, **extra})

    def creator(self, username: str | None = None, *, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/creator', params=_user_target(username, sec_uid, **extra))

    def same_shop(self, product_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/same-shop', params={'product_id': product_id, 'url': url, **extra})

    def recommendations(self, product_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/recommendations', params={'product_id': product_id, 'url': url, **extra})

    def promotions(self, product_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/promotions', params={'product_id': product_id, 'url': url, **extra})

    def translation(self, product_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/shop/translation', params={'product_id': product_id, 'url': url, **extra})


class LiveResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def room(self, room_id: str | None = None, *, username: str | None = None, url: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/live/room', params={'room_id': room_id, 'username': username, 'url': url, **extra})

    def check_alive(self, room_ids: Sequence[str] | str, **extra: Any) -> APIResponse:
        joined = room_ids if isinstance(room_ids, str) else ','.join(room_ids)
        return self._t.request('GET', '/v1/live/check-alive', params={'room_ids': joined, **extra})

    def chat(self, room_id: str, *, cursor: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/live/chat', params={'room_id': room_id, 'cursor': cursor, **extra})

    def with_chat(self, room_id: str, *, cursor: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/live/with-chat', params={'room_id': room_id, 'cursor': cursor, **extra})

    def stream(self, room_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/live/stream', params={'room_id': room_id, **extra})

    def audience(self, room_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/live/audience', params={'room_id': room_id, **extra})

    def ranking(self, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/live/ranking', params=extra)

    def gifts(self, room_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/live/gifts', params={'room_id': room_id, **extra})

    def recommended(self, *, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/live/recommended', params={'count': count, **extra})

    def goody_bag(self, room_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/live/goody-bag', params={'room_id': room_id, **extra})

    def bag_items(self, room_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/live/bag-items', params={'room_id': room_id, **extra})


class SeriesResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def mini_dramas(self, *, tab_id: str | None = None, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/series/mini-dramas', params={'tab_id': tab_id, 'cursor': cursor, 'count': count, **extra})

    def mini_drama_tabs(self, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/series/mini-dramas/tabs', params=extra)

    def mini_drama_history(self, account_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/series/mini-dramas/history', params={'account_id': account_id, 'cursor': cursor, 'count': count, **extra})

    def get(self, series_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/series', params={'series_id': series_id, **extra})

    def videos(self, series_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/series/videos', params={'series_id': series_id, 'cursor': cursor, 'count': count, **extra})

    def mix(self, mix_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/mix', params={'mix_id': mix_id, **extra})

    def mix_videos(self, mix_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/mix/videos', params={'mix_id': mix_id, 'cursor': cursor, 'count': count, **extra})


class MusicResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def get(self, music_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/music', params={'music_id': music_id, 'cursor': cursor, 'count': count, **extra})

    def fresh(self, music_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/music/fresh', params={'music_id': music_id, 'cursor': cursor, 'count': count, **extra})

    def user_original(self, username: str | None = None, *, sec_uid: str | None = None, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/music/user-original', params=_user_target(username, sec_uid, cursor=cursor, count=count, **extra))

    def charts(self, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/music/charts', params=extra)


class HashtagResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def get(self, hashtag: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/hashtag', params={'hashtag': hashtag.lstrip('#'), 'cursor': cursor, 'count': count, **extra})

    def trending(self, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/hashtag/trending', params=extra)


class AccountResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def import_session(
        self,
        session_id: str,
        *,
        cookies:    dict[str, str] | None = None,
        device_id:  str | None            = None,
        **extra:    Any,
    ) -> APIResponse:
        body = {'session_id': session_id, 'cookies': cookies, 'device_id': device_id, **extra}
        return self._t.request('POST', '/v1/account/import', json_body=body)

    def login_otp_send(self, email: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/login/otp/send', json_body={'email': email, **extra})

    def login_otp_verify(
        self,
        email:           str,
        code:            str,
        *,
        context_id:      str | None = None,
        passport_ticket: str | None = None,
        **extra:         Any,
    ) -> APIResponse:
        body = {'email': email, 'code': code, 'context_id': context_id, 'passport_ticket': passport_ticket, **extra}
        return self._t.request('POST', '/v1/account/login/otp/verify', json_body=body)

    def register_email_send(
        self,
        email:      str,
        *,
        proxy:      str | None = None,
        context_id: str | None = None,
        birthday:   str | None = None,
        **extra:    Any,
    ) -> APIResponse:
        body = {'email': email, 'proxy': proxy, 'context_id': context_id, 'birthday': birthday, **extra}
        return self._t.request('POST', '/v1/account/register/email/send', json_body=body)

    def register_email_verify(
        self,
        email:      str,
        code:       str,
        *,
        password:   str | None = None,
        proxy:      str | None = None,
        context_id: str | None = None,
        birthday:   str | None = None,
        username:   str | None = None,
        nickname:   str | None = None,
        **extra:    Any,
    ) -> APIResponse:
        body = {
            'email'      : email,
            'code'       : code,
            'password'   : password,
            'proxy'      : proxy,
            'context_id' : context_id,
            'birthday'   : birthday,
            'username'   : username,
            'nickname'   : nickname,
            **extra,
        }
        return self._t.request('POST', '/v1/account/register/email/verify', json_body=body)

    def refresh_session(self, account_id: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/session', json_body={'account_id': account_id, **extra})

    def health(self, account_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/account/health', params={'account_id': account_id, **extra})

    def warm_niche(self, account_id: str, niche: str, *, duration_sec: int | None = None, **extra: Any) -> APIResponse:
        body = {'account_id': account_id, 'niche': niche, 'duration_sec': duration_sec, **extra}
        return self._t.request('POST', '/v1/account/warm/niche', json_body=body)

    def warm_seed_accounts(self, account_id: str, usernames: Sequence[str], **extra: Any) -> APIResponse:
        body = {'account_id': account_id, 'usernames': list(usernames), **extra}
        return self._t.request('POST', '/v1/account/warm/seed-accounts', json_body=body)

    def warm_watch_item(self, account_id: str, aweme_id: str, *, play_delta_ms: int | None = None, finish: bool | None = None, **extra: Any) -> APIResponse:
        body = {'account_id': account_id, 'aweme_id': aweme_id, 'play_delta_ms': play_delta_ms, 'finish': finish, **extra}
        return self._t.request('POST', '/v1/account/warm/watch-item', json_body=body)

    def upload_precheck(self, account_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/account/upload/precheck', params={'account_id': account_id, **extra})

    def upload_video(
        self,
        account_id:   str,
        *,
        file:         FileInput | None     = None,
        video_url:    str | None           = None,
        video_base64: str | None           = None,
        caption:      str | None           = None,
        hashtags:     Sequence[str] | None = None,
        mentions:     Sequence[str] | None = None,
        visibility:   str | None           = None,
        **extra:      Any,
    ) -> APIResponse:
        payload: dict[str, Any] = {
            'account_id'   : account_id,
            'video_url'    : video_url,
            'video_base64' : video_base64,
            'caption'      : caption,
            'hashtags'     : list(hashtags) if hashtags is not None else None,
            'mentions'     : list(mentions) if mentions is not None else None,
            'visibility'   : visibility,
            **extra,
        }
        if file is not None:
            return self._t.request(
                'POST',
                '/v1/account/upload/video',
                data  = payload,
                files = [prepare_file('file', file)],
            )
        return self._t.request('POST', '/v1/account/upload/video', json_body=payload)

    def upload_slideshow(
        self,
        account_id: str,
        *,
        files:      Sequence[FileInput] | None = None,
        images:     Sequence[str] | None       = None,
        title:      str | None                 = None,
        caption:    str | None                 = None,
        visibility: str | None                 = None,
        **extra:    Any,
    ) -> APIResponse:
        payload: dict[str, Any] = {
            'account_id' : account_id,
            'images'     : list(images) if images is not None else None,
            'title'      : title,
            'caption'    : caption,
            'visibility' : visibility,
            **extra,
        }
        if files is not None:
            prepared = [prepare_file('files[]', f) for f in files]
            return self._t.request('POST', '/v1/account/upload/slideshow', data=payload, files=prepared)
        return self._t.request('POST', '/v1/account/upload/slideshow', json_body=payload)

    def delete_post(self, account_id: str, aweme_id: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/upload/delete', json_body={'account_id': account_id, 'aweme_id': aweme_id, **extra})

    def set_post_visibility(self, account_id: str, aweme_id: str, visibility: str, **extra: Any) -> APIResponse:
        body = {'account_id': account_id, 'aweme_id': aweme_id, 'visibility': visibility, **extra}
        return self._t.request('POST', '/v1/account/post/visibility', json_body=body)

    def update_profile(
        self,
        account_id: str,
        *,
        nickname:   str | None = None,
        signature:  str | None = None,
        bio_url:    str | None = None,
        **extra:    Any,
    ) -> APIResponse:
        body = {'account_id': account_id, 'nickname': nickname, 'signature': signature, 'bio_url': bio_url, **extra}
        return self._t.request('POST', '/v1/account/profile/update', json_body=body)

    def update_username(
        self,
        account_id: str,
        username:   str,
        *,
        full_flow:  bool = True,
        **extra:    Any,
    ) -> APIResponse:
        body = {'account_id': account_id, 'username': username.lstrip('@'), 'full_flow': full_flow, **extra}
        return self._t.request('POST', '/v1/account/profile/username', json_body=body)

    claim_username = update_username

    def update_avatar(
        self,
        account_id: str,
        image_b64:  str,
        *,
        filename:   str | None = None,
        mime_type:  str | None = None,
        **extra:    Any,
    ) -> APIResponse:
        body = {'account_id': account_id, 'image_b64': image_b64, 'filename': filename, 'mime_type': mime_type, **extra}
        return self._t.request('POST', '/v1/account/profile/avatar', json_body=body)

    def update_privacy(
        self,
        account_id: str,
        *,
        mode:       str = 'set',
        field:      str = 'private_account',
        value:      Any = 0,
        **extra:    Any,
    ) -> APIResponse:
        body = {'account_id': account_id, 'mode': mode, 'field': field, 'value': value, **extra}
        return self._t.request('POST', '/v1/account/profile/privacy', json_body=body)

    def studio_overview(self, account_id: str, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/account/studio/overview', params={'account_id': account_id, **extra})

    def like(self, account_id: str, aweme_id: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/like', json_body={'account_id': account_id, 'aweme_id': aweme_id, **extra})

    def unlike(self, account_id: str, aweme_id: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/unlike', json_body={'account_id': account_id, 'aweme_id': aweme_id, **extra})

    def follow(self, account_id: str, *, user_id: str | None = None, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/follow', json_body={'account_id': account_id, 'user_id': user_id, 'sec_uid': sec_uid, **extra})

    def unfollow(self, account_id: str, *, user_id: str | None = None, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/unfollow', json_body={'account_id': account_id, 'user_id': user_id, 'sec_uid': sec_uid, **extra})

    def repost(self, account_id: str, aweme_id: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/repost', json_body={'account_id': account_id, 'aweme_id': aweme_id, **extra})

    def unrepost(self, account_id: str, aweme_id: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/unrepost', json_body={'account_id': account_id, 'aweme_id': aweme_id, **extra})

    def favorite(self, account_id: str, aweme_id: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/favorite', json_body={'account_id': account_id, 'aweme_id': aweme_id, **extra})

    def unfavorite(self, account_id: str, aweme_id: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/unfavorite', json_body={'account_id': account_id, 'aweme_id': aweme_id, **extra})

    def share(self, account_id: str, aweme_id: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/share', json_body={'account_id': account_id, 'aweme_id': aweme_id, **extra})

    def action(self, account_id: str, action_type: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/action', json_body={'account_id': account_id, 'action': action_type, **extra})

    def comment(self, account_id: str, aweme_id: str, text: str, *, reply_to_comment_id: str | None = None, **extra: Any) -> APIResponse:
        body = {'account_id': account_id, 'aweme_id': aweme_id, 'text': text, 'reply_to_comment_id': reply_to_comment_id, **extra}
        return self._t.request('POST', '/v1/account/comment', json_body=body)

    def dm_inbox(self, account_id: str, *, cursor: str | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/account/dm/inbox', params={'account_id': account_id, 'cursor': cursor, **extra})

    def dm_conversations(self, account_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return self._t.request('GET', '/v1/account/dm/conversation/list', params={'account_id': account_id, 'cursor': cursor, 'count': count, **extra})

    def dm_messages(self, account_id: str, conversation_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        params = {'account_id': account_id, 'conversation_id': conversation_id, 'cursor': cursor, 'count': count, **extra}
        return self._t.request('GET', '/v1/account/dm/conversation/messages', params=params)

    def dm_send(
        self,
        account_id:      str,
        text:            str,
        *,
        conversation_id: str | None = None,
        to:              str | None = None,
        **extra:         Any,
    ) -> APIResponse:
        body = {'account_id': account_id, 'text': text, 'conversation_id': conversation_id, 'to': to, **extra}
        return self._t.request('POST', '/v1/account/dm/send', json_body=body)

    def dm_typing(self, account_id: str, conversation_id: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/dm/typing', json_body={'account_id': account_id, 'conversation_id': conversation_id, **extra})

    def live_start(self, account_id: str, title: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/live/start', json_body={'account_id': account_id, 'title': title, **extra})

    def live_ping(self, account_id: str, room_id: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/live/ping', json_body={'account_id': account_id, 'room_id': room_id, **extra})

    def live_finish(self, account_id: str, room_id: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/live/finish', json_body={'account_id': account_id, 'room_id': room_id, **extra})

    def session_cold_reopen(self, account_id: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/session/cold-reopen', json_body={'account_id': account_id, **extra})

    def session_warm_reopen(self, account_id: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/session/warm-reopen', json_body={'account_id': account_id, **extra})

    def session_background(self, account_id: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/session/background', json_body={'account_id': account_id, **extra})

    def session_tick(self, account_id: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/account/session/tick', json_body={'account_id': account_id, **extra})


class DevicesResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def list(self) -> APIResponse:
        return self._t.request('GET', '/v1/devices', apply_matrix=False)

    def get(self, device_id: str) -> APIResponse:
        seg = _path_seg(device_id, 'device_id')
        return self._t.request('GET', f'/v1/devices/{seg}', apply_matrix=False)

    def templates(self, *, os: str | None = None) -> APIResponse:
        return self._t.request('GET', '/v1/devices/templates', params={'os': os}, apply_matrix=False)

    def app_versions(self) -> APIResponse:
        return self._t.request('GET', '/v1/apps/versions', apply_matrix=False)

    def provision(
        self,
        *,
        region:            str        = 'US',
        city:              str | None = None,
        os:                str | None = None,
        app_flavour:       str | None = None,
        app_version:       str | None = None,
        hardware_template: str | None = None,
    ) -> APIResponse:
        body = {
            'region'            : region,
            'city'              : city,
            'os'                : os,
            'app_flavour'       : app_flavour,
            'app_version'       : app_version,
            'hardware_template' : hardware_template,
        }
        return self._t.request('POST', '/v1/devices/provision', json_body=body)

    def bootstrap(self, device_id: str, *, warmup: bool = True) -> APIResponse:
        seg = _path_seg(device_id, 'device_id')
        return self._t.request('POST', f'/v1/devices/{seg}/bootstrap', json_body={'warmup': warmup}, apply_matrix=False)

    def report(self, device_id: str, *, scene: str = 'full_sequence') -> APIResponse:
        seg = _path_seg(device_id, 'device_id')
        return self._t.request('POST', f'/v1/devices/{seg}/report', json_body={'scene': scene}, apply_matrix=False)

    def warm(self, device_id: str, *, niche: str, duration_sec: int | None = None) -> APIResponse:
        seg = _path_seg(device_id, 'device_id')
        body = {'niche': niche, 'duration_sec': duration_sec}
        return self._t.request('POST', f'/v1/devices/{seg}/warm', json_body=body, apply_matrix=False)


class CryptoResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def sign(
        self,
        url:     str,
        *,
        method:  str                   = 'GET',
        headers: dict[str, str] | None = None,
        body:    str | None            = None,
        **extra: Any,
    ) -> APIResponse:
        payload = {'method': method.upper(), 'url': url, 'headers': headers, 'body': body, **extra}
        return self._t.request('POST', '/v1/crypto/sign', json_body=payload)

    def protobuf_decode(self, hex_payload: str) -> APIResponse:
        return self._t.request('POST', '/v1/crypto/protobuf/decode', json_body={'hex': hex_payload}, apply_matrix=False)

    def protobuf_encode(self, fields: dict[str, Any]) -> APIResponse:
        return self._t.request('POST', '/v1/crypto/protobuf/encode', json_body={'fields': fields}, apply_matrix=False)

    def x_cylons(
        self,
        query_string: str,
        *,
        x_ss_stub:    str | None = None,
        lanusk:       str | None = None,
        lanusv:       str | None = None,
        khronos:      int | None = None,
    ) -> APIResponse:
        body = {
            'query_string' : query_string,
            'x_ss_stub'    : x_ss_stub,
            'lanusk'       : lanusk,
            'lanusv'       : lanusv,
            'khronos'      : khronos,
        }
        return self._t.request('POST', '/v1/crypto/x-cylons', json_body=body, apply_matrix=False)

    def x_cylons_decrypt(
        self,
        x_cylons:     str,
        *,
        query_string: str | None = None,
        x_ss_stub:    str | None = None,
        lanusk:       str | None = None,
        lanusv:       str | None = None,
    ) -> APIResponse:
        body = {
            'x_cylons'     : x_cylons,
            'query_string' : query_string,
            'x_ss_stub'    : x_ss_stub,
            'lanusk'       : lanusk,
            'lanusv'       : lanusv,
        }
        return self._t.request('POST', '/v1/crypto/x-cylons/decrypt', json_body=body, apply_matrix=False)

    def mssdk_decrypt(
        self,
        operation:      str,
        payload_base64: str,
        **extra:        Any,
    ) -> APIResponse:
        body = {
            'operation'      : operation,
            'payload_base64' : payload_base64,
            **extra,
        }
        return self._t.request('POST', '/v1/crypto/mssdk/decrypt', json_body=body)

    def x_argus_decrypt(self, x_argus: str, **extra: Any) -> APIResponse:
        return self._t.request('POST', '/v1/crypto/x-argus/decrypt', json_body={'x_argus': x_argus, **extra})

    def x_ladon_decrypt(self, x_ladon: str, *, aid: str = '1233') -> APIResponse:
        return self._t.request('POST', '/v1/crypto/x-ladon/decrypt', json_body={'x_ladon': x_ladon, 'aid': aid}, apply_matrix=False)

    def x_gorgon_decrypt(self, x_gorgon: str) -> APIResponse:
        return self._t.request('POST', '/v1/crypto/x-gorgon/decrypt', json_body={'x_gorgon': x_gorgon}, apply_matrix=False)

    def ttencrypt_encrypt(self, plaintext: str, *, compress: bool = True) -> APIResponse:
        return self._t.request('POST', '/v1/crypto/ttencrypt/encrypt', json_body={'plaintext': plaintext, 'compress': compress}, apply_matrix=False)

    def ttencrypt_decrypt(self, ciphertext_base64: str) -> APIResponse:
        return self._t.request('POST', '/v1/crypto/ttencrypt/decrypt', json_body={'ciphertext_base64': ciphertext_base64}, apply_matrix=False)

    def zstd_compress(self, data_base64: str) -> APIResponse:
        return self._t.request('POST', '/v1/crypto/zstd/compress', json_body={'data_base64': data_base64}, apply_matrix=False)

    def zstd_decompress(self, data_base64: str) -> APIResponse:
        return self._t.request('POST', '/v1/crypto/zstd/decompress', json_body={'data_base64': data_base64}, apply_matrix=False)

    def passport_hash(self, value: str, *, identifier_type: str = 'email') -> APIResponse:
        body = {'value': value, 'identifier_type': identifier_type}
        return self._t.request('POST', '/v1/crypto/passport-hash', json_body=body, apply_matrix=False)


class JobsResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._t = transport

    def submit(self, tasks: Sequence[dict[str, Any]], *, webhook_url: str | None = None, **extra: Any) -> APIResponse:
        body = {'tasks': list(tasks), 'webhook_url': webhook_url, **extra}
        return self._t.request('POST', '/v1/jobs/submit', json_body=body)

    def get(self, job_id: str) -> APIResponse:
        seg = _path_seg(job_id, 'job_id')
        return self._t.request('GET', f'/v1/jobs/{seg}', apply_matrix=False)

    def wait(self, job_id: str, *, poll_interval: float = 1.0, timeout: float = 60.0) -> APIResponse:
        seg      = _path_seg(job_id, 'job_id')
        interval = max(0.05, float(poll_interval))
        deadline = time.monotonic() + float(timeout)
        while True:
            res   = self._t.request('GET', f'/v1/jobs/{seg}', apply_matrix=False)
            raw   = res.get('state') if isinstance(res.get('state'), str) else res.get('status')
            state = raw.lower() if isinstance(raw, str) else ''
            if state in _TERMINAL_JOB_STATES or res.get('done') is True:
                return res
            if time.monotonic() + interval > deadline:
                raise TikUltraError(
                    f'Timed out waiting for job {seg} after {timeout}s',
                    status_code = 408,
                    code        = 'job_timeout',
                )
            time.sleep(interval)


class AsyncVideoResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def get(self, aweme_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/video', params=_video_target(aweme_id, url, **extra))

    async def batch(self, aweme_ids: Sequence[str], **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/video/batch', json_body={'aweme_ids': list(aweme_ids), **extra})

    async def comments(
        self,
        aweme_id:      str | None = None,
        *,
        url:           str | None = None,
        cursor:        str | None = None,
        count:         int | None = None,
        sort_strategy: str | None = None,
        **extra:       Any,
    ) -> APIResponse:
        params = _video_target(aweme_id, url, cursor=cursor, count=count, sort_strategy=sort_strategy, **extra)
        return await self._t.request('GET', '/v1/video/comments', params=params)

    async def comment_replies(
        self,
        aweme_id:   str,
        comment_id: str,
        *,
        cursor:     str | None = None,
        count:      int | None = None,
        **extra:    Any,
    ) -> APIResponse:
        params = {'aweme_id': aweme_id, 'comment_id': comment_id, 'cursor': cursor, 'count': count, **extra}
        return await self._t.request('GET', '/v1/video/comments/replies', params=params)

    async def comments_by_ids(self, comment_ids: Sequence[str] | str, **extra: Any) -> APIResponse:
        joined = comment_ids if isinstance(comment_ids, str) else ','.join(comment_ids)
        return await self._t.request('GET', '/v1/video/comments/by-ids', params={'comment_ids': joined, **extra})

    async def danmaku(
        self,
        aweme_id:      str,
        *,
        start_time_ms: int | None = None,
        end_time_ms:   int | None = None,
        **extra:       Any,
    ) -> APIResponse:
        params = {'aweme_id': aweme_id, 'start_time_ms': start_time_ms, 'end_time_ms': end_time_ms, **extra}
        return await self._t.request('GET', '/v1/video/danmaku', params=params)

    async def transcript(
        self,
        aweme_id: str | None = None,
        *,
        url:      str | None = None,
        lang:     str | None = None,
        **extra:  Any,
    ) -> APIResponse:
        return await self._t.request('GET', '/v1/video/transcript', params=_video_target(aweme_id, url, lang=lang, **extra))

    async def no_watermark(self, aweme_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/video/no-watermark', params=_video_target(aweme_id, url, **extra))

    async def slideshow(self, aweme_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/video/slideshow', params=_video_target(aweme_id, url, **extra))

    async def duets(self, aweme_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/video/duets', params={'aweme_id': aweme_id, 'cursor': cursor, 'count': count, **extra})

    async def anchors(self, aweme_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/video/anchors', params={'aweme_id': aweme_id, **extra})

    async def upvotes(self, aweme_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/video/upvotes', params={'aweme_id': aweme_id, 'cursor': cursor, 'count': count, **extra})

    async def share_info(self, aweme_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/video/share-info', params={'aweme_id': aweme_id, **extra})

    async def gifts(self, aweme_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/video/gifts', params={'aweme_id': aweme_id, **extra})

    async def forensics(self, aweme_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/video/forensics', params=_video_target(aweme_id, url, **extra))

    async def fyp_velocity(self, aweme_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/video/fyp-velocity', params=_video_target(aweme_id, url, **extra))

    async def comment_leads(self, aweme_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/video/comment-leads', params=_video_target(aweme_id, url, **extra))


class AsyncUserResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def profile(
        self,
        username: str | None = None,
        *,
        sec_uid:  str | None = None,
        uid:      str | None = None,
        url:      str | None = None,
        **extra:  Any,
    ) -> APIResponse:
        return await self._t.request('GET', '/v1/user', params=_user_target(username, sec_uid, uid, url, **extra))

    get = profile

    async def posts(
        self,
        username: str | None = None,
        *,
        sec_uid:  str | None = None,
        cursor:   str | None = None,
        count:    int | None = None,
        sort:     str | None = None,
        **extra:  Any,
    ) -> APIResponse:
        params = _user_target(username, sec_uid, cursor=cursor, count=count, sort=sort, **extra)
        return await self._t.request('GET', '/v1/user/posts', params=params)

    async def with_posts(self, username: str | None = None, *, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/user/with-posts', params=_user_target(username, sec_uid, **extra))

    async def stories(
        self,
        username: str | None = None,
        *,
        sec_uid:  str | None = None,
        uid:      str | None = None,
        cursor:   str | None = None,
        count:    int | None = None,
        **extra:  Any,
    ) -> APIResponse:
        return await self._t.request('GET', '/v1/user/stories', params=_user_target(username, sec_uid, uid, cursor=cursor, count=count, **extra))

    async def stories_batch(self, usernames: Sequence[str], **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/user/stories/batch', json_body={'usernames': list(usernames), **extra})

    async def reposts(
        self,
        username: str | None = None,
        *,
        sec_uid:  str | None = None,
        cursor:   str | None = None,
        count:    int | None = None,
        **extra:  Any,
    ) -> APIResponse:
        return await self._t.request('GET', '/v1/user/reposts', params=_user_target(username, sec_uid, cursor=cursor, count=count, **extra))

    async def favorites(
        self,
        username: str | None = None,
        *,
        sec_uid:  str | None = None,
        cursor:   str | None = None,
        count:    int | None = None,
        **extra:  Any,
    ) -> APIResponse:
        return await self._t.request('GET', '/v1/user/favorites', params=_user_target(username, sec_uid, cursor=cursor, count=count, **extra))

    async def playlists(
        self,
        username: str | None = None,
        *,
        sec_uid:  str | None = None,
        cursor:   str | None = None,
        count:    int | None = None,
        **extra:  Any,
    ) -> APIResponse:
        return await self._t.request('GET', '/v1/user/playlists', params=_user_target(username, sec_uid, cursor=cursor, count=count, **extra))

    async def followers(
        self,
        username: str | None = None,
        *,
        sec_uid:  str | None = None,
        cursor:   str | None = None,
        count:    int | None = None,
        **extra:  Any,
    ) -> APIResponse:
        return await self._t.request('GET', '/v1/user/followers', params=_user_target(username, sec_uid, cursor=cursor, count=count, **extra))

    async def followings(
        self,
        username: str | None = None,
        *,
        sec_uid:  str | None = None,
        cursor:   str | None = None,
        count:    int | None = None,
        **extra:  Any,
    ) -> APIResponse:
        return await self._t.request('GET', '/v1/user/followings', params=_user_target(username, sec_uid, cursor=cursor, count=count, **extra))

    async def followers_search(self, keyword: str, *, username: str | None = None, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/user/followers/search', params=_user_target(username, sec_uid, keyword=keyword, **extra))

    async def followings_search(self, keyword: str, *, username: str | None = None, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/user/followings/search', params=_user_target(username, sec_uid, keyword=keyword, **extra))

    async def similar(self, username: str | None = None, *, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/user/similar', params=_user_target(username, sec_uid, **extra))

    async def collections(
        self,
        username: str | None = None,
        *,
        sec_uid:  str | None = None,
        cursor:   str | None = None,
        count:    int | None = None,
        **extra:  Any,
    ) -> APIResponse:
        return await self._t.request('GET', '/v1/user/collections', params=_user_target(username, sec_uid, cursor=cursor, count=count, **extra))

    async def collection_videos(self, collection_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/user/collections/videos', params={'collection_id': collection_id, 'cursor': cursor, 'count': count, **extra})

    async def locate_post(self, aweme_id: str, *, username: str | None = None, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/user/locate-post', params=_user_target(username, sec_uid, aweme_id=aweme_id, **extra))

    async def series(self, username: str | None = None, *, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/user/series', params=_user_target(username, sec_uid, **extra))

    async def audit(self, username: str | None = None, *, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/user/audit', params=_user_target(username, sec_uid, **extra))

    async def visibility(self, username: str | None = None, *, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/user/visibility', params=_user_target(username, sec_uid, **extra))

    async def compare(self, usernames: Sequence[str] | str, **extra: Any) -> APIResponse:
        joined = usernames if isinstance(usernames, str) else ','.join(usernames)
        return await self._t.request('GET', '/v1/user/compare', params={'usernames': joined, **extra})

    async def check_username(self, unique_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/user/check-username', params={'unique_id': unique_id.lstrip('@'), **extra})

    async def bulk_check(self, usernames: Sequence[str], **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/user/bulk-check', json_body={'usernames': list(usernames), **extra})


class AsyncFeedResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
        feed_type: str        = 'foryou',
        *,
        cursor:    str | None = None,
        count:     int | None = None,
        **extra:   Any,
    ) -> APIResponse:
        return await self._t.request('GET', '/v1/feed', params={'type': feed_type, 'cursor': cursor, 'count': count, **extra})

    async def fyp(self, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self.get('foryou', cursor=cursor, count=count, **extra)

    async def persona_fyp(
        self,
        niche:   str | None = None,
        *,
        region:  str | None = None,
        city:    str | None = None,
        cursor:  str | None = None,
        count:   int | None = None,
        **extra: Any,
    ) -> APIResponse:
        params = {'niche': niche, 'region': region, 'city': city, 'cursor': cursor, 'count': count, **extra}
        return await self._t.request('GET', '/v1/feed/persona-fyp', params=params)

    async def persona_cities(self, *, region: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/feed/persona-fyp/cities', params={'region': region, **extra}, apply_matrix=False)

    async def stories(self, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/feed/stories', params=extra)

    async def landscape(self, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/feed/landscape', params={'cursor': cursor, 'count': count, **extra})


class AsyncSearchResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def query(
        self,
        keyword:      str,
        *,
        search_type:  str        = 'videos',
        sort_type:    str | None = None,
        publish_time: str | None = None,
        cursor:       str | None = None,
        count:        int | None = None,
        **extra:      Any,
    ) -> APIResponse:
        params = {
            'keyword'      : keyword,
            'type'         : search_type,
            'sort_type'    : sort_type,
            'publish_time' : publish_time,
            'cursor'       : cursor,
            'count'        : count,
            **extra,
        }
        return await self._t.request('GET', '/v1/search', params=params)

    async def suggestions(self, keyword: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/search/suggestions', params={'keyword': keyword, **extra})

    async def vision(
        self,
        *,
        image_url:    str | None = None,
        image_base64: str | None = None,
        mode:         str        = 'both',
        **extra:      Any,
    ) -> APIResponse:
        body = {'image_url': image_url, 'image_base64': image_base64, 'mode': mode, **extra}
        return await self._t.request('POST', '/v1/vision/ecom-search', json_body=body)


class AsyncTakoResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def ask(self, query: str, *, aweme_id: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/tako/ask', json_body={'query': query, 'aweme_id': aweme_id, **extra})

    async def chat(self, messages: Sequence[dict[str, Any]], **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/tako/chat', json_body={'messages': list(messages), **extra})

    async def suggestions(self, query: str | None = None, *, aweme_id: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/tako/sug', params={'aweme_id': aweme_id, 'query': query, **extra})

    async def conversation(self, account_id: str, conversation_id: str, **extra: Any) -> APIResponse:
        params = {'account_id': account_id, 'conversation_id': conversation_id, **extra}
        return await self._t.request('GET', '/v1/tako/conversation', params=params)

    async def inbox(self, account_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/tako/inbox', params={'account_id': account_id, **extra})

    async def memory(self, account_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/tako/memory', params={'account_id': account_id, **extra})


class AsyncShopResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def pdp(self, product_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/product-page', params={'product_id': product_id, 'url': url, **extra})

    async def live_bag(self, room_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/live-bag', params={'room_id': room_id, **extra})

    async def search(self, keyword: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/search', params={'keyword': keyword, 'cursor': cursor, 'count': count, **extra})

    async def browse(self, *, keyword: str | None = None, product_id: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/shop/browse', json_body={'keyword': keyword, 'product_id': product_id, **extra})

    async def seller(self, seller_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/seller', params={'seller_id': seller_id, 'cursor': cursor, 'count': count, **extra})

    async def seller_categories(self, seller_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/seller/categories', params={'seller_id': seller_id, **extra})

    async def seller_reviews(self, seller_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/seller/reviews', params={'seller_id': seller_id, 'cursor': cursor, 'count': count, **extra})

    async def showcase(self, username: str | None = None, *, sec_uid: str | None = None, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/showcase', params=_user_target(username, sec_uid, cursor=cursor, count=count, **extra))

    async def reviews(self, product_id: str | None = None, *, url: str | None = None, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/reviews', params={'product_id': product_id, 'url': url, 'cursor': cursor, 'count': count, **extra})

    async def anchors(self, aweme_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/anchors', params={'aweme_id': aweme_id, **extra})

    async def mall(self, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/mall', params=extra)

    async def tab(self, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/tab', params=extra)

    async def live_products(self, room_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/live-products', params={'room_id': room_id, **extra})

    async def live_room(self, room_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/live-room', params={'room_id': room_id, **extra})

    async def suggestions(self, keyword: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/suggestions', params={'keyword': keyword, **extra})

    async def creator(self, username: str | None = None, *, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/creator', params=_user_target(username, sec_uid, **extra))

    async def same_shop(self, product_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/same-shop', params={'product_id': product_id, 'url': url, **extra})

    async def recommendations(self, product_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/recommendations', params={'product_id': product_id, 'url': url, **extra})

    async def promotions(self, product_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/promotions', params={'product_id': product_id, 'url': url, **extra})

    async def translation(self, product_id: str | None = None, *, url: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/shop/translation', params={'product_id': product_id, 'url': url, **extra})


class AsyncLiveResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def room(self, room_id: str | None = None, *, username: str | None = None, url: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/live/room', params={'room_id': room_id, 'username': username, 'url': url, **extra})

    async def check_alive(self, room_ids: Sequence[str] | str, **extra: Any) -> APIResponse:
        joined = room_ids if isinstance(room_ids, str) else ','.join(room_ids)
        return await self._t.request('GET', '/v1/live/check-alive', params={'room_ids': joined, **extra})

    async def chat(self, room_id: str, *, cursor: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/live/chat', params={'room_id': room_id, 'cursor': cursor, **extra})

    async def with_chat(self, room_id: str, *, cursor: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/live/with-chat', params={'room_id': room_id, 'cursor': cursor, **extra})

    async def stream(self, room_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/live/stream', params={'room_id': room_id, **extra})

    async def audience(self, room_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/live/audience', params={'room_id': room_id, **extra})

    async def ranking(self, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/live/ranking', params=extra)

    async def gifts(self, room_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/live/gifts', params={'room_id': room_id, **extra})

    async def recommended(self, *, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/live/recommended', params={'count': count, **extra})

    async def goody_bag(self, room_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/live/goody-bag', params={'room_id': room_id, **extra})

    async def bag_items(self, room_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/live/bag-items', params={'room_id': room_id, **extra})


class AsyncAccountResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def import_session(
        self,
        session_id: str,
        *,
        cookies:    dict[str, str] | None = None,
        device_id:  str | None            = None,
        **extra:    Any,
    ) -> APIResponse:
        body = {'session_id': session_id, 'cookies': cookies, 'device_id': device_id, **extra}
        return await self._t.request('POST', '/v1/account/import', json_body=body)

    async def login_otp_send(self, email: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/login/otp/send', json_body={'email': email, **extra})

    async def login_otp_verify(
        self,
        email:           str,
        code:            str,
        *,
        context_id:      str | None = None,
        passport_ticket: str | None = None,
        **extra:         Any,
    ) -> APIResponse:
        body = {'email': email, 'code': code, 'context_id': context_id, 'passport_ticket': passport_ticket, **extra}
        return await self._t.request('POST', '/v1/account/login/otp/verify', json_body=body)

    async def register_email_send(
        self,
        email:      str,
        *,
        proxy:      str | None = None,
        context_id: str | None = None,
        birthday:   str | None = None,
        **extra:    Any,
    ) -> APIResponse:
        body = {'email': email, 'proxy': proxy, 'context_id': context_id, 'birthday': birthday, **extra}
        return await self._t.request('POST', '/v1/account/register/email/send', json_body=body)

    async def register_email_verify(
        self,
        email:      str,
        code:       str,
        *,
        password:   str | None = None,
        proxy:      str | None = None,
        context_id: str | None = None,
        birthday:   str | None = None,
        username:   str | None = None,
        nickname:   str | None = None,
        **extra:    Any,
    ) -> APIResponse:
        body = {
            'email'      : email,
            'code'       : code,
            'password'   : password,
            'proxy'      : proxy,
            'context_id' : context_id,
            'birthday'   : birthday,
            'username'   : username,
            'nickname'   : nickname,
            **extra,
        }
        return await self._t.request('POST', '/v1/account/register/email/verify', json_body=body)

    async def refresh_session(self, account_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/session', json_body={'account_id': account_id, **extra})

    async def health(self, account_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/account/health', params={'account_id': account_id, **extra})

    async def warm_niche(self, account_id: str, niche: str, *, duration_sec: int | None = None, **extra: Any) -> APIResponse:
        body = {'account_id': account_id, 'niche': niche, 'duration_sec': duration_sec, **extra}
        return await self._t.request('POST', '/v1/account/warm/niche', json_body=body)

    async def warm_seed_accounts(self, account_id: str, usernames: Sequence[str], **extra: Any) -> APIResponse:
        body = {'account_id': account_id, 'usernames': list(usernames), **extra}
        return await self._t.request('POST', '/v1/account/warm/seed-accounts', json_body=body)

    async def warm_watch_item(self, account_id: str, aweme_id: str, *, play_delta_ms: int | None = None, finish: bool | None = None, **extra: Any) -> APIResponse:
        body = {'account_id': account_id, 'aweme_id': aweme_id, 'play_delta_ms': play_delta_ms, 'finish': finish, **extra}
        return await self._t.request('POST', '/v1/account/warm/watch-item', json_body=body)

    async def upload_precheck(self, account_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/account/upload/precheck', params={'account_id': account_id, **extra})

    async def upload_video(
        self,
        account_id:   str,
        *,
        file:         FileInput | None     = None,
        video_url:    str | None           = None,
        video_base64: str | None           = None,
        caption:      str | None           = None,
        hashtags:     Sequence[str] | None = None,
        mentions:     Sequence[str] | None = None,
        visibility:   str | None           = None,
        **extra:      Any,
    ) -> APIResponse:
        payload: dict[str, Any] = {
            'account_id'   : account_id,
            'video_url'    : video_url,
            'video_base64' : video_base64,
            'caption'      : caption,
            'hashtags'     : list(hashtags) if hashtags is not None else None,
            'mentions'     : list(mentions) if mentions is not None else None,
            'visibility'   : visibility,
            **extra,
        }
        if file is not None:
            return await self._t.request(
                'POST',
                '/v1/account/upload/video',
                data  = payload,
                files = [prepare_file('file', file)],
            )
        return await self._t.request('POST', '/v1/account/upload/video', json_body=payload)

    async def upload_slideshow(
        self,
        account_id: str,
        *,
        files:      Sequence[FileInput] | None = None,
        images:     Sequence[str] | None       = None,
        title:      str | None                 = None,
        caption:    str | None                 = None,
        visibility: str | None                 = None,
        **extra:    Any,
    ) -> APIResponse:
        payload: dict[str, Any] = {
            'account_id' : account_id,
            'images'     : list(images) if images is not None else None,
            'title'      : title,
            'caption'    : caption,
            'visibility' : visibility,
            **extra,
        }
        if files is not None:
            prepared = [prepare_file('files[]', f) for f in files]
            return await self._t.request('POST', '/v1/account/upload/slideshow', data=payload, files=prepared)
        return await self._t.request('POST', '/v1/account/upload/slideshow', json_body=payload)

    async def delete_post(self, account_id: str, aweme_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/upload/delete', json_body={'account_id': account_id, 'aweme_id': aweme_id, **extra})

    async def set_post_visibility(self, account_id: str, aweme_id: str, visibility: str, **extra: Any) -> APIResponse:
        body = {'account_id': account_id, 'aweme_id': aweme_id, 'visibility': visibility, **extra}
        return await self._t.request('POST', '/v1/account/post/visibility', json_body=body)

    async def update_profile(
        self,
        account_id: str,
        *,
        nickname:   str | None = None,
        signature:  str | None = None,
        bio_url:    str | None = None,
        **extra:    Any,
    ) -> APIResponse:
        body = {'account_id': account_id, 'nickname': nickname, 'signature': signature, 'bio_url': bio_url, **extra}
        return await self._t.request('POST', '/v1/account/profile/update', json_body=body)

    async def update_username(
        self,
        account_id: str,
        username:   str,
        *,
        full_flow:  bool = True,
        **extra:    Any,
    ) -> APIResponse:
        body = {'account_id': account_id, 'username': username.lstrip('@'), 'full_flow': full_flow, **extra}
        return await self._t.request('POST', '/v1/account/profile/username', json_body=body)

    claim_username = update_username

    async def update_avatar(
        self,
        account_id: str,
        image_b64:  str,
        *,
        filename:   str | None = None,
        mime_type:  str | None = None,
        **extra:    Any,
    ) -> APIResponse:
        body = {'account_id': account_id, 'image_b64': image_b64, 'filename': filename, 'mime_type': mime_type, **extra}
        return await self._t.request('POST', '/v1/account/profile/avatar', json_body=body)

    async def update_privacy(
        self,
        account_id: str,
        *,
        mode:       str = 'set',
        field:      str = 'private_account',
        value:      Any = 0,
        **extra:    Any,
    ) -> APIResponse:
        body = {'account_id': account_id, 'mode': mode, 'field': field, 'value': value, **extra}
        return await self._t.request('POST', '/v1/account/profile/privacy', json_body=body)

    async def studio_overview(self, account_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/account/studio/overview', params={'account_id': account_id, **extra})

    async def like(self, account_id: str, aweme_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/like', json_body={'account_id': account_id, 'aweme_id': aweme_id, **extra})

    async def unlike(self, account_id: str, aweme_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/unlike', json_body={'account_id': account_id, 'aweme_id': aweme_id, **extra})

    async def follow(self, account_id: str, *, user_id: str | None = None, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/follow', json_body={'account_id': account_id, 'user_id': user_id, 'sec_uid': sec_uid, **extra})

    async def unfollow(self, account_id: str, *, user_id: str | None = None, sec_uid: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/unfollow', json_body={'account_id': account_id, 'user_id': user_id, 'sec_uid': sec_uid, **extra})

    async def repost(self, account_id: str, aweme_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/repost', json_body={'account_id': account_id, 'aweme_id': aweme_id, **extra})

    async def unrepost(self, account_id: str, aweme_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/unrepost', json_body={'account_id': account_id, 'aweme_id': aweme_id, **extra})

    async def favorite(self, account_id: str, aweme_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/favorite', json_body={'account_id': account_id, 'aweme_id': aweme_id, **extra})

    async def unfavorite(self, account_id: str, aweme_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/unfavorite', json_body={'account_id': account_id, 'aweme_id': aweme_id, **extra})

    async def share(self, account_id: str, aweme_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/share', json_body={'account_id': account_id, 'aweme_id': aweme_id, **extra})

    async def action(self, account_id: str, action_type: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/action', json_body={'account_id': account_id, 'action': action_type, **extra})

    async def comment(self, account_id: str, aweme_id: str, text: str, *, reply_to_comment_id: str | None = None, **extra: Any) -> APIResponse:
        body = {'account_id': account_id, 'aweme_id': aweme_id, 'text': text, 'reply_to_comment_id': reply_to_comment_id, **extra}
        return await self._t.request('POST', '/v1/account/comment', json_body=body)

    async def dm_inbox(self, account_id: str, *, cursor: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/account/dm/inbox', params={'account_id': account_id, 'cursor': cursor, **extra})

    async def dm_conversations(self, account_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/account/dm/conversation/list', params={'account_id': account_id, 'cursor': cursor, 'count': count, **extra})

    async def dm_messages(self, account_id: str, conversation_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        params = {'account_id': account_id, 'conversation_id': conversation_id, 'cursor': cursor, 'count': count, **extra}
        return await self._t.request('GET', '/v1/account/dm/conversation/messages', params=params)

    async def dm_send(
        self,
        account_id:      str,
        text:            str,
        *,
        conversation_id: str | None = None,
        to:              str | None = None,
        **extra:         Any,
    ) -> APIResponse:
        body = {'account_id': account_id, 'text': text, 'conversation_id': conversation_id, 'to': to, **extra}
        return await self._t.request('POST', '/v1/account/dm/send', json_body=body)

    async def dm_typing(self, account_id: str, conversation_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/dm/typing', json_body={'account_id': account_id, 'conversation_id': conversation_id, **extra})

    async def live_start(self, account_id: str, title: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/live/start', json_body={'account_id': account_id, 'title': title, **extra})

    async def live_ping(self, account_id: str, room_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/live/ping', json_body={'account_id': account_id, 'room_id': room_id, **extra})

    async def live_finish(self, account_id: str, room_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/live/finish', json_body={'account_id': account_id, 'room_id': room_id, **extra})

    async def session_cold_reopen(self, account_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/session/cold-reopen', json_body={'account_id': account_id, **extra})

    async def session_warm_reopen(self, account_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/session/warm-reopen', json_body={'account_id': account_id, **extra})

    async def session_background(self, account_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/session/background', json_body={'account_id': account_id, **extra})

    async def session_tick(self, account_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/account/session/tick', json_body={'account_id': account_id, **extra})


class AsyncDevicesResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> APIResponse:
        return await self._t.request('GET', '/v1/devices', apply_matrix=False)

    async def get(self, device_id: str) -> APIResponse:
        seg = _path_seg(device_id, 'device_id')
        return await self._t.request('GET', f'/v1/devices/{seg}', apply_matrix=False)

    async def templates(self, *, os: str | None = None) -> APIResponse:
        return await self._t.request('GET', '/v1/devices/templates', params={'os': os}, apply_matrix=False)

    async def app_versions(self) -> APIResponse:
        return await self._t.request('GET', '/v1/apps/versions', apply_matrix=False)

    async def provision(
        self,
        *,
        region:            str        = 'US',
        city:              str | None = None,
        os:                str | None = None,
        app_flavour:       str | None = None,
        app_version:       str | None = None,
        hardware_template: str | None = None,
    ) -> APIResponse:
        body = {
            'region'            : region,
            'city'              : city,
            'os'                : os,
            'app_flavour'       : app_flavour,
            'app_version'       : app_version,
            'hardware_template' : hardware_template,
        }
        return await self._t.request('POST', '/v1/devices/provision', json_body=body)

    async def bootstrap(self, device_id: str, *, warmup: bool = True) -> APIResponse:
        seg = _path_seg(device_id, 'device_id')
        return await self._t.request('POST', f'/v1/devices/{seg}/bootstrap', json_body={'warmup': warmup}, apply_matrix=False)

    async def report(self, device_id: str, *, scene: str = 'full_sequence') -> APIResponse:
        seg = _path_seg(device_id, 'device_id')
        return await self._t.request('POST', f'/v1/devices/{seg}/report', json_body={'scene': scene}, apply_matrix=False)

    async def warm(self, device_id: str, *, niche: str, duration_sec: int | None = None) -> APIResponse:
        seg = _path_seg(device_id, 'device_id')
        body = {'niche': niche, 'duration_sec': duration_sec}
        return await self._t.request('POST', f'/v1/devices/{seg}/warm', json_body=body, apply_matrix=False)


class AsyncCryptoResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def sign(
        self,
        url:     str,
        *,
        method:  str                   = 'GET',
        headers: dict[str, str] | None = None,
        body:    str | None            = None,
        **extra: Any,
    ) -> APIResponse:
        payload = {'method': method.upper(), 'url': url, 'headers': headers, 'body': body, **extra}
        return await self._t.request('POST', '/v1/crypto/sign', json_body=payload)

    async def protobuf_decode(self, hex_payload: str) -> APIResponse:
        return await self._t.request('POST', '/v1/crypto/protobuf/decode', json_body={'hex': hex_payload}, apply_matrix=False)

    async def protobuf_encode(self, fields: dict[str, Any]) -> APIResponse:
        return await self._t.request('POST', '/v1/crypto/protobuf/encode', json_body={'fields': fields}, apply_matrix=False)

    async def x_cylons(
        self,
        query_string: str,
        *,
        x_ss_stub:    str | None = None,
        lanusk:       str | None = None,
        lanusv:       str | None = None,
        khronos:      int | None = None,
    ) -> APIResponse:
        body = {
            'query_string' : query_string,
            'x_ss_stub'    : x_ss_stub,
            'lanusk'       : lanusk,
            'lanusv'       : lanusv,
            'khronos'      : khronos,
        }
        return await self._t.request('POST', '/v1/crypto/x-cylons', json_body=body, apply_matrix=False)

    async def x_cylons_decrypt(
        self,
        x_cylons:     str,
        *,
        query_string: str | None = None,
        x_ss_stub:    str | None = None,
        lanusk:       str | None = None,
        lanusv:       str | None = None,
    ) -> APIResponse:
        body = {
            'x_cylons'     : x_cylons,
            'query_string' : query_string,
            'x_ss_stub'    : x_ss_stub,
            'lanusk'       : lanusk,
            'lanusv'       : lanusv,
        }
        return await self._t.request('POST', '/v1/crypto/x-cylons/decrypt', json_body=body, apply_matrix=False)

    async def mssdk_decrypt(
        self,
        operation:      str,
        payload_base64: str,
        **extra:        Any,
    ) -> APIResponse:
        body = {
            'operation'      : operation,
            'payload_base64' : payload_base64,
            **extra,
        }
        return await self._t.request('POST', '/v1/crypto/mssdk/decrypt', json_body=body)

    async def x_argus_decrypt(self, x_argus: str, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/crypto/x-argus/decrypt', json_body={'x_argus': x_argus, **extra})

    async def x_ladon_decrypt(self, x_ladon: str, *, aid: str = '1233') -> APIResponse:
        return await self._t.request('POST', '/v1/crypto/x-ladon/decrypt', json_body={'x_ladon': x_ladon, 'aid': aid}, apply_matrix=False)

    async def x_gorgon_decrypt(self, x_gorgon: str) -> APIResponse:
        return await self._t.request('POST', '/v1/crypto/x-gorgon/decrypt', json_body={'x_gorgon': x_gorgon}, apply_matrix=False)

    async def ttencrypt_encrypt(self, plaintext: str, *, compress: bool = True) -> APIResponse:
        return await self._t.request('POST', '/v1/crypto/ttencrypt/encrypt', json_body={'plaintext': plaintext, 'compress': compress}, apply_matrix=False)

    async def ttencrypt_decrypt(self, ciphertext_base64: str) -> APIResponse:
        return await self._t.request('POST', '/v1/crypto/ttencrypt/decrypt', json_body={'ciphertext_base64': ciphertext_base64}, apply_matrix=False)

    async def zstd_compress(self, data_base64: str) -> APIResponse:
        return await self._t.request('POST', '/v1/crypto/zstd/compress', json_body={'data_base64': data_base64}, apply_matrix=False)

    async def zstd_decompress(self, data_base64: str) -> APIResponse:
        return await self._t.request('POST', '/v1/crypto/zstd/decompress', json_body={'data_base64': data_base64}, apply_matrix=False)

    async def passport_hash(self, value: str, *, identifier_type: str = 'email') -> APIResponse:
        body = {'value': value, 'identifier_type': identifier_type}
        return await self._t.request('POST', '/v1/crypto/passport-hash', json_body=body, apply_matrix=False)


class AsyncJobsResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def submit(self, tasks: Sequence[dict[str, Any]], *, webhook_url: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('POST', '/v1/jobs/submit', json_body={'tasks': list(tasks), 'webhook_url': webhook_url, **extra})

    async def get(self, job_id: str) -> APIResponse:
        seg = _path_seg(job_id, 'job_id')
        return await self._t.request('GET', f'/v1/jobs/{seg}', apply_matrix=False)

    async def wait(self, job_id: str, *, poll_interval: float = 1.0, timeout: float = 60.0) -> APIResponse:
        seg      = _path_seg(job_id, 'job_id')
        interval = max(0.05, float(poll_interval))
        deadline = time.monotonic() + float(timeout)
        while True:
            res   = await self._t.request('GET', f'/v1/jobs/{seg}', apply_matrix=False)
            raw   = res.get('state') if isinstance(res.get('state'), str) else res.get('status')
            state = raw.lower() if isinstance(raw, str) else ''
            if state in _TERMINAL_JOB_STATES or res.get('done') is True:
                return res
            if time.monotonic() + interval > deadline:
                raise TikUltraError(
                    f'Timed out waiting for job {seg} after {timeout}s',
                    status_code = 408,
                    code        = 'job_timeout',
                )
            await asyncio.sleep(interval)


class AsyncCreatorResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def search_insights(self, keyword: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/creator/search-insights', params={'keyword': keyword, 'cursor': cursor, 'count': count, **extra})

    async def insight_detail(self, topic_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/creator/search-insights/detail', params={'topic_id': topic_id, **extra})

    async def insight_trend(self, topic_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/creator/search-insights/trend', params={'topic_id': topic_id, **extra})

    async def insight_videos(self, topic_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/creator/search-insights/videos', params={'topic_id': topic_id, 'cursor': cursor, 'count': count, **extra})

    async def recommended_terms(self, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/creator/recommended-terms', params=extra)


class AsyncDouyinResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def hot(self, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/douyin/hot', params=extra)

    async def search(self, keyword: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/douyin/search', params={'keyword': keyword, **extra})

    async def brand(self, *, category: str | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/douyin/brand', params={'category': category, **extra})

    async def music(self, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/douyin/music', params=extra)


class AsyncSeriesResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def mini_dramas(self, *, tab_id: str | None = None, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/series/mini-dramas', params={'tab_id': tab_id, 'cursor': cursor, 'count': count, **extra})

    async def mini_drama_tabs(self, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/series/mini-dramas/tabs', params=extra)

    async def mini_drama_history(self, account_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/series/mini-dramas/history', params={'account_id': account_id, 'cursor': cursor, 'count': count, **extra})

    async def get(self, series_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/series', params={'series_id': series_id, **extra})

    async def videos(self, series_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/series/videos', params={'series_id': series_id, 'cursor': cursor, 'count': count, **extra})

    async def mix(self, mix_id: str, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/mix', params={'mix_id': mix_id, **extra})

    async def mix_videos(self, mix_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/mix/videos', params={'mix_id': mix_id, 'cursor': cursor, 'count': count, **extra})


class AsyncMusicResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def get(self, music_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/music', params={'music_id': music_id, 'cursor': cursor, 'count': count, **extra})

    async def fresh(self, music_id: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/music/fresh', params={'music_id': music_id, 'cursor': cursor, 'count': count, **extra})

    async def user_original(self, username: str | None = None, *, sec_uid: str | None = None, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/music/user-original', params=_user_target(username, sec_uid, cursor=cursor, count=count, **extra))

    async def charts(self, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/music/charts', params=extra)


class AsyncHashtagResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def get(self, hashtag: str, *, cursor: str | None = None, count: int | None = None, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/hashtag', params={'hashtag': hashtag.lstrip('#'), 'cursor': cursor, 'count': count, **extra})

    async def trending(self, **extra: Any) -> APIResponse:
        return await self._t.request('GET', '/v1/hashtag/trending', params=extra)
