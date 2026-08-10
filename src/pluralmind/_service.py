from typing import cast

from ._types import (
    DetectionResult,
    Fragment,
    Member,
    ProxiedMessage,
    ProxyTypes,
    System,
)
from ._util import ConsumeFragmentsResult, consume_fragments_to_match_proxy


def detect_proxy_in_message(system: System, fragments: list[Fragment]) -> DetectionResult[Fragment] | None:
    """
    Identifies if a configured proxy was used for this message.
    You generally shouldn't need to call this directly, and should use
    get_proxied_message instead since it takes autoproxies into consideration.
    """
    # Build the list of proxies to check against, with longest and
    # case-sensitive proxies prioritized first
    proxies = [(proxy, member) for member in system['members'] for proxy in member['proxies']]
    proxies.sort(
        key=lambda t: (len(t[0]['text']), t[1]['case_sensitive']),
        reverse=True,
    )

    # Search for a match
    for proxy, member in proxies:
        result: ConsumeFragmentsResult[Fragment] | None = None

        if proxy['type'] in [ProxyTypes.PREFIX, ProxyTypes.EITHER_SIDE]:
            result = consume_fragments_to_match_proxy(fragments, proxy, 'prefix', member)

        if not result and proxy['type'] in [ProxyTypes.SUFFIX, ProxyTypes.EITHER_SIDE]:
            result = consume_fragments_to_match_proxy(fragments, proxy, 'suffix', member)

        if result:
            return {
                **result,
                'proxy_used': proxy,
                'member': member,
            }


def get_proxied_message(system: System | None, message: str | list[Fragment]) -> ProxiedMessage[Fragment] | None:
    """
    Checks if a proxy applies to this message, and if so, returns information
    about the member and their preferences. Also includes clean versions of the
    message with the proxy removed, ready for display.
    """
    if not system:
        return

    # Start with the system's autoproxy, if one is set
    member: Member | None = None
    if auto_id := system['autoproxy_member_id']:
        member = next((m for m in system['members'] if m['id'] == auto_id), None)

    # Let's see if the user used a proxy
    fragments: list[Fragment] = (
        cast('list[Fragment]', [{'type': 'text', 'text': message}]) if isinstance(message, str) else message
    )
    if detection := detect_proxy_in_message(system, fragments):
        member = detection['member']

    # Check if we ended up with a member
    if not member:
        return

    # Compile the clean message body
    target_fragments = detection['clean_fragments'] if detection else fragments
    body = ''.join(f.get('text') or '' for f in target_fragments)

    return {
        'member': member,
        'system': system,
        'color': member['color'] or system['color'],
        'pronouns': member['pronouns'] or system['pronouns'],
        'proxy_used': detection['proxy_used'] if detection else None,
        'clean_fragments': target_fragments,
        'changed_fragments': detection['changed_fragments'] if detection else {},
        'body': body,
    }
