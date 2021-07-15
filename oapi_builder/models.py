import mimetypes
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import List
from collections import OrderedDict

from oapi_builder.utils import snake_to_camelback


class BaseObject:
    _is_camelback = True

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

        super(BaseObject, self).__init__(*args)

    def to_dict(self) -> dict:
        return {snake_to_camelback(k) if self._is_camelback else k: getattr(self, k) for k in dir(self)
                if not k.startswith('_') and not callable(getattr(self, k)) and getattr(self, k)}


@dataclass
class ParameterObject(BaseObject):
    """
    https://swagger.io/specification/#parameter-object
    """
    name: str
    schema: any = field(default=None)
    parameter_in: str = field(default='path')
    description: str = field(default=None)
    required: bool = field(default=None)
    deprecated: bool = field(default=False)
    allow_empty_value: bool = field(default=False)

    def __post_init__(self):
        assert self.parameter_in in ["query", "header", "path", "cookie"]
        self.required = self.required or bool(self.parameter_in == 'path')

    def to_dict(self) -> dict:
        response = super(ParameterObject, self).to_dict()
        response['in'] = response.pop('parameterIn')
        if self.schema:
            response['schema'] = self.schema

        return response


@dataclass
class ContentObject(BaseObject):
    """
    https://swagger.io/specification/#media-type-object
    https://swagger.io/specification/#example-object
    examples: dict(obj_ref=ExampleObject)
    """
    _valid_content_types = {content_type: True for content_type in mimetypes.types_map.values()}
    schema: any = field(default='')
    example: dict = field(default=None)
    examples: dict = field(default=None)
    content_type: str = field(default='application/json')

    def __post_init__(self):
        assert self._valid_content_types.get(self.content_type, False)
        self.schema = self.schema if isinstance(self.schema, str) else self.schema.__name__

    def to_dict(self) -> dict:
        response = super(ContentObject, self).to_dict()
        return {response.pop('contentType'): response}


@dataclass
class ParameterMixin:
    _parameters: List = field(default_factory=lambda: [], init=False)

    @property
    def parameters(self):
        return self._parameters

    @parameters.setter
    def parameters(self, parameters):
        self._parameters = [p.to_dict() if isinstance(p, ParameterObject) else p for p in parameters]


@dataclass
class ContentMixin:
    """
    https://swagger.io/specification/#media-type-object
    """
    _content: dict = field(default_factory=lambda: {}, init=False)

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, val):
        self._content = val.to_dict() if isinstance(val, ContentObject) else val


@dataclass
class HeaderMixin:
    """
    https://swagger.io/specification/#header-object
    """
    _headers: dict = field(default_factory=lambda: {}, init=False)

    @property
    def headers(self):
        return self._headers

    def upsert_headers(self, name, description, schema):
        self._headers[name] = dict(description=description, schema=schema)


@dataclass
class ServerVariableObject(BaseObject):
    """
    https://swagger.io/specification/#server-variable-object

    enum: list(str) - An enumeration of string values to be used if the substitution options are from a limited set.
        Example:
            port:
              enum:
                - '8443'
                - '443'
              default: '8443'
    """
    default: str
    description: str = field(default=None)
    enum: List = field(default_factory=lambda: [])


@dataclass
class ServerObject(BaseObject):
    """
    https://swagger.io/specification/#server-object
    """
    url: str
    description: str = field(default=None)
    _variables: dict = field(default_factory=lambda: {}, init=False)

    @property
    def variables(self):
        return self._variables

    def upsert_variable(self, name: str, server_var: ServerVariableObject):
        self._variables[name] = server_var.to_dict() if isinstance(server_var, ServerVariableObject) else server_var


@dataclass
class RequestBodyObject(BaseObject, ContentMixin):
    """
    https://swagger.io/specification/#request-body-object
    """
    description: str = field(default=None)
    required: bool = False


@dataclass
class LinkObject(BaseObject, ParameterMixin):
    """
    https://swagger.io/specification/#link-object

    tags: list(str)
    security: list(dict(component_security_scheme_key=list(f'{operation}:{tag}')))
    """
    operation_id: str = field(default=None)
    operation_ref: str = field(default=None)
    description: str = field(default=None)
    _server: dict = field(default_factory=lambda: {})
    _request_body: dict = field(default_factory=lambda: {})

    @property
    def request_body(self):
        return self._request_body

    @request_body.setter
    def request_body(self, request_body: RequestBodyObject):
        self._request_body = request_body.to_dict() if isinstance(request_body, RequestBodyObject) else request_body

    @property
    def server(self):
        return self._server

    @server.setter
    def server(self, server: ServerObject):
        self._server = server.to_dict() if isinstance(server, ServerObject) else server


@dataclass
class ResponseObject(BaseObject, ContentMixin, HeaderMixin):
    """
    https://swagger.io/specification/#response-object

    tags: list(str)
    """
    _is_camelback = False

    status_code: int
    description: str = field(default=None)
    tags: List = field(default_factory=lambda: [])
    _links: List = field(default_factory=lambda: [])

    def __post_init__(self):
        if not self.description:
            self.description = HTTPStatus(self.status_code).phrase

    @property
    def links(self):
        return self._links

    @links.setter
    def links(self, links):
        self._links = [link.to_dict() if isinstance(link, LinkObject) else link for link in links]

    @classmethod
    def get_defaults(cls, status_list: list) -> list:
        assert all(isinstance(status, int) for status in status_list)
        res_obj = list()
        for s in HTTPStatus:
            if s.value in status_list:
                res_obj.append(ResponseObject(status_code=s.value, description=s.phrase))
        return res_obj

    def to_dict(self) -> dict:
        res_obj = super(ResponseObject, self).to_dict()
        res_obj.pop('status_code', None)
        return res_obj


@dataclass
class OAuthFlowObject(BaseObject, ContentMixin):
    """
    https://swagger.io/specification/#oauth-flow-object
    """
    scopes: dict
    authorization_url: str = field(default=None)
    refresh_url: str = field(default=None)
    token_url: str = field(default=None)

    def to_dict(self) -> dict:
        response = super(OAuthFlowObject, self).to_dict()
        response.setdefault('scopes', {})
        return response


@dataclass
class OAuthFlowsObject(BaseObject, ContentMixin):
    """
    https://swagger.io/specification/#oauth-flows-object
    """
    authorization_code: dict = field(default_factory=lambda: {})
    client_credentials: dict = field(default_factory=lambda: {})
    implicit: dict = field(default_factory=lambda: {})
    password: dict = field(default_factory=lambda: {})

    def __post_init__(self):
        if self.authorization_code:
            assert self.authorization_code.get('authorizationUrl')
            assert self.authorization_code.get('tokenUrl')
        if self.implicit:
            assert self.implicit.get('authorizationUrl')
        if self.client_credentials:
            assert self.client_credentials.get('tokenUrl')
        if self.password:
            assert self.password.get('tokenUrl')


@dataclass
class SecuritySchemeObject(BaseObject, ParameterMixin):
    """
    https://swagger.io/specification/#security-scheme-object
    """
    type: str = field()
    description: str = field(default=None)
    bearer_format: str = field(default=None)
    scheme: str = field(default=None)
    open_id_connect_url: str = field(default=None)
    name: str = field(default=None)
    flows: dict = field(default_factory=lambda: {})
    key_in: str = field(default=None)

    def __post_init__(self):
        assert self.type in ["apiKey", "http", "oauth2", "openIdConnect"]
        if self.type == 'apiKey':
            assert self.name
            assert self.key_in in ['query', 'header', 'cookie']
        elif self.type == 'http':
            assert self.scheme
        elif self.type == 'oath2':
            assert self.flows
        elif self.type == 'openIdConnect':
            assert self.openIdConnectUrl

    def to_dict(self) -> dict:
        response = super(SecuritySchemeObject, self).to_dict()
        if self.key_in:
            response['in'] = response.pop('keyIn')
        return response


@dataclass
class OperationObject(BaseObject, ParameterMixin):
    """
    https://swagger.io/specification/#operation-object

    tags: list(str)
    security: list(dict(component_security_scheme_key=list(f'{operation}:{tag}')))
    """
    description: str
    summary: str = field(default=None)
    tags: List = field(default_factory=lambda: [])
    security: List = field(default_factory=lambda: [])
    deprecated: bool = field(default=False)
    _request_body: dict = field(default_factory=lambda: {}, init=False)
    _responses: dict = field(default_factory=lambda: {}, init=False)

    @property
    def request_body(self):
        return self._request_body

    @request_body.setter
    def request_body(self, request_body):
        self._request_body = request_body.to_dict() if isinstance(request_body, RequestBodyObject) else request_body

    @property
    def responses(self):
        return self._responses

    def upsert_responses(self, responses: list):
        responses = {str(r.status_code): r.to_dict() if isinstance(r, ResponseObject) else r
                     for r in list(responses)} | self._responses
        self._responses = OrderedDict(sorted(responses.items()))

