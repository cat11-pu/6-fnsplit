import json

from jmespath.compat import string_type as STRING_TYPE
from jmespath.fn_utils import signature


class StringFunctionsMixin(object):

    @signature({"types": ['string']}, {"types": ['array-string']})
    def _func_join(self, separator, array):
        return separator.join(array)

    @signature({'types': ['array', 'string']}, {'types': []})
    def _func_contains(self, subject, search):
        return search in subject

    @signature({'types': ['string']}, {'types': ['string']})
    def _func_starts_with(self, search, suffix):
        return search.startswith(suffix)

    @signature({'types': ['string']}, {'types': ['string']})
    def _func_ends_with(self, search, suffix):
        return search.endswith(suffix)

    @signature({'types': []})
    def _func_to_string(self, arg):
        if isinstance(arg, STRING_TYPE):
            return arg
        else:
            return json.dumps(arg, separators=(',', ':'),
                              default=str)

    @signature({'types': []})
    def _func_to_number(self, arg):
        if isinstance(arg, (list, dict, bool)):
            return None
        elif arg is None:
            return None
        elif isinstance(arg, (int, float)):
            return arg
        else:
            try:
                return int(arg)
            except ValueError:
                try:
                    return float(arg)
                except ValueError:
                    return None
