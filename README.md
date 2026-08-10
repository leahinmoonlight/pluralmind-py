# pluralmind-py

Pluralmind allows plural folks to share which of their system members is sending a message on Twitch. You can learn more about Pluralmind over at [pluralmind.chat](https://pluralmind.chat).

This library is designed to make it fast and simple to add plurality support to your own Python projects (such as TwitchIO bots, custom Twitch tools, etc.).

If you want to add Pluralmind to web-based projects such as chat widgets, check out our [JavaScript library](https://github.com/leahinmoonlight/pluralmind).

[![pypi version](https://img.shields.io/pypi/v/pluralmind?color=ff69b4)](https://pypi.org/project/pluralmind/) [![license](https://img.shields.io/pypi/l/pluralmind?color=ff69b4)](https://github.com/leahinmoonlight/pluralmind-py/blob/main/LICENSE)
[![Pyright Strict](https://img.shields.io/badge/Pyright-Strict-ff69b4)](https://github.com/leahinmoonlight/pluralmind-py/blob/main/pyproject.toml)

## Guides and References

We're still working on our Python documentation, but you may still want to reference the [Pluralmind Docs](https://docs.pluralmind.chat/) for guides, as well as a full [API Reference](https://docs.pluralmind.chat/api/).

This Python library is a very close port of the JavaScript one, so most of the concepts and types still apply.

## Installation

With pip (or your favorite package manager):

```bash
pip install pluralmind
```

(Note: Python 3.12+ is required. Everything is fully typed~!)

## Integrating Pluralmind

<!-- fmt: off -->
```python
from pluralmind import AsyncPluralmindClient, get_proxied_message

client = AsyncPluralmindClient()

# Let's imagine a new message just came in from someone!
# We'll start by pulling up their system's information. You can pass in their numeric Twitch user ID, or their username/handle.
system = await client.get_system('leahinmoonlight')

# Great! Now let's see if this is a proxied message.
pm = get_proxied_message(system, 'L: hihi chat~')
if pm:
    print(pm['member']['name'])  # "Leah"
    print(pm['color'])           # "#eb97ca"
    print(pm['pronouns'])        # "she/her"
    print(pm['body'])            # "hihi chat~" (the proxy was removed)
    # That's it! You can use this data to address this member appropriately.
```
<!-- fmt: on -->

> [!IMPORTANT]
> Be sure to reuse one `AsyncPluralmindClient` instance, rather than creating a new one every time. This will ensure cache management works properly.
