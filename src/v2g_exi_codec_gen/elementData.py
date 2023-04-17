# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 chargebyte GmbH
# Copyright (c) 2022 - 2023 Contributors to EVerest

from dataclasses import dataclass
from v2g_exi_codec_gen.tools_config import CONFIG_PARAMS


@dataclass
class Particle:
    prefix: str = ''
    name: str = None
    type: str = None
    type_short: str = None
    base_type: str = None
    top_level_type: str = None
    min_occurs: int = -1
    max_occurs: int = -1
    min_length: int = -1
    max_length: int = -1
    min_value: int = 0
    max_value: int = -1
    abstract: bool = False
    abstract_type: bool = False
    max_occurs_changed: bool = False
    is_complex: bool = False
    is_substitute: bool = False
    is_enum: bool = False
    is_attribute: bool = False
    is_simple_content: bool = False
    enum_count: int = -1
    # additional flag if content model is choice and changed min occurrence
    content_model_changed_restrictions: bool = False
    # additional flag if parent content model is sequence and changed occurrence
    parent_model_changed_restrictions: bool = False
    parent_has_sequence: bool = False
    parent_sequence = []
    parent_has_choice_sequence: bool = False
    parent_choice_sequence_number = -1
    parent_type_is_empty: bool = False
    has_simple_content: bool = False
    simple_content_names = []
    min_occurs_old: int = -1
    max_occurs_old: int = -1
    integer_min: int = -1
    integer_max: int = -1
    integer_bit_size: int = -1
    integer_base_type: str = None
    integer_is_unsigned: bool = False

    @property
    def typename(self) -> str:
        result = self.type_short
        if self.base_type != '':
            result = self.base_type

        if result == '':
            result = self.name

        return result

    @property
    def typename_simple(self):
        if self.type_short == 'AnonType':
            return self.name

        return self.type_short

    @property
    def length_parameter_name(self) -> str:
        return self.value_parameter_name + 'Len'

    @property
    def value_parameter_name(self) -> str:
        if self.is_array:
            if self.is_enum:
                return 'array'
            elif self.base_type in ['string']:
                return 'characters'
            elif self.base_type in ['base64Binary', 'hexBinary']:
                return 'bytes'
            else:
                return 'array'

        if self.base_type in ['base64Binary', 'hexBinary']:
            return 'bytes'

        if self.type_short == '':
            return 'characters'
        if self.type_short in ['base64Binary']:
            return 'bytes'

        if not self.is_complex and self.type_short in ['string']:
            return 'characters'

        return 'characters'

    @property
    def prefixed_name(self):
        return self.prefix + self.name

    @property
    def prefixed_type(self):
        return self.prefix + self.typename_simple

    @property
    def is_array(self) -> bool:
        # an occurrence of more than 1 marks an array
        return self.max_occurs > 1

    @property
    def is_optional(self) -> bool:
        return not bool(self.min_occurs)

    @property
    def simple_type(self) -> str:
        result = self.type_short

        if self.base_type == '':
            if str.casefold(self.type_short) == 'base64binary':
                result = 'binary'
            elif str.casefold(self.type_short) == 'hexbinary':
                result = 'hex'
            elif str.casefold(self.type_short) in ['string', 'id', 'ncname']:
                result = 'string'
            elif str.casefold(self.type_short) == 'anyuri':
                result = 'uri'
        else:
            if str.casefold(self.base_type) == 'base64binary':
                result = 'binary'
            elif str.casefold(self.base_type) == 'hexbinary':
                result = 'hex'
            elif str.casefold(self.base_type) in ['string', 'id', 'ncname']:
                result = 'string'
            elif str.casefold(self.base_type) == 'anyuri':
                result = 'uri'

        return result

    @property
    def simple_type_is_string(self) -> bool:
        # for now the uri is treated as string
        return self.simple_type == 'string' or self.simple_type == 'uri'

    @property
    def simple_type_is_binary(self) -> bool:
        # for now the hex is treated as binary
        return self.simple_type == 'binary' or self.simple_type == 'hex'

    @property
    def bit_count_for_coding(self) -> int:
        result = 0

        if self.type_short == 'boolean':
            return 1

        if self.is_enum:
            num_values = self.enum_count
        else:
            if self.max_value <= 0:  # the condition may need to be more precise, in case we get a range e.g. -20..-10
                return 0
            else:
                num_values = self.max_value - self.min_value + 1

        # calculate number of relevant bits required to encode full range
        num_values -= 1  # range 0 .. num_values - 1
        while num_values != 0:
            num_values = num_values >> 1
            result += 1

        return result

    def get_translated_type(self, translation_dict) -> str:
        result = self.typename

        if self.base_type:
            if self.base_type in translation_dict:
                result = translation_dict[self.base_type]

        return result

    # ---------------------------------------------------------------------------
    # properties for #define
    @property
    def define_for_base_type(self) -> str:
        if self.is_enum:
            return ''

        if self.is_array:
            if self.is_enum:
                return ''
            elif self.base_type not in ['', 'anyURI', 'string', 'base64Binary', 'hexBinary', 'ID', 'NCName']:
                return ''

        if self.base_type in ['base64Binary', 'hexBinary']:
            return self.type_short + CONFIG_PARAMS['byte_define_addendum']

        if self.base_type in ['string', 'anyURI', 'ID', 'NCName']:
            return self.name + CONFIG_PARAMS['char_define_addendum']

        if self.type_short == '':
            return self.name + CONFIG_PARAMS['char_define_addendum']

        if not self.is_complex:
            if self.type_short in ['string', 'anyURI']:
                return self.name + CONFIG_PARAMS['char_define_addendum']
            elif self.type_short in ['base64Binary', 'hexBinary']:
                return self.type_short + CONFIG_PARAMS['byte_define_addendum']

        return ''

    @property
    def prefixed_define_for_base_type(self) -> str:
        if self.define_for_base_type != '':
            return f'{self.prefix}{self.define_for_base_type}'

        return ''

    @property
    def define_for_array(self) -> str:
        if self.is_array:
            return f'{self.typename_simple}_{self.max_occurs}{CONFIG_PARAMS["array_define_addendum"]}'

        return ''

    @property
    def prefixed_define_for_array(self) -> str:
        return f'{self.prefix}{self.define_for_array}'

    @property
    def define_max_value(self) -> str:
        if self.value_parameter_name == 'characters':
            return 'EXI_STRING_MAX_LEN + ASCII_EXTRA_CHAR'
        elif self.value_parameter_name == 'bytes':
            return 'EXI_BYTE_ARRAY_MAX_LEN'

        return ''


class Choice:
    def __init__(self):
        self.is_multi_choice: int = 0
        self.multi_choice_max: int = 0
        self.choice_items = []
        self.choice_sequences = []
        self.min_occurs = -1

    @property
    def choice_item_count(self) -> int:
        return len(self.choice_items)

    @property
    def choice_sequence_count(self) -> int:
        return len(self.choice_sequences)


@dataclass
class ElementData:
    prefix: str = ''
    level: int = -1
    count: int = -1
    # full qualified name
    name: str = None
    name_short: str = None
    # reference
    ref: str = None
    # simple, complex
    type_definition: str = None
    # additional info for generating type, can be e.g. array or enum
    type_hint: str = None
    # type name
    type: str = None
    type_short: str = None
    base_type: str = None
    # element only
    content_type: str = None
    # restriction
    derivation: str = None
    # other info
    type_id: str = None
    final: bool = False
    abstract: bool = False
    abstract_type: bool = False
    has_abstract_particle: bool = False
    # additional info if element contains abstract particles and realizations
    has_abstract_sequence: bool = False
    abstract_sequences = []  # list of tuples (list of particles, min_occurs, max_occurs)
    # list of particles
    particles = []
    # additional info if content model is choice
    has_choice: bool = False
    choices = []
    is_choice: bool = False     # obsolete, will be removed if decoder and encoder is adjusted
    has_sequence: bool = False  # obsolete, will be removed if decoder and encoder is adjusted
    sequences = []              # obsolete, will be removed if decoder and encoder is adjusted
    # info regarding namespace elements list
    is_in_namespace_elements = False
    # additional info if type definition is enum
    has_enum_list: bool = False
    enum_list = []

    def __init__(self, prefix: str):
        self.prefix = prefix
        # list of corresponding next grammar IDs
        self.particles_next_grammar_ids = {}
        # reset sequences and choices lists
        self.sequences = []
        self.choices = []
        # reset info from abstract particles and realizations
        self.has_abstract_sequence = False
        self.abstract_sequences = []

    @property
    def typename(self):
        if self.type_short == 'AnonType':
            return self.name_short

        return self.type_short

    @property
    def prefixed_name(self):
        return self.prefix + self.name_short

    @property
    def prefixed_type(self):
        return self.prefix + self.typename

    @property
    def prefixed_init_name(self):
        return self.prefix + 'init_' + self.name_short

    @property
    def prefixed_init_type(self):
        return self.prefix + 'init_' + self.typename

    @property
    def element_comment(self):
        comment_parts = []
        comment_parts.append("definition=" + self.type_definition)
        comment_parts.append("name=" + self.name)
        comment_parts.append("type=" + self.type)
        comment_parts.append("base type=" + self.base_type)
        comment_parts.append("content type=" + self.content_type)
        comment = "// Element: "
        comment += '; '.join(comment_parts) + ';\n'

        comment_parts.clear()
        comment_parts.append("abstract=" + str(self.abstract))
        comment_parts.append("final=" + str(self.final))
        if self.derivation:
            comment_parts.append("derivation=" + self.derivation)
        if self.is_choice:
            comment_parts.append("choice=" + str(self.is_choice))
        if self.has_sequence:
            comment_parts.append("sequence=" + str(self.has_sequence) + " (" + str(len(self.sequences)))
        comment += "//          "
        comment += '; '.join(comment_parts)
        if comment_parts:
            comment += ';'

        return comment

    @property
    def particle_comment(self):
        comment_parts = []
        for particle in self.particles:
            comment_part = f'{particle.name}, {particle.type_short} ('
            comment_part += f'{particle.min_occurs}, {particle.max_occurs})'

            if particle.parent_has_sequence:
                comment_part += f'(was {particle.min_occurs_old}, {particle.max_occurs_old})'
                comment_part += f'(seq. {particle.parent_sequence})'

            comment_parts.append(comment_part)

        comment = '// Particle: '
        comment += '; '.join(comment_parts)
        if comment_parts:
            comment += ';'
        return comment

    def particle_from_name(self, particle_name: str) -> Particle:
        for particle in self.particles:
            if particle.name == particle_name:
                return particle
        return None
