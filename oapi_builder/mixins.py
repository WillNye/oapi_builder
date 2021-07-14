from dataclasses import dataclass, field
from typing import List


@dataclass
class HeaderMixin:
    """
    https://swagger.io/specification/#header-object
    """
    _headers: dict = field(default_factory=lambda: {}, init=False)

    @property
    def headers(self):
        return self._headers

    def append_headers(self, name, description, schema):
        self._headers[name] = dict(description=description, schema=schema)


@dataclass
class ParameterMixin:
    """
    https://swagger.io/specification/#parameter-object
    """
    _parameters: List = field(default_factory=lambda: [], init=False)

    def add_parameter(self, schema, name: str, required: bool = True, param_in: str = 'path', **kwargs):
        """
        https://swagger.io/specification/#parameter-object
        """
        self._parameters.append({'in': param_in, 'schema': schema, 'name': name, 'required': required} | kwargs)

    @property
    def parameters(self):
        return self._parameters


@dataclass
class ContentMixin:
    """
    https://swagger.io/specification/#media-type-object
    """
    _content: dict = field(default_factory=lambda: {}, init=False)

    def set_content(self, schema, example, content_type: str = 'application/json', examples: dict = None):
        """
        examples: dict(obj_ref=ExampleObject)
        https://swagger.io/specification/#example-object
        """
        content = dict(schema=schema if isinstance(schema, str) else schema.__name__, example=example)
        if examples:
            content['examples'] = examples
        self._content = {content_type: content}

    @property
    def content(self):
        return self._content
