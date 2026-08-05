import itertools
from typing import Literal

from pluralmind._types import Member, Proxy, ProxyTypes, System

counter = itertools.count(start=1)


def make_system(*, members: list[Member], autoproxy_member_id: int | None = None) -> System:
    return {
        'id': next(counter),
        'color': None,
        'pronouns': None,
        'autoproxy_member_id': autoproxy_member_id,
        'members': members,
    }


def make_member(
    *,
    name: str,
    proxies: list[Proxy],
    id: int | None = None,
    case_sensitive: bool = False,
    require_space: bool = True,
    color: str | None = None,
    pronouns: str | None = None,
) -> Member:
    return {
        'id': id or next(counter),
        'name': name,
        'case_sensitive': case_sensitive,
        'require_space': require_space,
        'color': color,
        'pronouns': pronouns,
        'proxies': proxies,
    }


type SampleSystemKey = Literal['moonlight', 'retrograde']


def make_sample_systems() -> dict[SampleSystemKey, System]:
    return {
        'moonlight': make_system(
            members=[
                make_member(
                    name='leah',
                    case_sensitive=False,
                    proxies=[
                        {'text': 'L:', 'type': ProxyTypes.PREFIX},
                        {'text': '-L', 'type': ProxyTypes.SUFFIX},
                        {'text': '🌙', 'type': ProxyTypes.EITHER_SIDE},
                        {'text': '🌙leahinmDance!', 'type': ProxyTypes.EITHER_SIDE},
                        {'text': 'leahinmWave L:', 'type': ProxyTypes.PREFIX},
                    ],
                ),
                make_member(
                    name='samara',
                    case_sensitive=True,
                    proxies=[
                        {'text': 'S:', 'type': ProxyTypes.PREFIX},
                        {'text': '-S', 'type': ProxyTypes.SUFFIX},
                        {'text': '💜', 'type': ProxyTypes.EITHER_SIDE},
                        {'text': 'Samara:', 'type': ProxyTypes.PREFIX},
                    ],
                ),
                make_member(
                    name='priority',
                    case_sensitive=True,
                    proxies=[
                        {'text': 'S:S:', 'type': ProxyTypes.PREFIX},
                        {'text': '-l', 'type': ProxyTypes.SUFFIX},
                    ],
                ),
            ],
        ),
        'retrograde': make_system(
            members=[
                make_member(
                    id=9001,
                    name='enni',
                    proxies=[
                        {'text': 'e:', 'type': ProxyTypes.PREFIX},
                        {'text': '💜', 'type': ProxyTypes.PREFIX},
                        {'text': '🪐', 'type': ProxyTypes.PREFIX},
                        {'text': '-e', 'type': ProxyTypes.SUFFIX},
                    ],
                ),
                make_member(
                    name='dani',
                    require_space=False,
                    proxies=[
                        {'text': 'd:', 'type': ProxyTypes.PREFIX},
                        {'text': '💚', 'type': ProxyTypes.PREFIX},
                        {'text': '-d', 'type': ProxyTypes.SUFFIX},
                    ],
                ),
            ],
            autoproxy_member_id=9001,
        ),
    }
