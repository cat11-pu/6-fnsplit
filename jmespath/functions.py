from jmespath import exceptions
from jmespath.compat import get_methods
from jmespath.fn_strings import StringFunctionsMixin
from jmespath.fn_collections import CollectionFunctionsMixin
from jmespath.fn_utils import signature


# python types -> jmespath types
TYPES_MAP = {
    'bool': 'boolean',
    'list': 'array',
    'dict': 'object',
    'NoneType': 'null',
    'unicode': 'string',
    'str': 'string',
    'float': 'number',
    'int': 'number',
    'long': 'number',
    'OrderedDict': 'object',
    '_Projection': 'array',
    '_Expression': 'expref',
}


# jmespath types -> python types
REVERSE_TYPES_MAP = {
    'boolean': ('bool',),
    'array': ('list', '_Projection'),
    'object': ('dict', 'OrderedDict',),
    'null': ('NoneType',),
    'string': ('unicode', 'str'),
    'number': ('float', 'int', 'long'),
    'expref': ('_Expression',),
}


class FunctionRegistry(type):
    def __init__(cls, name, bases, attrs):
        cls._populate_function_table()
        super(FunctionRegistry, cls).__init__(name, bases, attrs)

    def _populate_function_table(cls):
        function_table = {}
        # Any method with a @signature decorator that also
        # starts with "_func_" is registered as a function.
        # _func_max_by -> max_by function.
        for name, method in get_methods(cls):
            if not name.startswith('_func_'):
                continue
            sig = getattr(method, 'signature', None)
            if sig is not None:
                function_table[name[6:]] = {
                    'function': method,
                    'signature': sig,
                }
        cls.FUNCTION_TABLE = function_table


class Functions(StringFunctionsMixin, CollectionFunctionsMixin,
                metaclass=FunctionRegistry):

    FUNCTION_TABLE = {
    }

    def call_function(self, function_name, resolved_args):
        try:
            spec = self.FUNCTION_TABLE[function_name]
        except KeyError:
            raise exceptions.UnknownFunctionError(
                "Unknown function: %s()" % function_name)
        function = spec['function']
        sig = spec['signature']
        self._validate_arguments(resolved_args, sig, function_name)
        return function(self, *resolved_args)

    def _validate_arguments(self, args, sig, function_name):
        if sig and sig[-1].get('variadic'):
            if len(args) < len(sig):
                raise exceptions.VariadictArityError(
                    len(sig), len(args), function_name)
        elif len(args) != len(sig):
            raise exceptions.ArityError(
                len(sig), len(args), function_name)
        return self._type_check(args, sig, function_name)

    def _type_check(self, actual, sig, function_name):
        for i in range(len(sig)):
            allowed_types = sig[i]['types']
            if allowed_types:
                self._type_check_single(actual[i], allowed_types,
                                        function_name)

    def _type_check_single(self, current, types, function_name):
        # Type checking involves checking the top level type,
        # and in the case of arrays, potentially checking the types
        # of each element.
        allowed_types, allowed_subtypes = self._get_allowed_pytypes(types)
        # We're not using isinstance() on purpose.
        # The type model for jmespath does not map
        # 1-1 with python types (booleans are considered
        # integers in python for example).
        actual_typename = type(current).__name__
        if actual_typename not in allowed_types:
            raise exceptions.JMESPathTypeError(
                function_name, current,
                self._convert_to_jmespath_type(actual_typename), types)
        # If we're dealing with a list type, we can have
        # additional restrictions on the type of the list
        # elements (for example a function can require a
        # list of numbers or a list of strings).
        # Arrays are the only types that can have subtypes.
        if allowed_subtypes:
            self._subtype_check(current, allowed_subtypes,
                                types, function_name)

    def _get_allowed_pytypes(self, types):
        allowed_types = []
        allowed_subtypes = []
        for t in types:
            type_ = t.split('-', 1)
            if len(type_) == 2:
                type_, subtype = type_
                allowed_subtypes.append(REVERSE_TYPES_MAP[subtype])
            else:
                type_ = type_[0]
            allowed_types.extend(REVERSE_TYPES_MAP[type_])
        return allowed_types, allowed_subtypes

    def _subtype_check(self, current, allowed_subtypes, types, function_name):
        if len(allowed_subtypes) == 1:
            # The easy case, we know up front what type
            # we need to validate.
            allowed_subtypes = allowed_subtypes[0]
            for element in current:
                actual_typename = type(element).__name__
                if actual_typename not in allowed_subtypes:
                    raise exceptions.JMESPathTypeError(
                        function_name, element, actual_typename, types)
        elif len(allowed_subtypes) > 1 and current:
            # Dynamic type validation.  Based on the first
            # type we see, we validate that the remaining types
            # match.
            first = type(current[0]).__name__
            for subtypes in allowed_subtypes:
                if first in subtypes:
                    allowed = subtypes
                    break
            else:
                raise exceptions.JMESPathTypeError(
                    function_name, current[0], first, types)
            for element in current:
                actual_typename = type(element).__name__
                if actual_typename not in allowed:
                    raise exceptions.JMESPathTypeError(
                        function_name, element, actual_typename, types)

    def _create_key_func(self, expref, allowed_types, function_name):
        def keyfunc(x):
            result = expref.visit(expref.expression, x)
            actual_typename = type(result).__name__
            jmespath_type = self._convert_to_jmespath_type(actual_typename)
            # allowed_types is in term of jmespath types, not python types.
            if jmespath_type not in allowed_types:
                raise exceptions.JMESPathTypeError(
                    function_name, result, jmespath_type, allowed_types)
            return result
        return keyfunc

    def _convert_to_jmespath_type(self, pyobject):
        return TYPES_MAP.get(pyobject, 'unknown')
