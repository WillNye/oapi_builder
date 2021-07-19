from logging import getLogger

LOGGER = getLogger(__file__)


def validate(value, expected_type):
    if isinstance(value, dict):
        for k, v in expected_type._alias_map.items():
            if alias_val := value.pop(k, None):
                value[expected_type._alias_map[k]] = alias_val

        try:
            value = expected_type(**value)
        except (TypeError, ValueError) as err:
            LOGGER.exception(f'{expected_type.__class__.__name__} : {value} - {str(err)}')
            raise
    elif isinstance(value, OAPIObjectAttr):
        return value
    elif not isinstance(value, expected_type):
        raise TypeError(f"{value} must be a {expected_type} instance or it's dict representation.")

    return value.to_dict()


class OAPIObjectList(list):
    object_type = None

    def append(self, value) -> None:
        if not self.object_type:
            raise NotImplementedError('An Object type has not been defined for this list')
        super(OAPIObjectList, self).append(validate(value, self.object_type))


class OAPIObjectAttr:
    def __init__(self, object_type, is_map: bool = False):
        """
        :param object_type: The uninitialized class the attribute expects
        :param is_map: If True, the value is meant to represent the OAPI object, not the entire value.
                        An example of this is Operation.Responses = {Response.status_code: Response}
        """
        self.object_type = object_type
        self.is_map = is_map

    def __set_name__(self, owner, name):
        self.name = name
        if self.is_map:
            self.__dict__[name] = {}

    def __get__(self, instance, owner):
        if not instance: return self
        return instance.__dict__.get(self.name, instance.__dict__)

    def __delete__(self, instance):
        del instance.__dict__[self.name]

    def __set__(self, instance, value):
        if not isinstance(value, OAPIObjectAttr):
            if self.is_map:
                instance.__dict__[self.name] = {k: validate(v, self.object_type) for k, v in value.items()}
            else:
                instance.__dict__[self.name] = validate(value, self.object_type)
        else:
            instance.__dict__[self.name] = value

    def __setitem__(self, key, value):

        self.__dict__[self.name][key] = validate(value, self.object_type)

    def __setattr__(self, key, value):
        if key in ('object_type', 'is_map', 'name'):
            self.__dict__[key] = value
        else:
            self.__dict__[self.name][key] = value

    def __repr__(self):
        if obj_val := self.__dict__.get(self.name):
            return repr(obj_val)
        else:
            return super(OAPIObjectAttr, self).__repr__()

    def __str__(self):
        if obj_val := self.__dict__.get(self.name):
            return repr(obj_val)
        else:
            return super(OAPIObjectAttr, self).__repr__()

    def __bool__(self):
        return bool(getattr(self, self.__dict__.get('name', 'Unknown'), False))

    def items(self):
        return getattr(self, self.name).items()

    def values(self):
        return getattr(self, self.name).values()


class OAPIObjectListAttr(OAPIObjectAttr):

    def __set__(self, instance, value: list):
        if not isinstance(value, OAPIObjectListAttr):
            instance.__dict__[self.name] = OAPIObjectList(validate(v, self.object_type) for v in value)
        else:
            instance.__dict__[self.name] = instance.__dict__.get(self.name, OAPIObjectList())

        instance.__dict__[self.name].object_type = self.object_type

