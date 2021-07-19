import mimetypes
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import List

from oapi_builder.utils import snake_to_camelback
from oapi_builder.fields import OAPIObjectAttr, OAPIObjectListAttr


class BaseObject:
    _is_camelback = True
    _alias_map = dict()

    def to_dict(self) -> dict:
        return {snake_to_camelback(k) if self._is_camelback else k: getattr(self, k) for k in dir(self)
                if not k.startswith('_') and not callable(getattr(self, k)) and getattr(self, k)}

    @classmethod
    def dump(cls, value):
        if isinstance(value, dict):
            value = cls(**value)
        elif not isinstance(value, cls):
            raise TypeError(f"Must be an {cls.__name__} instance or it's dict representation.")

        return value.to_dict()


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
    _alias_map = {'in': 'parameter_in'}

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
    schema: any = field(default='')
    example: any = field(default=None)
    examples: dict = field(default=None)
    content_type: str = field(default='application/json')
    _valid_content_types = {content_type: True for content_type in mimetypes.types_map.values()}
    _alias_map = {'type': 'content_type'}

    def __post_init__(self):
        assert self._valid_content_types.get(self.content_type, False)
        self.schema = self.schema if isinstance(self.schema, str) else self.schema.__name__

    def to_dict(self) -> dict:
        response = super(ContentObject, self).to_dict()
        return {response.pop('contentType'): response}


@dataclass
class HeaderObject:
    """
    https://swagger.io/specification/#header-object
    """
    description: str = field(default=None)
    schema: any = field(default='')


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
    variables: dict = OAPIObjectAttr(ServerVariableObject, is_map=True)


@dataclass
class RequestBodyObject(BaseObject):
    """
    https://swagger.io/specification/#request-body-object
    """
    description: str = field(default=None)
    required: bool = False
    content: dict = OAPIObjectAttr(ContentObject)


@dataclass
class LinkObject(BaseObject):
    """
    https://swagger.io/specification/#link-object

    tags: list(str)
    security: list(dict(component_security_scheme_key=list(f'{operation}:{tag}')))
    """
    operation_id: str = field(default=None)
    operation_ref: str = field(default=None)
    description: str = field(default=None)
    parameters: List = OAPIObjectListAttr(ParameterObject)
    request_body: dict = OAPIObjectAttr(RequestBodyObject)
    server: dict = OAPIObjectAttr(ServerObject)


@dataclass
class ResponseObject(BaseObject):
    """
    https://swagger.io/specification/#response-object

    tags: list(str)
    """
    _is_camelback = False

    status_code: int
    description: str = field(default=None)
    tags: List = field(default_factory=lambda: [])
    links: List = OAPIObjectListAttr(LinkObject)
    content: dict = OAPIObjectAttr(ContentObject)
    headers: dict = OAPIObjectAttr(HeaderObject, is_map=True)

    def __post_init__(self):
        if not self.description:
            self.description = HTTPStatus(self.status_code).phrase

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
        del(res_obj['status_code'])
        return res_obj


@dataclass
class OAuthFlowObject(BaseObject):
    """
    https://swagger.io/specification/#oauth-flow-object
    """
    scopes: dict
    authorization_url: str = field(default=None)
    refresh_url: str = field(default=None)
    token_url: str = field(default=None)
    content: dict = OAPIObjectAttr(ContentObject)

    def to_dict(self) -> dict:
        response = super(OAuthFlowObject, self).to_dict()
        response.setdefault('scopes', {})
        return response


@dataclass
class OAuthFlowsObject(BaseObject):
    """
    https://swagger.io/specification/#oauth-flows-object
    """
    authorization_code: dict = field(default_factory=lambda: {})
    client_credentials: dict = field(default_factory=lambda: {})
    implicit: dict = field(default_factory=lambda: {})
    password: dict = field(default_factory=lambda: {})
    content: dict = OAPIObjectAttr(ContentObject)

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
class SecuritySchemeObject(BaseObject):
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
    parameters: List = OAPIObjectListAttr(ParameterObject)

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
class OperationObject(BaseObject):
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
    request_body: dict = OAPIObjectAttr(RequestBodyObject)
    responses: dict = OAPIObjectAttr(ResponseObject, is_map=True)
    parameters: List = OAPIObjectListAttr(ParameterObject)

    def upsert_responses(self, responses: list):
        for r in list(responses):
            self.responses[str(r.__dict__['status_code'])] = r
