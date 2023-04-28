# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 chargebyte GmbH
# Copyright (c) 2022 - 2023 Contributors to EVerest

""" Tools for the Exi Codegenerator """
from pathlib import Path
from cbexigen.tools_config import CONFIG_ARGS, CONFIG_PARAMS

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
