# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 chargebyte GmbH
# Copyright (c) 2022 - 2023 Contributors to EVerest

""" Tools for the Exi Codegenerator config """
import importlib

from typing import Union, Dict
from pathlib import Path


CONFIG_ARGS: Dict[str, Union[str, Path]] = {
    'program_dir': '',
    'config_file': '',
    'log_dir': '',
    'template_dir': '',
    'output_dir': '',
    'schema_base_dir': ''
}

CONFIG_PARAMS: Dict[str, Union[str, int]] = {
    # add debug code while generating code
    'add_debug_code': 0,
    # generate analysis tree while generating code
    'generate_analysis_tree': 0,
    'generate_analysis_tree_20': 0,
    # root structure definitions
    'root_struct_name': 'exiDocument',
    'root_parameter_name': 'exiDoc',
    # name addendum definitions
    'array_define_addendum': '_ARRAY_SIZE',
    'char_define_addendum': '_CHARACTER_SIZE',
    # name prefix definitions
    'init_function_prefix': 'init_',
    'encode_function_prefix': 'encode_',
    'decode_function_prefix': 'decode_',
    'choice_sequence_prefix': 'choice_',
    # do optimizations
    'apply_optimizations': 0,
    # generate fragment de- and encoder
    'generate_fragments': 0,
    # fragment structure definitions
    'fragment_struct_name': 'exiFragment',
    'fragment_parameter_name': 'exiFrag',
    'xmldsig_fragment_struct_name': 'xmldsigFragment',
    'xmldsig_fragment_parameter_name': 'xmldsigFrag',
    # general c-code style
    'c_code_indent_chars': 4,
    'c_replace_chars': [' ', '-'],
}

__CONFIG_MODULE = None


def check_config_file():
    result = True

    if not Path(CONFIG_ARGS['program_dir'], CONFIG_ARGS['config_file']).resolve().exists():
        result = False

    return result


def set_config_arg_from_config_file(arg_name: str, config_dir: str):
    CONFIG_ARGS[arg_name] = Path(CONFIG_ARGS['program_dir'], config_dir).resolve()


def get_config_module():
    global __CONFIG_MODULE

    if __CONFIG_MODULE is None:
        config_module_name = Path(CONFIG_ARGS['config_file']).name
        if config_module_name.endswith('.py'):
            config_module_name = config_module_name[:-3]
        __CONFIG_MODULE = importlib.import_module(config_module_name)

    return __CONFIG_MODULE


def get_fragment_parameter_for_schema(schema_prefix):
    fragments = []

    config_module = get_config_module()
    parameter = schema_prefix + 'fragments'
    if hasattr(config_module, parameter):
        fragments = getattr(config_module, parameter)

    return fragments


def check_config_parameters():
    result = True

    if not Path(CONFIG_ARGS['output_dir']).exists():
        Path(CONFIG_ARGS['output_dir']).mkdir(parents=True, exist_ok=True)

    if not Path(CONFIG_ARGS['log_dir']).exists():
        Path(CONFIG_ARGS['log_dir']).mkdir(parents=True, exist_ok=True)

    return result


def process_config_parameters():
    """
        Checks the config file for parameters and overwrites defaults
        with the values from config file
    """
    config_module = get_config_module()

    ''' debug code definitions '''
    # add_debug_code
    if hasattr(config_module, 'add_debug_code'):
        CONFIG_PARAMS['add_debug_code'] = config_module.add_debug_code

    ''' analysis tree definitions '''
    # generate_analysis_tree
    if hasattr(config_module, 'generate_analysis_tree'):
        CONFIG_PARAMS['generate_analysis_tree'] = config_module.generate_analysis_tree
    # generate_analysis_tree_20
    if hasattr(config_module, 'generate_analysis_tree_20'):
        CONFIG_PARAMS['generate_analysis_tree_20'] = config_module.generate_analysis_tree_20

    ''' root structure definitions '''
    # root_struct_name
    if hasattr(config_module, 'root_struct_name'):
        CONFIG_PARAMS['root_struct_name'] = config_module.root_struct_name
    # root_parameter_name
    if hasattr(config_module, 'root_parameter_name'):
        CONFIG_PARAMS['root_parameter_name'] = config_module.root_parameter_name

    ''' name addendum definitions '''
    # array_define_addendum
    if hasattr(config_module, 'array_define_addendum'):
        CONFIG_PARAMS['array_define_addendum'] = config_module.array_define_addendum
    # char_define_addendum
    if hasattr(config_module, 'char_define_addendum'):
        CONFIG_PARAMS['char_define_addendum'] = config_module.char_define_addendum
    # byte_define_addendum
    if hasattr(config_module, 'byte_define_addendum'):
        CONFIG_PARAMS['byte_define_addendum'] = config_module.byte_define_addendum

    ''' name prefix definitions '''
    # init_function_prefix
    if hasattr(config_module, 'init_function_prefix'):
        CONFIG_PARAMS['init_function_prefix'] = config_module.init_function_prefix
    # encode_function_prefix
    if hasattr(config_module, 'encode_function_prefix'):
        CONFIG_PARAMS['encode_function_prefix'] = config_module.encode_function_prefix
    # decode_function_prefix
    if hasattr(config_module, 'decode_function_prefix'):
        CONFIG_PARAMS['decode_function_prefix'] = config_module.decode_function_prefix
    # choice_sequence_prefix
    if hasattr(config_module, 'choice_sequence_prefix'):
        CONFIG_PARAMS['choice_sequence_prefix'] = config_module.choice_sequence_prefix

    ''' optimizations '''
    # apply optimizations
    if hasattr(config_module, 'apply_optimizations'):
        CONFIG_PARAMS['apply_optimizations'] = config_module.apply_optimizations

    ''' fragment de- and encoder '''
    # apply fragments
    if hasattr(config_module, 'generate_fragments'):
        CONFIG_PARAMS['generate_fragments'] = config_module.generate_fragments

    ''' fragment structure definitions '''
    # fragment_struct_name
    if hasattr(config_module, 'fragment_struct_name'):
        CONFIG_PARAMS['fragment_struct_name'] = config_module.fragment_struct_name
    # fragment_parameter_name
    if hasattr(config_module, 'fragment_parameter_name'):
        CONFIG_PARAMS['fragment_parameter_name'] = config_module.fragment_parameter_name
    # xmldsig_fragment_struct_name
    if hasattr(config_module, 'xmldsig_fragment_struct_name'):
        CONFIG_PARAMS['xmldsig_fragment_struct_name'] = config_module.xmldsig_fragment_struct_name
    # xmldsig_fragment_parameter_name
    if hasattr(config_module, 'xmldsig_fragment_parameter_name'):
        CONFIG_PARAMS['xmldsig_fragment_parameter_name'] = config_module.xmldsig_fragment_parameter_name

    ''' general c-code style '''
    # c_code_indent_chars (number of spaces)
    if hasattr(config_module, 'c_code_indent_chars'):
        CONFIG_PARAMS['c_code_indent_chars'] = config_module.c_code_indent_chars
    # c_replace_chars (replace with underscore)
    if hasattr(config_module, 'c_replace_chars'):
        CONFIG_PARAMS['c_replace_chars'] = config_module.c_replace_chars
