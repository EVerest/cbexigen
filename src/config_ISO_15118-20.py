# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 chargebyte GmbH
# Copyright (c) 2022 - 2023 Contributors to EVerest

"""
    config file for ISO 15118-20
"""

# general path definitions
template_dir = 'input/code_templates/c'
output_dir = 'output/c'

# definitions for logging
log_dir = 'output/log'
log_file_name = 'logfile_ISO_15118-20.txt'

# root structure definitions
root_struct_name = 'exiDocument'
root_parameter_name = 'exiDoc'

# name addendum definitions
array_define_addendum = '_ARRAY_SIZE'
char_define_addendum = '_CHARACTER_SIZE'
byte_define_addendum = '_BYTES_SIZE'

# name prefix definitions
init_function_prefix = 'init_'
encode_function_prefix = 'encode_'
decode_function_prefix = 'decode_'
choice_sequence_prefix = 'choice_'

# general c-code style
c_code_indent_chars = 4
# these characters will be replaced by an underscore in generated code
c_replace_chars = [' ', '-']

# general schema info
schema_name = 'ISO 15118-20'
schema_path = 'input/schemas/ISO_15118-20/FDIS'
schema_default = 'V2G_CI_AppProtocol.xsd'

# files to be generated
c_files_to_generate = {
    'ExiOptions': {
        'schema': '',
        'type': 'schemaless',
        'module': 'exi_options',
        'h': {
            'filename': 'ExiOptions.h',
            'identifier': 'EXI_OPTIONS_H',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'ExiConfig': {
        'schema': '',
        'type': 'schemaless',
        'module': 'exi_config',
        'h': {
            'filename': 'ExiConfig.h',
            'identifier': 'EXI_CONFIG_H',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'ExiTypes': {
        'schema': '',
        'type': 'schemaless',
        'module': 'exi_types',
        'h': {
            'filename': 'ExiTypes.h',
            'identifier': 'EXI_TYPES_H',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'ErrorCodes': {
        'schema': '',
        'type': 'schemaless',
        'module': 'error_codes',
        'h': {
            'filename': 'ErrorCodes.h',
            'identifier': 'ERROR_CODES_H',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'BitInputStream': {
        'schema': '',
        'type': 'schemaless',
        'module': 'bit_input_stream',
        'h': {
            'filename': 'BitInputStream.h',
            'identifier': 'BIT_INPUT_STREAM_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'filename': 'BitInputStream.c',
            'identifier': 'BIT_INPUT_STREAM_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'BitOutputStream': {
        'schema': '',
        'type': 'schemaless',
        'module': 'bit_output_stream',
        'h': {
            'filename': 'BitOutputStream.h',
            'identifier': 'BIT_OUTPUT_STREAM_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'filename': 'BitOutputStream.c',
            'identifier': 'BIT_OUTPUT_STREAM_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'ExiHeaderDecoder': {
        'schema': '',
        'type': 'schemaless',
        'module': 'exi_header_decoder',
        'h': {
            'filename': 'ExiHeaderDecoder.h',
            'identifier': 'EXI_HEADER_DECODER_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'filename': 'ExiHeaderDecoder.c',
            'identifier': 'EXI_HEADER_DECODER_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'ExiHeaderEncoder': {
        'schema': '',
        'type': 'schemaless',
        'module': 'exi_header_encoder',
        'h': {
            'filename': 'ExiHeaderEncoder.h',
            'identifier': 'EXI_HEADER_ENCODER_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'filename': 'ExiHeaderEncoder.c',
            'identifier': 'EXI_HEADER_ENCODER_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'DecoderBaseTypes': {
        'schema': '',
        'type': 'schemaless',
        'module': 'decoder_base_types',
        'h': {
            'filename': 'DecoderBaseTypes.h',
            'identifier': 'DECODER_BASE_TYPES_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'filename': 'DecoderBaseTypes.c',
            'identifier': 'DECODER_BASE_TYPES_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'EncoderBaseTypes': {
        'schema': '',
        'type': 'schemaless',
        'module': 'encoder_base_types',
        'h': {
            'filename': 'EncoderBaseTypes.h',
            'identifier': 'ENCODER_BASE_TYPES_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'filename': 'EncoderBaseTypes.c',
            'identifier': 'ENCODER_BASE_TYPES_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'appHandshakeDatatypes': {
        'schema': 'V2G_CI_AppProtocol.xsd',
        'type': 'datatypes',
        'module': 'datatypes',
        'h': {
            'filename': 'appHandshakeDatatypes.h',
            'identifier': 'APP_HANDSHAKE_DATATYPES_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'filename': 'appHandshakeDatatypes.c',
            'identifier': 'APP_HANDSHAKE_DATATYPES_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'commonMessagesDatatypes': {
        'schema': 'V2G_CI_CommonMessages.xsd',
        'type': 'datatypes',
        'module': 'datatypes',
        'h': {
            'filename': 'commonMessagesDatatypes.h',
            'identifier': 'COMMON_MESSAGES_DATATYPES_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'filename': 'commonMessagesDatatypes.c',
            'identifier': 'COMMON_MESSAGES_DATATYPES_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'acMessagesDatatypes': {
        'schema': 'V2G_CI_AC.xsd',
        'type': 'datatypes',
        'module': 'datatypes',
        'h': {
            'filename': 'acMessagesDatatypes.h',
            'identifier': 'AC_MESSAGES_DATATYPES_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'filename': 'acMessagesDatatypes.c',
            'identifier': 'AC_MESSAGES_DATATYPES_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'acdpMessagesDatatypes': {
        'schema': 'V2G_CI_ACDP.xsd',
        'type': 'datatypes',
        'module': 'datatypes',
        'h': {
            'filename': 'acdpMessagesDatatypes.h',
            'identifier': 'ACDP_MESSAGES_DATATYPES_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'filename': 'acdpMessagesDatatypes.c',
            'identifier': 'ACDP_MESSAGES_DATATYPES_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'dcMessagesDatatypes': {
        'schema': 'V2G_CI_DC.xsd',
        'type': 'datatypes',
        'module': 'datatypes',
        'h': {
            'filename': 'dcMessagesDatatypes.h',
            'identifier': 'DC_MESSAGES_DATATYPES_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'filename': 'dcMessagesDatatypes.c',
            'identifier': 'DC_MESSAGES_DATATYPES_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'wptMessagesDatatypes': {
        'schema': 'V2G_CI_WPT.xsd',
        'type': 'datatypes',
        'module': 'datatypes',
        'h': {
            'filename': 'wptMessagesDatatypes.h',
            'identifier': 'WPT_MESSAGES_DATATYPES_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'filename': 'wptMessagesDatatypes.c',
            'identifier': 'WPT_MESSAGES_DATATYPES_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
}
