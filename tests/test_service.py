from typing import Any, TypedDict

import pytest

from pluralmind._service import detect_proxy_in_message, get_proxied_message

from .fixtures import SampleSystemKey


class CaseDetectionResult(TypedDict):
    member: str
    proxy_used: str
    clean_fragments: list[dict[str, Any]]
    changed_fragments: dict[int, dict[str, Any] | None]


class ProxyTestCase(TypedDict):
    label: str
    fragments: list[Any]
    expected: CaseDetectionResult | None


class Scenario(TypedDict):
    system: SampleSystemKey
    cases: list[ProxyTestCase]


class ParametrizedTestCase(ProxyTestCase):
    id: str
    system: SampleSystemKey


SCENARIOS = [
    Scenario({
        'system': 'moonlight',
        'cases': [
            ProxyTestCase({
                'label': 'simple proxy prefix',
                'fragments': [{'type': 'text', 'text': 'L: hihi~'}],
                'expected': {
                    'member': 'leah',
                    'proxy_used': 'L:',
                    'clean_fragments': [{'type': 'text', 'text': 'hihi~'}],
                    'changed_fragments': {
                        0: {'type': 'text', 'text': 'hihi~'},
                    },
                },
            }),
            ProxyTestCase({
                'label': 'proxy prefix used as a suffix',
                'fragments': [{'type': 'text', 'text': 'hihi~ L:'}],
                'expected': None,
            }),
            ProxyTestCase({
                'label': 'proxy prefix with surrounding whitespace',
                'fragments': [{'type': 'text', 'text': ' L: hihi~ '}],
                'expected': {
                    'member': 'leah',
                    'proxy_used': 'L:',
                    'clean_fragments': [{'type': 'text', 'text': ' hihi~ '}],
                    'changed_fragments': {
                        0: {'type': 'text', 'text': ' hihi~ '},
                    },
                },
            }),
            ProxyTestCase({
                'label': 'proxy suffix with surrounding whitespace',
                'fragments': [{'type': 'text', 'text': 'hihi~ -L '}],
                'expected': {
                    'member': 'leah',
                    'proxy_used': '-L',
                    'clean_fragments': [{'type': 'text', 'text': 'hihi~ '}],
                    'changed_fragments': {
                        0: {'type': 'text', 'text': 'hihi~ '},
                    },
                },
            }),
            ProxyTestCase({
                'label': 'proxy spread across 3 fragments with a Twitch emote in the middle (as a prefix)',
                'fragments': [
                    {'type': 'text', 'text': ' 🌙'},
                    {'type': 'emote', 'text': 'leahinmDance'},
                    {'type': 'text', 'text': '! hihi~'},
                    {'type': 'emote', 'text': 'leahinmLove'},
                    {'type': 'text', 'text': ' '},
                ],
                'expected': {
                    'member': 'leah',
                    'proxy_used': '🌙leahinmDance!',
                    'clean_fragments': [
                        {'type': 'text', 'text': ' '},
                        {'type': 'text', 'text': 'hihi~'},
                        {'type': 'emote', 'text': 'leahinmLove'},
                        {'type': 'text', 'text': ' '},
                    ],
                    'changed_fragments': {
                        0: {'type': 'text', 'text': ' '},
                        1: None,
                        2: {'type': 'text', 'text': 'hihi~'},
                    },
                },
            }),
            ProxyTestCase({
                'label': 'proxy spread across 3 fragments with a Twitch emote in the middle (as a suffix)',
                'fragments': [
                    {'type': 'text', 'text': 'hihi~ '},
                    {'type': 'emote', 'text': 'leahinmLove'},
                    {'type': 'text', 'text': ' 🌙'},
                    {'type': 'emote', 'text': 'leahinmDance'},
                    {'type': 'text', 'text': '! '},
                ],
                'expected': {
                    'member': 'leah',
                    'proxy_used': '🌙leahinmDance!',
                    'clean_fragments': [
                        {'type': 'text', 'text': 'hihi~ '},
                        {'type': 'emote', 'text': 'leahinmLove'},
                        {'type': 'text', 'text': ''},
                        {'type': 'text', 'text': ' '},
                    ],
                    'changed_fragments': {
                        2: {'type': 'text', 'text': ''},
                        3: None,
                        4: {'type': 'text', 'text': ' '},
                    },
                },
            }),
            ProxyTestCase({
                'label': 'either side proxy, empty space in leading fragments',
                'fragments': [
                    {'type': 'text', 'text': ''},
                    {'type': 'text', 'text': ' '},
                    {'type': 'text', 'text': ' 💜 '},
                    {'type': 'emote', 'text': 'leahinmDance'},
                    {'type': 'text', 'text': ' hihi~'},
                ],
                'expected': {
                    'member': 'samara',
                    'proxy_used': '💜',
                    'clean_fragments': [
                        {'type': 'text', 'text': ''},
                        {'type': 'text', 'text': ' '},
                        {'type': 'text', 'text': ' '},
                        {'type': 'emote', 'text': 'leahinmDance'},
                        {'type': 'text', 'text': ' hihi~'},
                    ],
                    'changed_fragments': {
                        2: {'type': 'text', 'text': ' '},
                    },
                },
            }),
            ProxyTestCase({
                'label': 'either side proxy, empty space in trailing fragments',
                'fragments': [
                    {'type': 'emote', 'text': 'leahinmDance'},
                    {'type': 'text', 'text': ' hihi~ 💜 '},
                    {'type': 'text', 'text': ' '},
                    {'type': 'text', 'text': ''},
                ],
                'expected': {
                    'member': 'samara',
                    'proxy_used': '💜',
                    'clean_fragments': [
                        {'type': 'emote', 'text': 'leahinmDance'},
                        {'type': 'text', 'text': ' hihi~ '},
                        {'type': 'text', 'text': ' '},
                        {'type': 'text', 'text': ''},
                    ],
                    'changed_fragments': {
                        1: {'type': 'text', 'text': ' hihi~ '},
                    },
                },
            }),
            ProxyTestCase({
                'label': 'case-insensitive upper proxy matching lower message',
                'fragments': [{'type': 'text', 'text': 'l: hihi~'}],
                'expected': {
                    'member': 'leah',
                    'proxy_used': 'L:',
                    'clean_fragments': [{'type': 'text', 'text': 'hihi~'}],
                    'changed_fragments': {
                        0: {'type': 'text', 'text': 'hihi~'},
                    },
                },
            }),
            ProxyTestCase({
                'label': 'case-sensitive upper proxy with lower message',
                'fragments': [{'type': 'text', 'text': 's: hihi~'}],
                'expected': None,
            }),
            ProxyTestCase({
                'label': 'case-sensitive proxy takes priority over case-insensitive proxy',
                'fragments': [{'type': 'text', 'text': 'hihi~ -l'}],
                'expected': {
                    'member': 'priority',
                    'proxy_used': '-l',
                    'clean_fragments': [{'type': 'text', 'text': 'hihi~'}],
                    'changed_fragments': {
                        0: {'type': 'text', 'text': 'hihi~'},
                    },
                },
            }),
            ProxyTestCase({
                'label': 'longer proxy takes priority over shorter proxy',
                'fragments': [{'type': 'text', 'text': 'S:S: hihi~'}],
                'expected': {
                    'member': 'priority',
                    'proxy_used': 'S:S:',
                    'clean_fragments': [{'type': 'text', 'text': 'hihi~'}],
                    'changed_fragments': {
                        0: {'type': 'text', 'text': 'hihi~'},
                    },
                },
            }),
            ProxyTestCase({
                'label': 'leading mentions are ignored even when in a text fragment',
                'fragments': [{'type': 'text', 'text': ' @someone L: hihi~'}],
                'expected': {
                    'member': 'leah',
                    'proxy_used': 'L:',
                    'clean_fragments': [{'type': 'text', 'text': ' @someone hihi~'}],
                    'changed_fragments': {
                        0: {'type': 'text', 'text': ' @someone hihi~'},
                    },
                },
            }),
            ProxyTestCase({
                'label': 'leading mentions are ignored when in their own fragment',
                'fragments': [
                    {'type': 'mention', 'text': '@someone'},
                    {'type': 'text', 'text': ' L: hihi~'},
                ],
                'expected': {
                    'member': 'leah',
                    'proxy_used': 'L:',
                    'clean_fragments': [
                        {'type': 'mention', 'text': '@someone'},
                        {'type': 'text', 'text': ' hihi~'},
                    ],
                    'changed_fragments': {
                        1: {'type': 'text', 'text': ' hihi~'},
                    },
                },
            }),
            ProxyTestCase({
                'label': 'misc fragment data is preserved',
                'fragments': [
                    {'type': 'mention', 'text': '@someone', 'something': 'else'},
                    {'type': 'text', 'text': ' L: hihi~ ', 'hihi': 'hihi'},
                    {'type': 'emote', 'text': 'leahinmNya', 'image': 'nya.webp'},
                    {'type': 'text', 'text': ' ', 'position': 'end'},
                ],
                'expected': {
                    'member': 'leah',
                    'proxy_used': 'L:',
                    'clean_fragments': [
                        {'type': 'mention', 'text': '@someone', 'something': 'else'},
                        {'type': 'text', 'text': ' hihi~ ', 'hihi': 'hihi'},
                        {'type': 'emote', 'text': 'leahinmNya', 'image': 'nya.webp'},
                        {'type': 'text', 'text': ' ', 'position': 'end'},
                    ],
                    'changed_fragments': {
                        1: {'type': 'text', 'text': ' hihi~ ', 'hihi': 'hihi'},
                    },
                },
            }),
            ProxyTestCase({
                'label': 'proxy prefix without a space does not proxy',
                'fragments': [{'type': 'text', 'text': 'L:hihi~'}],
                'expected': None,
            }),
            ProxyTestCase({
                'label': 'proxy prefix without any content after',
                'fragments': [{'type': 'text', 'text': 'L:'}],
                'expected': None,
            }),
            ProxyTestCase({
                'label': 'proxy surrounded by actual content',
                'fragments': [{'type': 'text', 'text': 'hihi~ L: hihi~'}],
                'expected': None,
            }),
            ProxyTestCase({
                'label': 'proxy prefix with unknown fragment type before it does not proxy',
                'fragments': [
                    {'type': 'cheermote', 'text': 'PrideCheer100'},
                    {'type': 'text', 'text': 'L: hihi~'},
                ],
                'expected': None,
            }),
            ProxyTestCase({
                'label': 'either-side proxy on both sides of the message is used as a prefix',
                'fragments': [{'type': 'text', 'text': '🌙 hihi~ 🌙'}],
                'expected': {
                    'member': 'leah',
                    'proxy_used': '🌙',
                    'clean_fragments': [{'type': 'text', 'text': 'hihi~ 🌙'}],
                    'changed_fragments': {
                        0: {'type': 'text', 'text': 'hihi~ 🌙'},
                    },
                },
            }),
            ProxyTestCase({
                'label': 'verify emoji survive being double reversed',
                'fragments': [{'type': 'text', 'text': 'hihi~ 🌙 💁‍♀️ 🩷 -L'}],
                'expected': {
                    'member': 'leah',
                    'proxy_used': '-L',
                    'clean_fragments': [{'type': 'text', 'text': 'hihi~ 🌙 💁‍♀️ 🩷'}],
                    'changed_fragments': {
                        0: {'type': 'text', 'text': 'hihi~ 🌙 💁‍♀️ 🩷'},
                    },
                },
            }),
            ProxyTestCase({
                'label': 'Samara: verify before interruption checks',
                'fragments': [{'type': 'text', 'text': 'Samara: hihi~'}],
                'expected': {
                    'member': 'samara',
                    'proxy_used': 'Samara:',
                    'clean_fragments': [{'type': 'text', 'text': 'hihi~'}],
                    'changed_fragments': {
                        0: {'type': 'text', 'text': 'hihi~'},
                    },
                },
            }),
            ProxyTestCase({
                'label': 'interrupted proxy',
                'fragments': [{'type': 'text', 'text': 'Sama ra: hihi~'}],
                'expected': None,
            }),
            ProxyTestCase({
                'label': 'interrupted proxy across multiple fragments',
                'fragments': [
                    {'type': 'text', 'text': 'Sama'},
                    {'type': 'text', 'text': ' '},
                    {'type': 'text', 'text': 'ra: hihi~'},
                ],
                'expected': None,
            }),
            ProxyTestCase({
                'label': 'proxy with emote, space and text',
                'fragments': [
                    {'type': 'emote', 'text': 'leahinmWave'},
                    {'type': 'text', 'text': ' L: hihi~'},
                ],
                'expected': {
                    'member': 'leah',
                    'proxy_used': 'leahinmWave L:',
                    'clean_fragments': [
                        {'type': 'text', 'text': 'hihi~'},
                    ],
                    'changed_fragments': {
                        0: None,
                        1: {'type': 'text', 'text': 'hihi~'},
                    },
                },
            }),
        ],
    }),
    Scenario({
        'system': 'retrograde',
        'cases': [
            ProxyTestCase({
                'label': 'prefix without a required space',
                'fragments': [{'type': 'text', 'text': 'd:hihi'}],
                'expected': {
                    'member': 'dani',
                    'proxy_used': 'd:',
                    'clean_fragments': [{'type': 'text', 'text': 'hihi'}],
                    'changed_fragments': {
                        0: {'type': 'text', 'text': 'hihi'},
                    },
                },
            }),
            ProxyTestCase({
                'label': 'suffix without a required space',
                'fragments': [{'type': 'text', 'text': 'hihi-d'}],
                'expected': {
                    'member': 'dani',
                    'proxy_used': '-d',
                    'clean_fragments': [{'type': 'text', 'text': 'hihi'}],
                    'changed_fragments': {
                        0: {'type': 'text', 'text': 'hihi'},
                    },
                },
            }),
            ProxyTestCase({
                'label': 'suffix without a required space (but still with a space)',
                'fragments': [{'type': 'text', 'text': 'hihi -d'}],
                'expected': {
                    'member': 'dani',
                    'proxy_used': '-d',
                    'clean_fragments': [{'type': 'text', 'text': 'hihi '}],
                    'changed_fragments': {
                        0: {'type': 'text', 'text': 'hihi '},
                    },
                },
            }),
        ],
    }),
]

parametrized_cases: list[ParametrizedTestCase] = []
for scenario in SCENARIOS:
    for case in scenario['cases']:
        parametrized_cases.append(
            ParametrizedTestCase({
                'id': f'{scenario["system"]}: {case["label"]}',
                'system': scenario['system'],
                **case,
            })
        )


@pytest.mark.parametrize('case', [pytest.param(c, id=c['id']) for c in parametrized_cases])
def test_proxy_detection(case: ParametrizedTestCase, sample_systems) -> None:
    raw_result = detect_proxy_in_message(sample_systems[case['system']], case['fragments'])
    test_result = (
        {
            **raw_result,
            'member': raw_result['member']['name'],
            'proxy_used': raw_result['proxy_used']['text'],
        }
        if raw_result
        else None
    )
    assert test_result == case['expected']


def test_message_string_instead_of_fragments(sample_systems) -> None:
    pm = get_proxied_message(sample_systems['moonlight'], 'L: hihi~ <3')
    assert pm is not None
    assert pm['member']['name'] == 'leah'
    assert pm['body'] == 'hihi~ <3'


def test_autoproxy(sample_systems) -> None:
    pm1 = get_proxied_message(sample_systems['retrograde'], 'hihi!')
    assert pm1 is not None
    assert pm1['member']['name'] == 'enni'
    assert pm1['body'] == 'hihi!'

    # Verify that autoproxy can still be overridden
    pm2 = get_proxied_message(sample_systems['retrograde'], 'd: hihi!')
    assert pm2 is not None
    assert pm2['member']['name'] == 'dani'
    assert pm2['body'] == ' hihi!'


def test_body_string_with_fragments(sample_systems) -> None:
    pm = get_proxied_message(
        sample_systems['retrograde'],
        [
            {'type': 'text', 'text': 'e: hihi! '},
            {'type': 'emote', 'text': 'leahinmWave'},
            {'type': 'text', 'text': ' how has your stream been going?'},
        ],
    )
    assert pm is not None
    assert pm['member']['name'] == 'enni'
    assert pm['body'] == 'hihi! leahinmWave how has your stream been going?'
