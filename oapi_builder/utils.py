import re


def add_schemas(api_spec, schemas):
    for schema in schemas:
        api_spec.components.schema(schema.__name__)


def snake_to_camelback(str_obj: str) -> str:
    return re.sub(r'_([a-z])', lambda x: x.group(1).upper(), str_obj)
