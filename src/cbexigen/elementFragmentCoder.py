# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2026 chargebyte GmbH
# Copyright (c) 2022 - 2026 Contributors to EVerest

""" C code for the EXI schema-informed element fragment grammar.

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


def __get_string_member(name, define, indent):
    return (f'{indent}struct {{\n'
            f'{indent}    char characters[{define}];\n'
            f'{indent}    uint16_t charactersLen;\n'
            f'{indent}}} {name};\n')


def get_struct(prefix, fragment_type: ElementFragmentType, indent='    '):
    """The data a fragment of this element can carry."""
    struct_name = get_type_name(prefix, fragment_type)
    declared = ', '.join(fragment_type.declared_types)

    content = (f'// Element fragment: name={{{fragment_type.namespace}}}{fragment_type.name}\n'
               f'//          EXI 1.0, 8.5.3 Schema-informed Element Fragment Grammar\n'
               f'//          declared with more than one type: {declared}\n'
               f'struct {struct_name} {{\n')

    used = []
    for attribute in fragment_type.attributes:
        content += f'{indent}// AT({attribute.qname}); event code {attribute.event_code}\n'
        content += __get_string_member(attribute.name, f'{prefix}{attribute.define}', indent)
        used.append(attribute.name)

    if fragment_type.has_characters:
        content += f'{indent}// CH [untyped value]\n'
        content += __get_string_member('CONTENT', f'{prefix}{fragment_type.content_define}', indent)
        used.append('CONTENT')

    content += '\n'
    for name in used:
        content += f'{indent}unsigned int {name}_isUsed:1;\n'
    content += '};\n'

    return content


def get_init_elements(fragment_type: ElementFragmentType):
    """Member names whose _isUsed flag the init function has to clear."""
    names = [attribute.name for attribute in fragment_type.attributes]
    if fragment_type.has_characters:
        names.append('CONTENT')
    return names


def __get_comment(prefix, fragment_type: ElementFragmentType, grammar: ElementFragmentGrammar):
    declared = ', '.join(fragment_type.declared_types)
    return (f'// Element fragment: name={{{fragment_type.namespace}}}{fragment_type.name}\n'
            f'// EXI 1.0, 8.5.3: declared with more than one type ({declared}), so inside a\n'
            f'//          fragment its content uses the element fragment grammar, whose event codes are\n'
            f'//          numbered over the {grammar.attribute_count} attribute and {grammar.element_count} '
            f'element qnames of the schema.')


def get_encoder(prefix, fragment_type: ElementFragmentType, grammar: ElementFragmentGrammar):
    struct_name = get_type_name(prefix, fragment_type)
    parameter = fragment_type.type
    first_bits = tools.get_bits_to_decode(grammar.first_characters_code)
    content_bits = tools.get_bits_to_decode(grammar.content_characters_code)

    code = __get_comment(prefix, fragment_type, grammar) + '\n'
    code += f'static int encode_{struct_name}(exi_bitstream_t* stream, const struct {struct_name}* {parameter}) {{\n'
    code += '    int grammar_id = 0;\n'
    code += '    int done = 0;\n'
    code += '    int error = 0;\n'
    code += ('    // ElementFragment_0 returns to itself after every attribute, so the\n'
             '    // remaining events are tracked here instead of in the caller\'s struct.\n')
    for name in get_init_elements(fragment_type):
        code += f'    int {name}_pending = {parameter}->{name}_isUsed;\n'
    code += '\n    while (!done)\n    {\n        switch (grammar_id)\n        {\n'

    # ElementFragment_0
    code += '        case 0:\n'
    code += f'            // Grammar: ElementFragment_0; read/write bits={first_bits}\n'
    branch = 'if'
    for attribute in fragment_type.attributes:
        code += f'            {branch} ({attribute.name}_pending)\n            {{\n'
        code += (f'                // Event: AT({attribute.qname}); '
                 f'event code {attribute.event_code}; next=ElementFragment_0\n')
        code += f'                {attribute.name}_pending = 0;\n'
        code += (f'                error = exi_basetypes_encoder_nbit_uint(stream, {first_bits}, '
                 f'{attribute.event_code});\n')
        code += __get_encode_string(parameter, attribute.name, f'{prefix}{attribute.define}', '                ')
        code += '            }\n'
        branch = 'else if'

    if fragment_type.has_characters:
        code += f'            {branch} (CONTENT_pending)\n            {{\n'
        code += (f'                // Event: CH [untyped value]; event code '
                 f'{grammar.first_characters_code}; next=ElementFragment_1\n')
        code += '                CONTENT_pending = 0;\n'
        code += (f'                error = exi_basetypes_encoder_nbit_uint(stream, {first_bits}, '
                 f'{grammar.first_characters_code});\n')
        code += __get_encode_string(parameter, 'CONTENT', f'{prefix}{fragment_type.content_define}',
                                    '                ')
        code += '                grammar_id = 1;\n'
        code += '            }\n'
        branch = 'else if'

    code += '            else\n            {\n'
    code += f'                // Event: END Element; event code {grammar.first_end_element_code}\n'
    code += (f'                error = exi_basetypes_encoder_nbit_uint(stream, {first_bits}, '
             f'{grammar.first_end_element_code});\n')
    code += '                done = 1;\n'
    code += '            }\n            break;\n'

    # ElementFragment_1
    code += '        case 1:\n'
    code += f'            // Grammar: ElementFragment_1; read/write bits={content_bits}\n'
    code += ('            // A second CH would need a second character member, so only the\n'
             '            // end of the element is reachable here.\n')
    code += f'            // Event: END Element; event code {grammar.content_end_element_code}\n'
    code += (f'            error = exi_basetypes_encoder_nbit_uint(stream, {content_bits}, '
             f'{grammar.content_end_element_code});\n')
    code += '            done = 1;\n            break;\n'

    code += '        default:\n            error = EXI_ERROR__UNKNOWN_GRAMMAR_ID;\n            break;\n'
    code += '        }\n\n        if (error)\n        {\n            done = 1;\n        }\n    }\n\n'
    code += '    return error;\n}\n'

    return code


def __get_encode_string(parameter, name, define, indent):
    return (f'{indent}if (error == EXI_ERROR__NO_ERROR)\n'
            f'{indent}{{\n'
            f'{indent}    // string should not be found in table, so add 2\n'
            f'{indent}    error = exi_basetypes_encoder_uint_16(stream, '
            f'(uint16_t)({parameter}->{name}.charactersLen + 2));\n'
            f'{indent}    if (error == EXI_ERROR__NO_ERROR)\n'
            f'{indent}    {{\n'
            f'{indent}        error = exi_basetypes_encoder_characters(stream, {parameter}->{name}.charactersLen, '
            f'{parameter}->{name}.characters, {define});\n'
            f'{indent}    }}\n'
            f'{indent}}}\n')


def __get_decode_string(parameter, name, define, indent):
    return (f'{indent}error = exi_basetypes_decoder_uint_16(stream, &{parameter}->{name}.charactersLen);\n'
            f'{indent}if (error == 0)\n'
            f'{indent}{{\n'
            f'{indent}    if ({parameter}->{name}.charactersLen >= 2)\n'
            f'{indent}    {{\n'
            f'{indent}        // string tables and table partitions are not supported, '
            f'so the length has to be decremented by 2\n'
            f'{indent}        {parameter}->{name}.charactersLen -= 2;\n'
            f'{indent}        error = exi_basetypes_decoder_characters(stream, {parameter}->{name}.charactersLen, '
            f'{parameter}->{name}.characters, {define});\n'
            f'{indent}    }}\n'
            f'{indent}    else\n'
            f'{indent}    {{\n'
            f'{indent}        // the string seems to be in the table, but this is not supported\n'
            f'{indent}        error = EXI_ERROR__STRINGVALUES_NOT_SUPPORTED;\n'
            f'{indent}    }}\n'
            f'{indent}}}\n')


def get_decoder(prefix, fragment_type: ElementFragmentType, grammar: ElementFragmentGrammar):
    struct_name = get_type_name(prefix, fragment_type)
    parameter = fragment_type.type
    first_bits = tools.get_bits_to_decode(grammar.first_characters_code)
    content_bits = tools.get_bits_to_decode(grammar.content_characters_code)

    code = __get_comment(prefix, fragment_type, grammar) + '\n'
    code += f'static int decode_{struct_name}(exi_bitstream_t* stream, struct {struct_name}* {parameter}) {{\n'
    code += '    int grammar_id = 0;\n    int done = 0;\n    uint32_t eventCode;\n    int error;\n\n'
    code += f'    init_{struct_name}({parameter});\n\n'
    code += '    while (!done)\n    {\n        switch (grammar_id)\n        {\n'

    code += '        case 0:\n'
    code += f'            // Grammar: ElementFragment_0; read/write bits={first_bits}\n'
    code += f'            error = exi_basetypes_decoder_nbit_uint(stream, {first_bits}, &eventCode);\n'
    code += '            if (error == 0)\n            {\n                switch (eventCode)\n                {\n'
    for attribute in fragment_type.attributes:
        code += f'                case {attribute.event_code}:\n'
        code += f'                    // Event: AT({attribute.qname}); next=ElementFragment_0\n'
        code += '                    // decode: string (len, characters) (Attribute)\n'
        code += __get_decode_string(parameter, attribute.name, f'{prefix}{attribute.define}', '                    ')
        code += f'                    {parameter}->{attribute.name}_isUsed = 1u;\n'
        code += '                    grammar_id = 0;\n                    break;\n'
    if fragment_type.has_characters:
        code += f'                case {grammar.first_characters_code}:\n'
        code += '                    // Event: CH [untyped value]; next=ElementFragment_1\n'
        code += '                    // decode: string (len, characters)\n'
        code += __get_decode_string(parameter, 'CONTENT', f'{prefix}{fragment_type.content_define}',
                                    '                    ')
        code += f'                    {parameter}->CONTENT_isUsed = 1u;\n'
        code += '                    grammar_id = 1;\n                    break;\n'
    code += f'                case {grammar.first_end_element_code}:\n'
    code += '                    // Event: END Element\n                    done = 1;\n                    break;\n'
    code += ('                default:\n                    error = EXI_ERROR__UNKNOWN_EVENT_CODE;\n'
             '                    break;\n                }\n            }\n            break;\n')

    code += '        case 1:\n'
    code += f'            // Grammar: ElementFragment_1; read/write bits={content_bits}\n'
    code += f'            error = exi_basetypes_decoder_nbit_uint(stream, {content_bits}, &eventCode);\n'
    code += '            if (error == 0)\n            {\n                switch (eventCode)\n                {\n'
    code += f'                case {grammar.content_end_element_code}:\n'
    code += '                    // Event: END Element\n                    done = 1;\n                    break;\n'
    if fragment_type.has_characters:
        code += f'                case {grammar.content_characters_code}:\n'
        code += ('                    // Event: CH [untyped value]; a second character event cannot be\n'
                 '                    // stored in the single CONTENT member\n'
                 '                    error = EXI_ERROR__UNSUPPORTED_SUB_EVENT;\n                    break;\n')
    code += ('                default:\n                    error = EXI_ERROR__UNKNOWN_EVENT_CODE;\n'
             '                    break;\n                }\n            }\n            break;\n')

    code += '        default:\n            error = EXI_ERROR__UNKNOWN_GRAMMAR_ID;\n            break;\n'
    code += '        }\n\n        if (error)\n        {\n            done = 1;\n        }\n    }\n\n'
    code += '    return error;\n}\n'

    return code


def is_element_fragment_type(grammar: ElementFragmentGrammar, fragment_type):
    """True when this fragment type is generated from the element fragment grammar."""
    if grammar is None:
        return False

    return any(generated.type == fragment_type for generated in grammar.types.values())
