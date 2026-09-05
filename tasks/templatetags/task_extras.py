import json
from django import template 
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, [])

@register.filter
def safe_json(value):
    """Serialize a Python object for safe inline use in an onclick attribute."""
    def item_style(event_type):
        return {
            'task': ('bg-rose-50 text-rose-700', 'bg-rose-400'),
            'milestone': ('bg-amber-50 text-amber-700', 'bg-amber-400'),
            'leave': ('bg-blue-50 text-blue-700', 'bg-blue-400'),
            'event': ('bg-indigo-50 text-indigo-700', 'bg-indigo-500'),
        }.get(event_type, ('bg-gray-50 text-gray-700', 'bg-gray-400'))

    enriched = []
    for item in value:
        cls, dot = item_style(item.get('type'))
        enriched.append({'label': item.get('label', ''), 'sub': item.get('sub', ''), 'cls': cls, 'dot': dot})
    return mark_safe(json.dumps(enriched).replace("'", "\\'"))

@register.filter
def abs_val(value):
    return abs(value)

_AVATAR_PALETTE = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#0ea5e9', '#ef4444', '#14b8a6']

@register.filter
def avatar_color(username):
    if not username:
        return '#9ca3af'
    return _AVATAR_PALETTE[sum(ord(c) for c in username) % len(_AVATAR_PALETTE)]