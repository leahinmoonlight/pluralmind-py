from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Generic, Literal, NotRequired, TypedDict

from typing_extensions import TypeVar

Fragment = TypeVar('Fragment', bound='MessageFragment', default='MessageFragment')

type TwitchId = str | int
"""
The user's numerical Twitch ID, or their login username.
Note: It is always preferable to use the user's numerical ID since that
identifier never changes. If you provide their username, we may not be able to
match them if they have changed their username recently.
"""


class System(TypedDict):
    id: int
    """The numeric ID of the system's Twitch account."""

    color: str | None
    """
    The fallback color that will be used when a member has not specified their
    own color.
    """

    pronouns: str | None
    """
    The fallback pronouns that will be used when a member has not specified
    their own pronouns.
    """

    autoproxy_member_id: int | None
    """
    If set, messages sent without a proxy will be automatically proxied as the
    target member.
    """

    members: list[Member]
    """The list of members in this system."""


class Member(TypedDict):
    id: int
    """
    The unique ID of the member, which may be referenced by
    `System.autoproxy_member_id`.
    """

    name: str
    """The display name of the member."""

    proxies: list[Proxy]
    """The list of proxies to check messages against."""

    case_sensitive: bool
    """
    Whether case-sensitivity should be respected when checking for the proxies
    in the message.
    """

    require_space: bool
    """
    Whether a space needs to separate the proxy from the rest of the
    message.
    """

    color: str | None
    """The color this member would like their name displayed as in chat."""

    pronouns: str | None
    """
    Pronouns for this member.
    When set, this is free text (i.e. "they/them", or "she/they").
    """


class ProxiedMessage(TypedDict, Generic[Fragment]):
    member: Member
    """The member that was identified to be sending the message."""

    system: System
    """The system that the member belongs to."""

    color: str | None
    """
    The color to display this member's name as in chat. Uses the member's color
    when set, and falls back to the system's color if not.
    """

    pronouns: str | None
    """
    The pronouns to display for this member.
    This is free text (i.e. "they/them", or "she/they").
    Uses the member's pronouns when set, and falls back to the system's if not.
    Note: When set, these should take precedent over other pronoun sources such
    as alejo, PronounDB, etc.
    """

    proxy_used: Proxy | None
    """
    The proxy that was detected in the message, if any. This will be None if an
    autoproxy was used.
    """

    clean_fragments: list[Fragment]
    """
    The message's fragments with the proxy removed. If no proxy was used, a
    copy of the original fragments will be returned.
    """

    changed_fragments: dict[int, Fragment | None]
    """
    The fragments to change or remove in order to remove the proxy from the
    message. Fragments are keyed by their original index in the message.
    If a value is None, that fragment should be removed, otherwise it should
    be updated. This will be an empty dict if no proxy was used.

    Note: Depending on your use case, clean_fragments may be simpler. Check out
    both options to see which works best for you. You'll only need to use one
    or the other.
    """

    body: str
    """
    The content of the message with the proxy removed. If an autoproxy was
    used, this will be the original message body.
    """


class FragmentTypes:
    TEXT: Final = 'text'
    """
    Basic text from a message. This can include emojis as well as emotes from
    other services (like FFZ, BTTV, etc.), as long as they are still in their
    text form.
    """

    EMOTE: Final = 'emote'
    """
    A Twitch emote. The emote's name should be provided as
    `MessageFragment.text`. It's expected that there won't be colons around the
    name, since Twitch doesn't actually include those in their messages.
    """

    MENTION: Final = 'mention'
    """
    A @mention of another user. Don't worry about providing this type unless
    you already have the data separated and available. The library will still
    attempt to detect and ignore leading mentions in text fragments.
    """


KNOWN_FRAGMENT_TYPES = frozenset({FragmentTypes.TEXT, FragmentTypes.EMOTE, FragmentTypes.MENTION})


type MessageFragmentType = Literal['text', 'emote', 'mention'] | str


class MessageFragment(TypedDict):
    """
    Twitch messages are generally made up of multiple parts, called fragments.
    For example, a message with a Twitch emote in the middle will actually have
    three fragments: a text fragment, the twitch emote, and another text
    fragment.

    If your data is coming directly from Twitch's EventSub, each message's
    `fragments` property is already compatible with this type.

    Alternatively, if your data is coming from their IRC feed, you can just pass
    the entire body string into `get_proxied_message` without worrying about
    fragments at all.

    In the unlikely event you're working with raw HTML, the message's children
    can be mapped back into these fragments.
    """

    type: MessageFragmentType
    """
    What this fragment represents (text, an emote, etc.). Pluralmind will
    gracefully ignore any fragments that aren't relevant to it.
    For a list of relevant fragment types, check out `FragmentTypes`.
    """

    text: NotRequired[str | None]
    """
    The text value of this fragment. For emote fragments, this is the emote's
    name, and for mention fragments, this is the mention text. It can be safely
    omitted for any fragments that it doesn't apply to.
    """


@dataclass(frozen=True, slots=True)
class CacheHit:
    system: System | None
    """
    The system, if one exists. This will be None if there is no system
    associated with the Twitch user.
    """

    expired: bool
    """
    Whether the cached data was loaded too long ago to be considered fresh.
    This is configurable via `PluralmindConfig.cache_duration`.
    """


class ProxyTypes:
    EITHER_SIDE: Final = 0
    """The proxy can be used as either a prefix or a suffix on the message."""

    PREFIX: Final = 1
    """The proxy must be used at the start of the message."""

    SUFFIX: Final = 2
    """The proxy must be used at the end of the message."""


type ProxyType = Literal[0, 1, 2]


class Proxy(TypedDict):
    text: str
    """The text to look for in the message."""

    type: ProxyType
    """Where the proxy text should be detected in the message."""


class DetectionResult(TypedDict, Generic[Fragment]):
    """
    A raw detection result. See `ProxiedMessage` for more information on these
    fields.
    """

    member: Member
    proxy_used: Proxy
    clean_fragments: list[Fragment]
    changed_fragments: dict[int, Fragment | None]
