from importlib.metadata import version

from ._client import AsyncPluralmindClient
from ._config import PluralmindConfig, config
from ._service import detect_proxy_in_message, get_proxied_message
from ._types import (
    CacheHit,
    DetectionResult,
    FragmentTypes,
    Member,
    MessageFragment,
    MessageFragmentType,
    ProxiedMessage,
    Proxy,
    ProxyType,
    ProxyTypes,
    System,
    TwitchId,
)

__all__ = [
    'AsyncPluralmindClient',
    'CacheHit',
    'DetectionResult',
    'FragmentTypes',
    'Member',
    'MessageFragment',
    'MessageFragmentType',
    'PluralmindConfig',
    'ProxiedMessage',
    'Proxy',
    'ProxyType',
    'ProxyTypes',
    'System',
    'TwitchId',
    'config',
    'detect_proxy_in_message',
    'get_proxied_message',
]

__version__ = version('pluralmind')
