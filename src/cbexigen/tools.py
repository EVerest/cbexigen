# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 chargebyte GmbH
# Copyright (c) 2022 - 2023 Contributors to EVerest

""" Tools for the Exi Codegenerator """
from pathlib import Path
from cbexigen.tools_config import CONFIG_ARGS, CONFIG_PARAMS
from xmlschema import XMLSchema11, XsdElement
from xmlschema.validators import XsdAnyElement, XsdAtomicBuiltin, Xsd11AtomicRestriction, Xsd11Group
from pprint import pprint

TYPE_TRANSLATION_C = {
    'char': 'char',
    'boolean': 'int',
    'integer': 'int',
    'int8': 'int8_t',
    'int16': 'int16_t',
    'int32': 'int32_t',
    'int64': 'int64_t',
    'uint8': 'uint8_t',
    'uint16': 'uint16_t',
    'uint32': 'uint32_t',
    'uint64': 'uint64_t',
}

TYPE_TRANSLATION = {
    'anyURI': 'char',
    'boolean': 'boolean',
    'byte': 'int8',
    'short': 'int16',
    'int': 'int32',
    'integer': 'int32',
    'long': 'int64',
    'decimal': 'integer',  # FIXME special type
    'unsignedByte': 'uint8',
    'unsignedShort': 'uint16',
    'unsignedInt': 'uint32',
    'unsignedLong': 'uint64',
}


''' code tools '''


def save_code_to_file(filename, code, folder=''):
    out_dir = Path(CONFIG_ARGS['output_dir'], folder, filename).resolve()

    if not Path(CONFIG_ARGS['output_dir'], folder).exists():
        Path(CONFIG_ARGS['output_dir'], folder).mkdir(parents=True, exist_ok=True)

    with open(out_dir, 'w') as fp:
        fp.write(code)
        fp.close()


def adjust_string_start_end(string):
    result = ''

    if string is None:
        return result

    if string == '':
        return result

    if string.startswith('\n'):
        result = string[1:]

    if not string.endswith('\n'):
        result += '\n'

    return result


def get_indent(level: int = 1):
    return level * (' ' * CONFIG_PARAMS['c_code_indent_chars'])


''' generator tools '''


# TODO: refactor function name to have only the function get_bit_count_for_value
def get_bits_to_decode(max_value):
    result = 0
    if max_value == 0 or max_value > 4096:
        return result

    total = max_value + 1

    if total <= 2:
        result = 1
    elif total <= 4:
        result = 2
    elif total <= 8:
        result = 3
    elif total <= 16:
        result = 4
    elif total <= 32:
        result = 5
    elif total <= 64:
        result = 6
    elif total <= 128:
        result = 7
    elif total <= 256:
        result = 8
    elif total <= 512:
        result = 9
    elif total <= 1024:
        result = 10
    elif total <= 2048:
        result = 11
    elif total <= 4096:
        result = 12

    return result


def get_bit_count_for_value(max_value):
    return get_bits_to_decode(max_value)


def generate_analysis_tree(schema: XMLSchema11, element_name: str, prefix):
    element: XsdElement = schema.elements.get(element_name)
    if element is None:
        return

    def __print_child_recursive(tree_file, child_element: XsdElement, level, tree):
        indent = '    ' * level
        status = ', optional' if child_element.min_occurs == 0 else ''

        occurs_max = f'{child_element.max_occurs}' if child_element.max_occurs is not None else 'unbounded'
        occurs = f'({child_element.min_occurs}, {occurs_max})'

        abstract = ''
        base_type_name = ''
        content = ''
        model_name = ''
        enum_content = ''
        derivation = ''
        if not isinstance(child_element, XsdAnyElement):
            if child_element.abstract:
                abstract = 'abstract, '
            if child_element.type.abstract:
                abstract += 'abstract-type, '

            if child_element.type.base_type is not None:
                base_type_name = ', base-type=' + child_element.type.base_type.local_name

            if not isinstance(child_element.type, (XsdAtomicBuiltin, Xsd11AtomicRestriction)):
                if isinstance(child_element.type.content, Xsd11Group):
                    model_max = f'{child_element.type.content.max_occurs}' \
                        if child_element.type.content.max_occurs is not None else 'unbounded'
                    model_name = f', model={child_element.type.content.model} ' \
                                 f'({child_element.type.content.min_occurs}, {model_max})'

                    content = ', content=('
                    for model in child_element.type.content.iter_model():
                        if isinstance(model, Xsd11Group):
                            if model.model == 'sequence':
                                content += '('
                                for sub_model in model.iter_model():
                                    content += f'{sub_model.local_name}, '
                                content = content.removesuffix(', ')
                                sequence_max = f'{model.max_occurs}' if model.max_occurs is not None else 'unbounded'
                                content += f')({model.min_occurs}, {sequence_max}), '
                        else:
                            content += f'{model.local_name}, '
                    content = content.removesuffix(', ')
                    content += ')'
            else:
                if child_element.type.derivation is not None:
                    derivation = f', derivation={child_element.type.derivation}'

                if child_element.type.enumeration is not None:
                    enum_list = ''
                    for enum_value in child_element.type.enumeration:
                        enum_list += f'{enum_value}, '
                    enum_list = enum_list.removesuffix(', ')
                    enum_content = f', ENUM (Elements: {len(child_element.type.enumeration)}) {enum_list}'
                    # file.write(f'{indent}{child_element.local_name}: ENUM (Elements: '
                    #            f'{len(child_element.type.enumeration)}) {enum_content}\n')

        sub_tree = {}

        if child_element.local_name is not None:
            # print(f'{indent}{child_element.local_name} ({abstract}{child_element.type.local_name}{status}), {occurs}')
            file.write(f'{indent}{child_element.local_name} '
                       f'({abstract}{child_element.type.local_name}{status}), {occurs}{derivation}, '
                       f'content-type={child_element.type.content_type_label}{base_type_name}'
                       f'{model_name}{content}{enum_content}\n')

            if child_element.type.content_type_label == 'simple':
                tree[child_element.local_name] = 'simple_type'
            else:
                tree[child_element.local_name] = sub_tree
        else:
            process = f'process_content={child_element.process_contents}'
            # print(f'{indent}None ({child_element.namespace[0]}{status}), {occurs}')
            file.write(f'{indent}None ({child_element.namespace[0]}{status}), {occurs}, {process}\n')
            tree[child_element.namespace[0]] = 'wildcard'

        for attribute_str in child_element.attributes:
            attr = child_element.attributes.get(attribute_str)
            # print(f'{indent}    {attr.local_name} (attribute, {attr.type.local_name}, {attr.use})')
            file.write(f'{indent}    {attr.local_name} (attribute, {attr.type.local_name}, {attr.use})\n')
            sub_tree[attr.local_name] = 'attribute'

        for subst_child in child_element.iter_substitutes():
            __print_child_recursive(tree_file, subst_child, level, tree)

        for sub_child in child_element.iterchildren():
            __print_child_recursive(tree_file, sub_child, level + 1, sub_tree)

    # print(element.local_name)
    file = open('tree_' + prefix + element.local_name + '.txt', 'w', encoding="utf-8")
    file.write(element.local_name + '\n')
    inner_tree = {}
    all_tree = {element.local_name: inner_tree}
    for child in element.iterchildren():
        __print_child_recursive(file, child, 1, inner_tree)

    file.write('\n\npprint output of all_tree structure:\n\n')
    pprint(all_tree, sort_dicts=False, stream=file)
    file.close()


def exi_hex_string_to_bin(exi_hex_string: str):
    exi_bin = ''

    for c in exi_hex_string:
        nibble = int(c) if c in '0123456789' else ord(c.upper()) - 55
        for n in [8, 4, 2, 1]:
            if (nibble & n) > 0:
                exi_bin += '1'
            else:
                exi_bin += '0'

    print(exi_bin)
