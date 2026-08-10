import re
from typing import Literal, TypedDict

from ._types import KNOWN_FRAGMENT_TYPES, FragmentTypes, Member, MessageFragment, Proxy

# Match JavaScript's \S implementation for consistency
non_whitespace_regex = re.compile(r'[^\s\ufeff]')

mention_regex = re.compile(r'^@\w{4,25} ')


class ConsumeFragmentsResult[Fragment: MessageFragment](TypedDict):
    clean_fragments: list[Fragment]
    changed_fragments: dict[int, Fragment | None]


def consume_fragments_to_match_proxy[Fragment: MessageFragment](
    fragments: list[Fragment],
    proxy: Proxy,
    kind: Literal['prefix', 'suffix'],
    member: Member,
) -> ConsumeFragmentsResult[Fragment] | None:
    # Keep a reference to the original fragments so we can use them later
    source_fragments = fragments

    # Start with the full proxy text so we can keep track of what we're still
    # looking for as we match parts of it
    remaining_proxy = proxy['text']
    if member['require_space']:
        remaining_proxy = f'{proxy["text"]} ' if kind == 'prefix' else f' {proxy["text"]}'

    # Flip everything around if we're trying to detect a suffix
    if kind == 'suffix':
        remaining_proxy = remaining_proxy[::-1]
        fragments = reverse_fragments(fragments)

    # Prepare configurable case-insensitive text matching
    def startswith(text: str, prefix: str) -> bool:
        if member['case_sensitive']:
            return text.startswith(prefix)
        return text.lower().startswith(prefix.lower())

    # Search through the fragments checking that our proxy text matches
    changed_fragments: dict[int, Fragment | None] = {}
    found_first_text = False
    matched = False
    for idx, fragment in enumerate(fragments):
        # Bail out as soon as we hit a fragment type that we don't recognize
        if fragment['type'] not in KNOWN_FRAGMENT_TYPES:
            return

        # All known fragment types that we're working with are expected to have
        # a text property, so let the type checker know it's safe to access it
        if 'text' not in fragment or not isinstance(fragment['text'], str):
            return

        # Ignore mention fragments at the start of the message (Twitch adds
        # these when replying to someone)
        if kind == 'prefix' and idx == 0 and fragment['type'] == FragmentTypes.MENTION:
            continue

        # Ignore any completely empty fragments
        if not fragment['text']:
            continue

        # Determine which part of this fragment should be looked at
        # (If we haven't found any text yet, we jump over leading whitespace to
        # get to the first non-whitespace character)
        first_character_idx = 0
        if not found_first_text:
            if match := non_whitespace_regex.search(fragment['text']):
                first_character_idx = match.start()
            else:
                # This fragment is only whitespace, ignore it
                continue

        # Get the text from the fragment (ignoring any leading whitespace if
        # this is the first non-whitespace fragment we've run into)
        true_text = fragment['text'][first_character_idx:]
        found_first_text = True

        # If this is the first fragment, skip over a leading mention (since
        # mentions are sometimes found in text fragments depending on the
        # implementation)
        if (
            kind == 'prefix'
            and idx == 0
            and fragment['type'] == FragmentTypes.TEXT
            and (mention_match := mention_regex.match(true_text))
        ):
            first_character_idx += mention_match.end()
            true_text = true_text[mention_match.end() :]

        # Check if this fragment has enough text to finish our proxy
        if len(true_text) >= len(remaining_proxy):
            # Stop if the fragment doesn't match what we were expecting to find
            if not startswith(true_text, remaining_proxy):
                return

            # We theoretically have a match! Let's make sure this wouldn't
            # result in breaking up an emote
            if len(true_text) > len(remaining_proxy) and fragment['type'] == FragmentTypes.EMOTE:
                return

            # We have a match! Update the fragment to remove the proxy text
            changed_fragments[idx] = (
                None
                if fragment['type'] == FragmentTypes.EMOTE
                else with_text(fragment, fragment['text'][:first_character_idx] + true_text[len(remaining_proxy) :])
            )
            matched = True
            break
        else:
            # Our remaining proxy is longer than this fragment, let's see if
            # what we do have matches
            if not startswith(remaining_proxy, true_text):
                return

            # It matches so far, let's consume this fragment and keep going
            remaining_proxy = remaining_proxy[len(true_text) :]
            changed_fragments[idx] = (
                None
                if fragment['type'] == FragmentTypes.EMOTE
                else with_text(fragment, fragment['text'][:first_character_idx])
            )

    if not matched:
        return

    # Flip the changed data back around if we found a suffix match
    if kind == 'suffix':
        changed_fragments = {
            len(fragments) - 1 - idx: (
                with_text(fragment, text[::-1]) if fragment and (text := fragment.get('text')) else fragment
            )
            for idx, fragment in changed_fragments.items()
        }

    return {
        'changed_fragments': changed_fragments,
        'clean_fragments': [
            f
            for idx, fragment in enumerate(source_fragments)
            if (f := changed_fragments.get(idx, fragment)) is not None
        ],
    }


def reverse_fragments[Fragment: MessageFragment](fragments: list[Fragment]) -> list[Fragment]:
    rev: list[Fragment] = []
    for f in reversed(fragments):
        fragment = f.copy()
        if text := fragment.get('text'):
            fragment['text'] = text[::-1]
        rev.append(fragment)
    return rev


def with_text[Fragment: MessageFragment](fragment: Fragment, text: str) -> Fragment:
    revised = fragment.copy()
    revised['text'] = text
    return revised
