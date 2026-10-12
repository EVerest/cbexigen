# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2026 chargebyte GmbH
# Copyright (c) 2022 - 2026 Contributors to EVerest

"""C code for the EXI schema-informed element fragment grammar.

EXI 1.0, 8.5.3. An element whose qname is declared more than once, with
declarations that do not all agree on type name and {nillable}, cannot be
resolved to a single type grammar inside a fragment, because a fragment
carries no parent context. Its content is coded with the relaxed element
fragment grammar instead, whose event codes are numbered over the attribute
and element declarations of the whole schema.

    ElementFragment_0:  AT(A_0..A_n-1) 0..n-1, AT(*) n,
                        SE(F_0..F_m-1) n+1..n+m, SE(*) n+m+1,
                        EE n+m+2, CH n+m+3
    ElementFragment_1:  SE(F_0..F_m-1) 0..m-1, SE(*) m, EE m+1, CH m+2

Only the productions an element can actually reach are generated, which for a
simple-content element is the subset of its attributes, one CH and EE. The
event codes still come from the schema-wide lists, and that is what makes the
bytes agree with other implementations.

The C lives in ElementFragmentStruct.jinja, ElementFragmentEncode.jinja and
ElementFragmentDecode.jinja, and the coders share ElementFragmentComment.jinja.
"""

from cbexigen import tools
from cbexigen.typeDefinitions import ElementFragmentGrammar, ElementFragmentType

CHARACTER_SIZE_VALUE = 'EXI_STRING_MAX_LEN + ASCII_EXTRA_CHAR'
FEATURE_DEFINE_SUFFIX = 'HAS_ELEMENT_FRAGMENT_GRAMMAR'


def get_feature_define(prefix):
    """The macro that tells consumers the element fragment grammar is generated."""
    return f'{prefix.upper().replace("-", "_")}{FEATURE_DEFINE_SUFFIX}'


def get_type_name(prefix, fragment_type: ElementFragmentType):
    return f'{prefix}{fragment_type.type}'


def get_render_context(prefix, fragment_type: ElementFragmentType,
                       grammar: ElementFragmentGrammar) -> dict:
    """The data the element fragment templates render from."""
    return {
        'prefix': prefix,
        'struct_name': get_type_name(prefix, fragment_type),
        'fragment': fragment_type,
        'grammar': grammar,
        'members': get_init_elements(fragment_type),
        'first_bits': tools.get_bits_to_decode(grammar.first_characters_code),
        'content_bits': tools.get_bits_to_decode(grammar.content_characters_code),
    }


def get_defines(prefix, grammar: ElementFragmentGrammar):
    """Character buffer sizes for every generated element fragment struct."""
    defines = {}
    if grammar is None:
        return defines

    for fragment_type in grammar.types.values():
        for attribute in fragment_type.attributes:
            defines[f'{prefix}{attribute.define}'] = CHARACTER_SIZE_VALUE
        if fragment_type.has_characters:
            defines[f'{prefix}{fragment_type.content_define}'] = CHARACTER_SIZE_VALUE

    return defines


def get_init_elements(fragment_type: ElementFragmentType):
    """Member names whose _isUsed flag the init function has to clear."""
    names = [attribute.name for attribute in fragment_type.attributes]
    if fragment_type.has_characters:
        names.append('CONTENT')
    return names


def is_element_fragment_type(grammar: ElementFragmentGrammar, fragment_type):
    """True when this fragment type is generated from the element fragment grammar."""
    if grammar is None:
        return False

    return any(generated.type == fragment_type for generated in grammar.types.values())
