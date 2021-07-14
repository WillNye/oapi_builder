import re
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import List
from collections import OrderedDict

from oapi_builder.mixins import ContentMixin, HeaderMixin, ParameterMixin


def snake_to_camelback(str_obj: str) -> str:
    return re.sub(r'_([a-z])', lambda x: x.group(1).upper(), str_obj)


class BaseObject:
    _is_camelback = True

    def to_dict(self) -> dict:
        return {snake_to_camelback(k) if self._is_camelback else k: getattr(self, k) for k in dir(self)
                if not k.startswith('_') and not callable(getattr(self, k)) and getattr(self, k)}


@dataclass
class RequestBodyObject(BaseObject, ContentMixin):
    """
    https://swagger.io/specification/#request-body-object
    """
    description: str = field(default=None)
    required: bool = False


@dataclass
class ResponseObject(BaseObject, ContentMixin, HeaderMixin):
    """
    https://swagger.io/specification/#response-object
    """
    _is_camelback = False

    status_code: int
    description: str = field(default=None)
    tags: List = field(default_factory=lambda: [])
    links: List = field(default_factory=lambda: [])  # https://swagger.io/specification/#link-object

    def __post_init__(self):
        if not self.description:
            self.description = HTTPStatus(self.status_code).phrase

    def to_dict(self) -> dict:
        res_obj = super(ResponseObject, self).to_dict()
        res_obj.pop('status_code', None)
        return res_obj

    @classmethod
    def get_defaults(cls, status_list: list) -> list:
        assert all(isinstance(status, int) for status in status_list)
        res_obj = list()
        for s in HTTPStatus:
            if s.value in status_list:
                res_obj.append(ResponseObject(status_code=s.value, description=s.phrase))
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
    _in: str = field(default=None, metadata=dict(field_name="in"))
    flows: dict = field(default_factory=lambda: {})

    def __post_init__(self):
        assert self.type in ["apiKey", "http", "oauth2", "openIdConnect"]
        if self.type == 'apiKey':
            assert self.name
            assert self._in in ['query', 'header', 'cookie']
        elif self.type == 'http':
            assert self.scheme
        elif self.type == 'oath2':
            assert self.flows
        elif self.type == 'openIdConnect':
            assert self.openIdConnectUrl


@dataclass
class OperationObject(BaseObject, ParameterMixin):
    """
    https://swagger.io/specification/#operation-object
    """
    description: str
    summary: str = field(default=None)
    tags: List = field(default_factory=lambda: [])
    security: List = field(default_factory=lambda: [])
    deprecated: bool = field(default=False)
    _request_body: dict = field(default_factory=lambda: {}, init=False)
    _responses: dict = field(default_factory=lambda: {}, init=False)

    @property
    def responses(self):
        return self._responses

    @property
    def request_body(self):
        return self._request_body

    def set_request_body(self, request_body):
        self._request_body = request_body.to_dict() if isinstance(request_body, RequestBodyObject) else request_body

    def upsert_responses(self, responses: list):
        assert all(isinstance(r, ResponseObject) for r in responses)
        responses = {str(r.status_code): r.to_dict() for r in responses} | self._responses
        self._responses = OrderedDict(sorted(responses.items()))

