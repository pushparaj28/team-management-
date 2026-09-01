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