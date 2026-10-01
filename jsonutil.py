"""JSON utilities for Merestone: canonical encoding, strict reading/writing and the schema subset used by the contracts."""
import json
import math
import re
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode('utf-8')


def read_json(path):
    path = Path(path)
    if path.stat().st_size > 10_000_000:
        raise ValueError('File exceeds 10 MB')
    def pairs(items):
        result = {}
        for key, val in items:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = val
        return result
    def invalid(value):
        raise ValueError('Non-finite JSON number: ' + value)
    return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=pairs, parse_constant=invalid)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def validate(value, schema, loc='$'):
    """Explicit subset of JSON Schema used by the package contracts."""
    if 'anyOf' in schema:
        for branch in schema['anyOf']:
            try:
                validate(value, branch, loc)
                break
            except ValueError:
                pass
        else:
            raise ValueError(f'{loc}: no schema alternative matches')
    kinds = {'object': dict, 'array': list, 'string': str, 'integer': int, 'boolean': bool, 'null': type(None)}
    kind = schema.get('type')
    if kind and type(value) is not kinds[kind]:
        raise ValueError(f'{loc}: expected {kind}')
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError(f'{loc}: value not allowed')
    if isinstance(value, dict):
        for key in schema.get('required', []):
            if key not in value:
                raise ValueError(f'{loc}: missing {key}')
        props = schema.get('properties', {})
        if schema.get('additionalProperties') is False and set(value) - set(props):
            raise ValueError(f'{loc}: properties not allowed')
        for key, child in props.items():
            if key in value:
                validate(value[key], child, loc + '.' + key)
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0) or len(value) > schema.get('maxItems', math.inf):
            raise ValueError(f'{loc}: invalid size')
        if schema.get('uniqueItems') and len({canonical(x) for x in value}) != len(value):
            raise ValueError(f'{loc}: duplicate items')
        for i, child in enumerate(value):
            validate(child, schema.get('items', {}), f'{loc}[{i}]')
    if isinstance(value, str):
        if len(value.strip()) < schema.get('minLength', 0):
            raise ValueError(f'{loc}: empty string')
        if 'pattern' in schema and not re.search(schema['pattern'], value):
            raise ValueError(f'{loc}: invalid pattern')
    if type(value) is int:
        if value < schema.get('minimum', -math.inf) or value > schema.get('maximum', math.inf):
            raise ValueError(f'{loc}: integer out of range')
