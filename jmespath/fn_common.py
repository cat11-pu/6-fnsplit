# -*- coding: utf-8 -*-
"""Shared helpers for the builtin JMESPath function mixins."""


def signature(*arguments):
    def _record_signature(func):
        func.signature = arguments
        return func
    return _record_signature
