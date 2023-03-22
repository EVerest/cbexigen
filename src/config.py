# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 chargebyte GmbH
# Copyright (c) 2022 - 2023 Contributors to EVerest

"""
    config file example
"""

# general path definitions
template_dir = 'input/code_templates/c'
output_dir = 'output/c'
schema_base_dir = 'input/schemas'

# definitions for logging
log_dir = 'output/log'
log_file_name = 'logfile.txt'

# add debug code while generating code
# this will add calls to status_callback if set at init of exi_bitstream_t
add_debug_code = 0

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

# optimizations for arrays and structs
apply_optimizations = 0
# the name of this parameter consists of the schema prefix plus "array_optimizations"
appHand_array_optimizations = {
    'AppProtocolType': 5
}
iso2_array_optimizations = {
    'PMaxScheduleEntryType': 12,
    'SalesTariffEntryType': 12,
    'ParameterSetType': 5,
    'X509IssuerSerialType': 5
}

# general c-code style
c_code_indent_chars = 4
# these characters will be replaced by an underscore in generated code
c_replace_chars = [' ', '-', '/']

# files to be generated
c_files_to_generate = {
    'exi_error_codes': {
        'prefix': '',
        'type': 'static',
        'folder': 'common',
        'h': {
            'template': 'static_code/exi_error_codes_h.ctc',
            'filename': 'exi_error_codes.h',
            'identifier': 'EXI_ERROR_CODES_H',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'exi_basetypes': {
        'prefix': '',
        'type': 'static',
        'folder': 'common',
        'h': {
            'template': 'static_code/exi_basetypes_h.ctc',
            'filename': 'exi_basetypes.h',
            'identifier': 'EXI_BASETYPES_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'template': 'static_code/exi_basetypes_c.ctc',
            'filename': 'exi_basetypes.c',
            'identifier': 'EXI_BASETYPES_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'exi_bitstream': {
        'prefix': '',
        'type': 'static',
        'folder': 'common',
        'h': {
            'template': 'static_code/exi_bitstream_h.ctc',
            'filename': 'exi_bitstream.h',
            'identifier': 'EXI_BITSTREAM_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'template': 'static_code/exi_bitstream_c.ctc',
            'filename': 'exi_bitstream.c',
            'identifier': 'EXI_BITSTREAM_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'exi_header': {
        'prefix': '',
        'type': 'static',
        'folder': 'common',
        'h': {
            'template': 'static_code/exi_header_h.ctc',
            'filename': 'exi_header.h',
            'identifier': 'EXI_HEADER_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'template': 'static_code/exi_header_c.ctc',
            'filename': 'exi_header.c',
            'identifier': 'EXI_HEADER_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'exi_basetypes_decoder': {
        'prefix': '',
        'type': 'static',
        'folder': 'common',
        'h': {
            'template': 'static_code/exi_basetypes_decoder_h.ctc',
            'filename': 'exi_basetypes_decoder.h',
            'identifier': 'EXI_BASETYPES_DECODER_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'template': 'static_code/exi_basetypes_decoder_c.ctc',
            'filename': 'exi_basetypes_decoder.c',
            'identifier': 'EXI_BASETYPES_DECODER_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'exi_basetypes_encoder': {
        'prefix': '',
        'type': 'static',
        'folder': 'common',
        'h': {
            'template': 'static_code/exi_basetypes_encoder_h.ctc',
            'filename': 'exi_basetypes_encoder.h',
            'identifier': 'EXI_BASETYPES_ENCODER_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'template': 'static_code/exi_basetypes_encoder_c.ctc',
            'filename': 'exi_basetypes_encoder.c',
            'identifier': 'EXI_BASETYPES_ENCODER_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'exi_types_decoder': {
        'prefix': '',
        'type': 'static',
        'folder': 'common',
        'h': {
            'template': 'static_code/exi_types_decoder_h.ctc',
            'filename': 'exi_types_decoder.h',
            'identifier': 'EXI_TYPES_DECODER_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'template': 'static_code/exi_types_decoder_c.ctc',
            'filename': 'exi_types_decoder.c',
            'identifier': 'EXI_TYPES_DECODER_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'exi_v2gtp': {
        'prefix': '',
        'type': 'static',
        'folder': 'v2gtp',
        'h': {
            'template': 'static_code/exi_v2gtp_h.ctc',
            'filename': 'exi_v2gtp.h',
            'identifier': 'EXI_V2GTP_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'template': 'static_code/exi_v2gtp_c.ctc',
            'filename': 'exi_v2gtp.c',
            'identifier': 'EXI_V2GTP_C',
            'include_std_lib': [],
            'include_other': []
        }
    },
    'appHand_Datatypes': {
        'schema': 'ISO_15118-2/FDIS/V2G_CI_AppProtocol.xsd',
        'prefix': 'appHand_',
        'type': 'converter',
        'folder': 'appHandshake',
        'h': {
            'filename': 'appHand_Datatypes.h',
            'identifier': 'APP_HANDSHAKE_DATATYPES_H',
            'include_std_lib': ['stddef.h', 'stdint.h'],
            'include_other': []
        },
        'c': {
            'filename': 'appHand_Datatypes.c',
            'identifier': 'APP_HANDSHAKE_DATATYPES_C',
            'include_std_lib': [],
            'include_other': ['appHand_Datatypes.h']
        }
    },
    'appHand_Decoder': {
        'schema': 'ISO_15118-2/FDIS/V2G_CI_AppProtocol.xsd',
        'prefix': 'appHand_',
        'type': 'decoder',
        'folder': 'appHandshake',
        'h': {
            'filename': 'appHand_Decoder.h',
            'identifier': 'APP_HANDSHAKE_DECODER_H',
            'include_std_lib': [],
            'include_other': ['exi_basetypes.h', 'exi_bitstream.h', 'appHand_Datatypes.h']
        },
        'c': {
            'filename': 'appHand_Decoder.c',
            'identifier': 'APP_HANDSHAKE_DECODER_C',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h', 'exi_basetypes_decoder.h', 'exi_error_codes.h',
                              'exi_header.h', 'exi_types_decoder.h', 'appHand_Datatypes.h']
        }
    },
    'appHand_Encoder': {
        'schema': 'ISO_15118-2/FDIS/V2G_CI_AppProtocol.xsd',
        'prefix': 'appHand_',
        'type': 'encoder',
        'folder': 'appHandshake',
        'h': {
            'filename': 'appHand_Encoder.h',
            'identifier': 'APP_HANDSHAKE_ENCODER_H',
            'include_std_lib': [],
            'include_other': ['exi_basetypes.h', 'exi_bitstream.h', 'appHand_Datatypes.h']
        },
        'c': {
            'filename': 'appHand_Encoder.c',
            'identifier': 'APP_HANDSHAKE_ENCODER_C',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes_encoder.h', 'exi_error_codes.h',
                              'exi_header.h', 'appHand_Datatypes.h']
        }
    },
    'din_msgDefDatatypes': {
        'schema': 'DIN_70121/V2G_CI_MsgDef.xsd',
        'prefix': 'din_',
        'type': 'converter',
        'folder': 'din',
        'h': {
            'filename': 'din_msgDefDatatypes.h',
            'identifier': 'DIN_MSG_DEF_DATATYPES_H',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h']
        },
        'c': {
            'filename': 'din_msgDefDatatypes.c',
            'identifier': 'DIN_MSG_DEF_DATATYPES_C',
            'include_std_lib': [],
            'include_other': ['din_msgDefDatatypes.h']
        }
    },
    'din_msgDefDecoder': {
        'schema': 'DIN_70121/V2G_CI_MsgDef.xsd',
        'prefix': 'din_',
        'type': 'decoder',
        'folder': 'din',
        'h': {
            'filename': 'din_msgDefDecoder.h',
            'identifier': 'DIN_MSG_DEF_DECODER_H',
            'include_std_lib': [],
            'include_other': ['exi_bitstream.h', 'din_msgDefDatatypes.h']
        },
        'c': {
            'filename': 'din_msgDefDecoder.c',
            'identifier': 'DIN_MSG_DEF_DECODER_C',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h', 'exi_basetypes_decoder.h', 'exi_error_codes.h', 'exi_header.h',
                              'exi_types_decoder.h', 'din_msgDefDatatypes.h', 'din_msgDefDecoder.h']
        }
    },
    'din_msgDefEncoder': {
        'schema': 'DIN_70121/V2G_CI_MsgDef.xsd',
        'prefix': 'din_',
        'type': 'encoder',
        'folder': 'din',
        'h': {
            'filename': 'din_msgDefEncoder.h',
            'identifier': 'DIN_MSG_DEF_ENCODER_H',
            'include_std_lib': [],
            'include_other': ['exi_bitstream.h', 'din_msgDefDatatypes.h']
        },
        'c': {
            'filename': 'din_msgDefEncoder.c',
            'identifier': 'DIN_MSG_DEF_ENCODER_C',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h', 'exi_basetypes_encoder.h', 'exi_error_codes.h', 'exi_header.h',
                              'din_msgDefDatatypes.h', 'din_msgDefEncoder.h']
        }
    },
    'iso2_msgDefDatatypes': {
        'schema': 'ISO_15118-2/FDIS/V2G_CI_MsgDef.xsd',
        'prefix': 'iso2_',
        'type': 'converter',
        'folder': 'iso-2',
        'h': {
            'filename': 'iso2_msgDefDatatypes.h',
            'identifier': 'ISO2_MSG_DEF_DATATYPES_H',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h']
        },
        'c': {
            'filename': 'iso2_msgDefDatatypes.c',
            'identifier': 'ISO2_MSG_DEF_DATATYPES_C',
            'include_std_lib': [],
            'include_other': ['iso2_msgDefDatatypes.h']
        }
    },
    'iso2_msgDefDecoder': {
        'schema': 'ISO_15118-2/FDIS/V2G_CI_MsgDef.xsd',
        'prefix': 'iso2_',
        'type': 'decoder',
        'folder': 'iso-2',
        'h': {
            'filename': 'iso2_msgDefDecoder.h',
            'identifier': 'ISO2_MSG_DEF_DECODER_H',
            'include_std_lib': [],
            'include_other': ['exi_bitstream.h', 'iso2_msgDefDatatypes.h']
        },
        'c': {
            'filename': 'iso2_msgDefDecoder.c',
            'identifier': 'ISO2_MSG_DEF_DECODER_C',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h', 'exi_basetypes_decoder.h', 'exi_error_codes.h', 'exi_header.h',
                              'exi_types_decoder.h', 'iso2_msgDefDatatypes.h', 'iso2_msgDefDecoder.h']
        }
    },
    'iso2_msgDefEncoder': {
        'schema': 'ISO_15118-2/FDIS/V2G_CI_MsgDef.xsd',
        'prefix': 'iso2_',
        'type': 'encoder',
        'folder': 'iso-2',
        'h': {
            'filename': 'iso2_msgDefEncoder.h',
            'identifier': 'ISO2_MSG_DEF_ENCODER_H',
            'include_std_lib': [],
            'include_other': ['exi_bitstream.h', 'iso2_msgDefDatatypes.h']
        },
        'c': {
            'filename': 'iso2_msgDefEncoder.c',
            'identifier': 'ISO2_MSG_DEF_ENCODER_C',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h', 'exi_basetypes_encoder.h', 'exi_error_codes.h', 'exi_header.h',
                              'iso2_msgDefDatatypes.h', 'iso2_msgDefEncoder.h']
        }
    },
}
