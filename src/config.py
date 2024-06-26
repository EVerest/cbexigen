# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 chargebyte GmbH
# Copyright (c) 2022 - 2023 Contributors to EVerest

"""
    config file for cbexigen
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
# and create separate code for the debugging functions
add_debug_code = 0

# generate analysis tree while generating code
# this will generate an analysis tree file starting from the root element
# for the 15118-20 every message has its separate tree file
generate_analysis_tree = 0
generate_analysis_tree_20 = 0

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

# Ambiguous element names are elements with the same name but different types.
# Currently, this only seems to apply to the eMAID element from ISO 15118-2.
# With the fragment coder, the type for the ambiguous element must be specified
# here so that the correct decoder or encoder is called.
iso2_ambiguous_element_names = {
    'eMAID': 'EMAIDType',
}

# optimizations for arrays and structs
apply_optimizations = 1
# the name of this parameter must consist of the schema prefix (chosen below)
# plus "array_optimizations"
appHand_array_optimizations = {
    'AppProtocolType': 5
}
din_array_optimizations = {
    'ReferenceType': 1
}
iso2_array_optimizations = {
    'PMaxScheduleEntryType': 12,
    'SalesTariffEntryType': 12,
    'ParameterSetType': 5,
    # this shall apply to array ListOfRootCertificateIDsType->RootCertificateID only
    'X509IssuerSerialType': 5
}
iso20_array_optimizations = {
    # FIXME
    # gdb's stack overflows on the original struct site - no other
    # reason to restrict this currently
    'PriceRuleStackType': 64,
    # Workaround for missing loop implementation of large arrays (https://github.com/EVerest/cbexigen/issues/28).
    'ParameterSetType': 4,
    'ParameterType': 8
}

# optimizations for fields, which shall be excluded. The name to exclude and a list of parent elements [V2G2-771]
#  - Id (attribute in SignedInfo)
#  - ##any in SignedInfo – CanonicalizationMethod
#  - HMACOutputLength in SignedInfo – SignatureMethod
#  - ##other in SignedInfo – SignatureMethod
#  - Type (attribute in SignedInfo-Reference)
#  - ##other in SignedInfo – Reference – Transforms – Transform
#  - XPath in SignedInfo – Reference – Transforms – Transform
#  - ##other in SignedInfo – Reference – DigestMethod
#  - Id (attribute in SignatureValue)
#  - Object (in Signature)
#  - KeyInfo
iso2_field_optimizations = {
    'Id': ['SignedInfo', 'SignatureValue'],  # remove Id from SignedInfo and SignatureValue
    'ANY': ['CanonicalizationMethod', 'SignatureMethod', 'Transform', 'DigestMethod'],  # remove ##any from these elements
    'HMACOutputLength': ['SignatureMethod'],  # remove HMACOutputLength from SignatureMethod
    'Type': ['Reference'],  # remove Type from Reference
    'XPath': ['Transform'],  # remove XPath from Transform
    'Object': ['Signature'],  # remove Object from Signature
    'KeyInfo': []  # remove generally
}

# if fragment de- and encoder should be generated, set this value to 1.
# Currently only complex elements can be added to the fragment coders.
# NOTE! There may be problems when comparing the signature of the eMAID.
#       In the ISO 15118-2 schema there are two different types with problematic names, EMAIDType and eMAIDType.
#       The fragment de- and encoder of e.g. openV2G considers this type as generic type
#       EXISchemaInformedElementFragmentGrammar. We treat it as a complex type.
#       We have not yet been able to determine why this particular type has to be coded as a generic type,
#       and only for the fragment decoder and encoder.
#       This is why we have not yet adapted our fragment coders, and it can lead to the problem mentioned.
generate_fragments = 1
# fragment structure definitions
fragment_struct_name = 'exiFragment'
fragment_parameter_name = 'exiFrag'
xmldsig_fragment_struct_name = 'xmldsigFragment'
xmldsig_fragment_parameter_name = 'xmldsigFrag'
# the name of this parameter must consist of the schema prefix (chosen below) plus "fragments"
iso2_fragments = [
    'SignedInfo',
    'AuthorizationReq',
    'CertificateInstallationReq',
    'CertificateUpdateReq',
    'ContractSignatureCertChain',
    'ContractSignatureEncryptedPrivateKey',
    'DHpublickey',
    'MeteringReceiptReq',
    'SalesTariff',
    'eMAID',
]
iso20_fragments = [
    'SignedInfo',
    'PnC_AReqAuthorizationMode',
    'CertificateInstallationReq',
    'SignedInstallationData',
    'MeteringConfirmationReq',
    'AbsolutePriceSchedule',
]
iso20_ac_fragments = [
    'SignedInfo',
    'AC_ChargeParameterDiscoveryRes',
]
iso20_dc_fragments = [
    'SignedInfo',
    'DC_ChargeParameterDiscoveryRes',
]

# mxldsig fragments which should be generated
xmldsig_fragments = [
    'SignedInfo'  # creates only signedInfo fragment
]

# general C code style
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
            'template': 'static_code/exi_error_codes.h.jinja',
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
            'template': 'static_code/exi_basetypes.h.jinja',
            'filename': 'exi_basetypes.h',
            'identifier': 'EXI_BASETYPES_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'template': 'static_code/exi_basetypes.c.jinja',
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
            'template': 'static_code/exi_bitstream.h.jinja',
            'filename': 'exi_bitstream.h',
            'identifier': 'EXI_BITSTREAM_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'template': 'static_code/exi_bitstream.c.jinja',
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
            'template': 'static_code/exi_header.h.jinja',
            'filename': 'exi_header.h',
            'identifier': 'EXI_HEADER_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'template': 'static_code/exi_header.c.jinja',
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
            'template': 'static_code/exi_basetypes_decoder.h.jinja',
            'filename': 'exi_basetypes_decoder.h',
            'identifier': 'EXI_BASETYPES_DECODER_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'template': 'static_code/exi_basetypes_decoder.c.jinja',
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
            'template': 'static_code/exi_basetypes_encoder.h.jinja',
            'filename': 'exi_basetypes_encoder.h',
            'identifier': 'EXI_BASETYPES_ENCODER_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'template': 'static_code/exi_basetypes_encoder.c.jinja',
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
            'template': 'static_code/exi_types_decoder.h.jinja',
            'filename': 'exi_types_decoder.h',
            'identifier': 'EXI_TYPES_DECODER_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'template': 'static_code/exi_types_decoder.c.jinja',
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
            'template': 'static_code/exi_v2gtp.h.jinja',
            'filename': 'exi_v2gtp.h',
            'identifier': 'EXI_V2GTP_H',
            'include_std_lib': [],
            'include_other': []
        },
        'c': {
            'template': 'static_code/exi_v2gtp.c.jinja',
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
                              'exi_header.h', 'exi_types_decoder.h', 'appHand_Datatypes.h',
                              'appHand_Decoder.h']
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
                              'exi_header.h', 'appHand_Datatypes.h', 'appHand_Encoder.h']
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
    'iso20_CommonMessages_Datatypes': {
        'schema': 'ISO_15118-20/FDIS/V2G_CI_CommonMessages.xsd',
        'prefix': 'iso20_',
        'type': 'converter',
        'folder': 'iso-20',
        'h': {
            'filename': 'iso20_CommonMessages_Datatypes.h',
            'identifier': 'ISO20_COMMON_MESSAGES_DATATYPES_H',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h']
        },
        'c': {
            'filename': 'iso20_CommonMessages_Datatypes.c',
            'identifier': 'ISO20_COMMON_MESSAGES_DATATYPES_C',
            'include_std_lib': [],
            'include_other': ['iso20_CommonMessages_Datatypes.h']
        }
    },
    'iso20_CommonMessages_Decoder': {
        'schema': 'ISO_15118-20/FDIS/V2G_CI_CommonMessages.xsd',
        'prefix': 'iso20_',
        'type': 'decoder',
        'folder': 'iso-20',
        'h': {
            'filename': 'iso20_CommonMessages_Decoder.h',
            'identifier': 'ISO20_COMMON_MESSAGES_DECODER_H',
            'include_std_lib': [],
            'include_other': ['exi_bitstream.h', 'iso20_CommonMessages_Datatypes.h']
        },
        'c': {
            'filename': 'iso20_CommonMessages_Decoder.c',
            'identifier': 'ISO20_COMMON_MESSAGES_DECODER_C',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h', 'exi_types_decoder.h', 'exi_basetypes_decoder.h',
                              'exi_error_codes.h', 'exi_header.h', 'iso20_CommonMessages_Datatypes.h',
                              'iso20_CommonMessages_Decoder.h']
        }
    },
    'iso20_CommonMessages_Encoder': {
        'schema': 'ISO_15118-20/FDIS/V2G_CI_CommonMessages.xsd',
        'prefix': 'iso20_',
        'type': 'encoder',
        'folder': 'iso-20',
        'h': {
            'filename': 'iso20_CommonMessages_Encoder.h',
            'identifier': 'ISO20_COMMON_MESSAGES_ENCODER_H',
            'include_std_lib': [],
            'include_other': ['exi_bitstream.h', 'iso20_CommonMessages_Datatypes.h']
        },
        'c': {
            'filename': 'iso20_CommonMessages_Encoder.c',
            'identifier': 'ISO20_COMMON_MESSAGES_ENCODER_C',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h', 'exi_basetypes_encoder.h', 'exi_error_codes.h', 'exi_header.h',
                              'iso20_CommonMessages_Datatypes.h', 'iso20_CommonMessages_Encoder.h']
        }
    },
    'iso20_AC_Datatypes': {
        'schema': 'ISO_15118-20/FDIS/V2G_CI_AC.xsd',
        'prefix': 'iso20_ac_',
        'type': 'converter',
        'folder': 'iso-20',
        'h': {
            'filename': 'iso20_AC_Datatypes.h',
            'identifier': 'ISO20_AC_DATATYPES_H',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h']
        },
        'c': {
            'filename': 'iso20_AC_Datatypes.c',
            'identifier': 'ISO20_AC_DATATYPES_C',
            'include_std_lib': [],
            'include_other': ['iso20_AC_Datatypes.h']
        }
    },
    'iso20_AC_Decoder': {
        'schema': 'ISO_15118-20/FDIS/V2G_CI_AC.xsd',
        'prefix': 'iso20_ac_',
        'type': 'decoder',
        'folder': 'iso-20',
        'h': {
            'filename': 'iso20_AC_Decoder.h',
            'identifier': 'ISO20_AC_DECODER_H',
            'include_std_lib': [],
            'include_other': ['exi_bitstream.h', 'iso20_AC_Datatypes.h']
        },
        'c': {
            'filename': 'iso20_AC_Decoder.c',
            'identifier': 'ISO20_AC_DECODER_C',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h', 'exi_types_decoder.h', 'exi_basetypes_decoder.h', 'exi_error_codes.h',
                              'exi_header.h', 'iso20_AC_Datatypes.h', 'iso20_AC_Decoder.h']
        }
    },
    'iso20_AC_Encoder': {
        'schema': 'ISO_15118-20/FDIS/V2G_CI_AC.xsd',
        'prefix': 'iso20_ac_',
        'type': 'encoder',
        'folder': 'iso-20',
        'h': {
            'filename': 'iso20_AC_Encoder.h',
            'identifier': 'ISO20_AC_ENCODER_H',
            'include_std_lib': [],
            'include_other': ['exi_bitstream.h', 'iso20_AC_Datatypes.h']
        },
        'c': {
            'filename': 'iso20_AC_Encoder.c',
            'identifier': 'ISO20_AC_ENCODER_C',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h', 'exi_basetypes_encoder.h', 'exi_error_codes.h', 'exi_header.h',
                              'iso20_AC_Datatypes.h', 'iso20_AC_Encoder.h']
        }
    },
    'iso20_DC_Datatypes': {
        'schema': 'ISO_15118-20/FDIS/V2G_CI_DC.xsd',
        'prefix': 'iso20_dc_',
        'type': 'converter',
        'folder': 'iso-20',
        'h': {
            'filename': 'iso20_DC_Datatypes.h',
            'identifier': 'ISO20_DC_DATATYPES_H',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h']
        },
        'c': {
            'filename': 'iso20_DC_Datatypes.c',
            'identifier': 'ISO20_DC_DATATYPES_C',
            'include_std_lib': [],
            'include_other': ['iso20_DC_Datatypes.h']
        }
    },
    'iso20_DC_Decoder': {
        'schema': 'ISO_15118-20/FDIS/V2G_CI_DC.xsd',
        'prefix': 'iso20_dc_',
        'type': 'decoder',
        'folder': 'iso-20',
        'h': {
            'filename': 'iso20_DC_Decoder.h',
            'identifier': 'ISO20_DC_DECODER_H',
            'include_std_lib': [],
            'include_other': ['exi_bitstream.h', 'iso20_DC_Datatypes.h']
        },
        'c': {
            'filename': 'iso20_DC_Decoder.c',
            'identifier': 'ISO20_DC_DECODER_C',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h', 'exi_types_decoder.h', 'exi_basetypes_decoder.h',
                              'exi_error_codes.h', 'exi_header.h', 'iso20_DC_Datatypes.h',
                              'iso20_DC_Decoder.h']
        }
    },
    'iso20_DC_Encoder': {
        'schema': 'ISO_15118-20/FDIS/V2G_CI_DC.xsd',
        'prefix': 'iso20_dc_',
        'type': 'encoder',
        'folder': 'iso-20',
        'h': {
            'filename': 'iso20_DC_Encoder.h',
            'identifier': 'ISO20_DC_ENCODER_H',
            'include_std_lib': [],
            'include_other': ['exi_bitstream.h', 'iso20_DC_Datatypes.h']
        },
        'c': {
            'filename': 'iso20_DC_Encoder.c',
            'identifier': 'ISO20_DC_ENCODER_C',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h', 'exi_basetypes_encoder.h', 'exi_error_codes.h', 'exi_header.h',
                              'iso20_DC_Datatypes.h', 'iso20_DC_Encoder.h']
        }
    },
    'iso20_WPT_Datatypes': {
        'schema': 'ISO_15118-20/FDIS/V2G_CI_WPT.xsd',
        'prefix': 'iso20_wpt_',
        'type': 'converter',
        'folder': 'iso-20',
        'h': {
            'filename': 'iso20_WPT_Datatypes.h',
            'identifier': 'ISO20_WPT_DATATYPES_H',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h']
        },
        'c': {
            'filename': 'iso20_WPT_Datatypes.c',
            'identifier': 'ISO20_WPT_DATATYPES_C',
            'include_std_lib': [],
            'include_other': ['iso20_WPT_Datatypes.h']
        }
    },
    'iso20_WPT_Decoder': {
        'schema': 'ISO_15118-20/FDIS/V2G_CI_WPT.xsd',
        'prefix': 'iso20_wpt_',
        'type': 'decoder',
        'folder': 'iso-20',
        'h': {
            'filename': 'iso20_WPT_Decoder.h',
            'identifier': 'ISO20_WPT_DECODER_H',
            'include_std_lib': [],
            'include_other': ['exi_bitstream.h', 'iso20_WPT_Datatypes.h']
        },
        'c': {
            'filename': 'iso20_WPT_Decoder.c',
            'identifier': 'ISO20_WPT_DECODER_C',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h', 'exi_types_decoder.h', 'exi_basetypes_decoder.h',
                              'exi_error_codes.h', 'exi_header.h', 'iso20_WPT_Datatypes.h',
                              'iso20_WPT_Decoder.h']
        }
    },
    'iso20_WPT_Encoder': {
        'schema': 'ISO_15118-20/FDIS/V2G_CI_WPT.xsd',
        'prefix': 'iso20_wpt_',
        'type': 'encoder',
        'folder': 'iso-20',
        'h': {
            'filename': 'iso20_WPT_Encoder.h',
            'identifier': 'ISO20_WPT_ENCODER_H',
            'include_std_lib': [],
            'include_other': ['exi_bitstream.h', 'iso20_WPT_Datatypes.h']
        },
        'c': {
            'filename': 'iso20_WPT_Encoder.c',
            'identifier': 'ISO20_WPT_ENCODER_C',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h', 'exi_basetypes_encoder.h', 'exi_error_codes.h', 'exi_header.h',
                              'iso20_WPT_Datatypes.h', 'iso20_WPT_Encoder.h']
        }
    },
    'iso20_ACDP_Datatypes': {
        'schema': 'ISO_15118-20/FDIS/V2G_CI_ACDP.xsd',
        'prefix': 'iso20_acdp_',
        'type': 'converter',
        'folder': 'iso-20',
        'h': {
            'filename': 'iso20_ACDP_Datatypes.h',
            'identifier': 'ISO20_ACDP_DATATYPES_H',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h']
        },
        'c': {
            'filename': 'iso20_ACDP_Datatypes.c',
            'identifier': 'ISO20_ACDP_DATATYPES_C',
            'include_std_lib': [],
            'include_other': ['iso20_ACDP_Datatypes.h']
        }
    },
    'iso20_ACDP_Decoder': {
        'schema': 'ISO_15118-20/FDIS/V2G_CI_ACDP.xsd',
        'prefix': 'iso20_acdp_',
        'type': 'decoder',
        'folder': 'iso-20',
        'h': {
            'filename': 'iso20_ACDP_Decoder.h',
            'identifier': 'ISO20_ACDP_DECODER_H',
            'include_std_lib': [],
            'include_other': ['exi_bitstream.h', 'iso20_ACDP_Datatypes.h']
        },
        'c': {
            'filename': 'iso20_ACDP_Decoder.c',
            'identifier': 'ISO20_ACDP_DECODER_C',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h', 'exi_types_decoder.h', 'exi_basetypes_decoder.h',
                              'exi_error_codes.h', 'exi_header.h', 'iso20_ACDP_Datatypes.h',
                              'iso20_ACDP_Decoder.h']
        }
    },
    'iso20_ACDP_Encoder': {
        'schema': 'ISO_15118-20/FDIS/V2G_CI_ACDP.xsd',
        'prefix': 'iso20_acdp_',
        'type': 'encoder',
        'folder': 'iso-20',
        'h': {
            'filename': 'iso20_ACDP_Encoder.h',
            'identifier': 'ISO20_ACDP_ENCODER_H',
            'include_std_lib': [],
            'include_other': ['exi_bitstream.h', 'iso20_ACDP_Datatypes.h']
        },
        'c': {
            'filename': 'iso20_ACDP_Encoder.c',
            'identifier': 'ISO20_ACDP_ENCODER_C',
            'include_std_lib': ['stdint.h'],
            'include_other': ['exi_basetypes.h', 'exi_basetypes_encoder.h', 'exi_error_codes.h', 'exi_header.h',
                              'iso20_ACDP_Datatypes.h', 'iso20_ACDP_Encoder.h']
        }
    },
}
