# -*- coding: UTF-8 -*-
"""Generic baseN functions.

"""
from math import log
from six import integer_types, string_types
from string import printable
from types import FunctionType

from ..__common__ import *


# generic base en/decoding functions
class BaseError(ValueError):
    pass


class BaseDecodeError(BaseError):
    pass


class BaseEncodeError(BaseError):
    pass


def _generate_charset(n):
    """
    Generate a characters set.
    
    :param n: size of charset
    """
    if 1 < n <= 100:
        return printable[:n]
    elif 100 < n < 256:
        return "".join(chr(i) for i in range(n))
    raise ValueError("Bad size of character set")


def _get_charset(charset, p=""):
    """
    Charaters set selection function. It allows to define charsets in many
     different ways.
    
    :param charset: charset object, can be a string (the charset itself), a
                     function (that chooses the right charset depending on the
                     input parameter) or a dictionary (either by exact key or by
                     pattern matching)
    :param p:       the parameter for choosing the charset
    """
    # case 1: charset is a function, so return its result
    if isinstance(charset, FunctionType):
        return charset(p)
    # case 2: charset is a string, so return it
    elif isinstance(charset, string_types):
        return charset
    # case 3: charset is a dict with keys '' and 'inv', typically for a charset
    #          using lowercase and uppercase characters that can be inverted
    elif isinstance(charset, dict) and list(charset.keys()) == ["", "inv"]:
        return charset["inv" if re.match(r"[-_]inv(erted)?$", p) else ""]
    # case 4: charset is a dict, but not with the specific keys '' and 'inv', so
    #          consider it as pattern-charset pairs
    elif isinstance(charset, dict):
        # try to handle [p]arameter as a simple key
        try:
            return charset[p]
        except KeyError:
            pass
        # or handle [p]arameter as a pattern
        default, n = None, None
        for pattern, cset in charset.items():
            n = len(cset)
            if pattern == "":
                default = cset
                continue
            if re.match(pattern, p):
                return cset
        # special case: the given [p]arameter can be the charset itself if
        #                it has the right length
        p = re.sub(r"^[-_]+", "", p)
        if len(p) == n:
            return p
        # or simply rely on key ''
        if default is not None:
            return default
    raise ValueError("Bad charset descriptor")


def base_encode(input, charset, errors="strict", exc=BaseEncodeError):
    """
    Base-10 to base-N encoding.
    
    :param input:   input (str or int) to be decoded
    :param charset: base-N characters set
    :param errors:  errors handling marker
    :param exc:     exception to be raised in case of error
    """
    i = input if isinstance(input, integer_types) else s2i(input)
    n = len(charset)
    r = ""
    while i > 0:
        i, c = divmod(i, n)
        r = charset[c] + r
    return r


def base_decode(input, charset, errors="strict", exc=BaseEncodeError):
    """
    Base-N to base-10 decoding.
    
    :param input:   input to be decoded
    :param charset: base-N characters set
    :param errors:  errors handling marker
    :param exc:     exception to be raised in case of error
    """
    i, n = 0, len(charset)
    for k, c in enumerate(input):
        try:
            i = i * n + charset.index(c)
        except ValueError:
            if errors == "strict":
                raise exc("'base' codec can't decode character '{}' in position"
                          " {}".format(c, k))
            elif errors in ["ignore", "replace"]:
                continue
            else:
                raise ValueError("Unsupported error handling {}".format(errors))
    return base_encode(i, [chr(j) for j in range(256)], errors, exc)


def base(charset, pattern=None, pow2=False,
         encode_template=base_encode, decode_template=base_decode):
    """
    Base-N codec factory.
    
    :param charset: charset selection function
    :param pattern: matching pattern for the codec name (first capturing group
                     is used as the parameter for selecting the charset)
    :param pow2:    whether the base codec's N is a power of 2
    """
    is_n = isinstance(charset, int)
    n = len(_generate_charset(charset) if is_n else _get_charset(charset))
    nb = log(n, 2)
    if pow2 and nb != int(nb):
        raise BaseError("Bad charset ; {} is not a power of 2".format(n))
    
    def encode(param=""):
        a = _generate_charset(n) if is_n else _get_charset(charset, param)
        def _encode(input, errors="strict"):
            return encode_template(input, a, errors), len(input)
        return _encode
    
    def decode(param=""):
        a = _generate_charset(n) if is_n else _get_charset(charset, param)
        def _decode(input, errors="strict"):
            return decode_template(input, a, errors), len(input)
        return _decode
    
    if pattern is None:
        pattern = "base{}".format(n)
    add("base{}".format(n), encode, decode, pattern)
