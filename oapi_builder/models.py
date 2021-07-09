from dataclasses import dataclass
from http import HTTPStatus
from collections import OrderedDict

from oapi_builder.mixins import ContentMixin, HeaderMixin, ParameterMixin


class BaseObject:
    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in dir(self)
                if not k.startswith('_') and not callable(getattr(self, k)) and getattr(self, k)}


@dataclass
class ResponseObject(BaseObject, ContentMixin, HeaderMixin):
    """
    https://swagger.io/specification/#response-object
    """
    status_code: int
    description: str = ""
    tags = []
    links = []  # https://swagger.io/specification/#link-object

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
        status_list.sort()
        res_obj = list()
        for s in HTTPStatus:
            if s.value in status_list:
                res_obj.append(ResponseObject(status_code=s.value, description=s.phrase))
        return res_obj


@dataclass
class OperationObject(BaseObject, ParameterMixin):
    """
    https://swagger.io/specification/#operation-object
    """
    description: str
    tags = []
    _responses = {}

    @property
    def responses(self):
        return self._responses

    def upsert_responses(self, responses: list):
        assert all(isinstance(r, ResponseObject) for r in responses)
        responses = {str(r.status_code): r.to_dict() for r in responses} | self._responses
        self._responses = OrderedDict(sorted(responses.items()))

