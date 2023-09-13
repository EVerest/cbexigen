# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 chargebyte GmbH
# Copyright (c) 2022 - 2023 Contributors to EVerest

from typing import List
from cbexigen.base_coder_classes import ExiBaseCoderHeader, ExiBaseCoderCode
from cbexigen import tools_generator, tools
from cbexigen.elementData import ElementData, Particle
from cbexigen.elementGrammar import GrammarFlag, ElementGrammar, ElementGrammarDetail
from cbexigen.tools_config import CONFIG_PARAMS
from cbexigen.tools_logging import log_write_error

# ---------------------------------------------------------------------------
# Exi decoder generating header file
# ---------------------------------------------------------------------------


class ExiDecoderHeader(ExiBaseCoderHeader):
    def __init__(self, parameters, enable_logging=True):
        super(ExiDecoderHeader, self).__init__(parameters=parameters, enable_logging=enable_logging)

        self.__is_iso20 = str(self.parameters['prefix']).startswith('iso20_')

        self.__include_content = ''
        self.__code_content = ''

    def __get_root_content(self):
        content = '// main function for decoding\n'

        name = self.parameters['prefix'] + self.config['root_struct_name']
        content += 'int ' + self.config['decode_function_prefix'] + name + '('
        content += 'exi_bitstream_t* stream, '
        content += 'struct ' + name + '* ' + self.config['root_parameter_name'] + ');'

        return content

    def __render_file(self):
        try:
            temp = self.generator.get_template('DatatypesDecoder.h.jinja')
            code = temp.render(filename=self.h_params["filename"], filekey=self.h_params['identifier'],
                               include_content=self.__include_content, code_content=self.__code_content)
            tools.save_code_to_file(self.h_params['filename'], code, self.parameters['folder'])
        except KeyError as err:
            log_write_error(f'Exception in {self.__class__.__name__}.{self.__render_file.__name__} '
                            f'(KeyError): {err}')

    def generate_file(self):
        if self.h_params is None:
            log_write_error(f'Caution! No h-parameters passed. '
                            f'{self.__class__.__name__}.{self.generate_file.__name__}')
            return

        self.__include_content = tools_generator.get_includes_content(self.h_params)

        self.__code_content = '\n'
        self.__code_content += self.__get_root_content()

        self.__render_file()

# ---------------------------------------------------------------------------
# Exi decoder generating code file
# ---------------------------------------------------------------------------


class ExiDecoderCode(ExiBaseCoderCode):
    def __init__(self, parameters, analyzer_data, enable_logging=True):
        super(ExiDecoderCode, self).__init__(parameters, analyzer_data, enable_logging)

        self.__is_iso20 = str(self.parameters['prefix']).startswith('iso20_')

        self.__include_content = ''
        self.__code_content = ''
        self.__function_content = ''

    # ---------------------------------------------------------------------------
    # generator helper functions
    # ---------------------------------------------------------------------------
    def get_function_declaration(self, element_name, is_forward_declaration):
        content = 'static '
        content += 'int ' + self.config['decode_function_prefix'] + self.parameters['prefix'] + element_name + '('
        content += 'exi_bitstream_t* stream, '
        content += 'struct ' + self.parameters['prefix'] + element_name + '* ' + element_name + ')'

        if is_forward_declaration:
            content += ';'

        return content

    # ---------------------------------------------------------------------------
    # content delivery functions
    # ---------------------------------------------------------------------------
    def __get_content_decode_hex_binary(self, element_typename, detail: ElementGrammarDetail, level):
        decode_comment = '// decode exi type: hexBinary'
        if detail.particle.is_attribute:
            decode_comment += ' (Attribute)'
        if detail.particle.parent_has_choice_sequence:
            type_value = \
                f'{element_typename}->choice_{detail.particle.parent_choice_sequence_number}.{detail.particle.name}'
            type_content = type_value + f'.{detail.particle.value_parameter_name}'
            type_content_len = type_value + f'.{detail.particle.length_parameter_name}'
        else:
            type_value = f'{element_typename}->{detail.particle.name}'
            type_content = type_value + f'.{detail.particle.value_parameter_name}'
            type_content_len = type_value + f'.{detail.particle.length_parameter_name}'
        type_define = detail.particle.prefixed_define_for_base_type
        next_grammar_id = detail.next_grammar

        temp = self.generator.get_template('DecodeTypeHexBinary.jinja')
        decode_content = temp.render(decode_comment=decode_comment,
                                     type_value=type_value,
                                     type_content=type_content,
                                     type_content_len=type_content_len,
                                     type_define=type_define,
                                     type_option=detail.particle.is_optional,
                                     next_grammar_id=next_grammar_id,
                                     indent=self.indent, level=level)

        return decode_content

    def __get_content_decode_base64_binary_simple(self, element_typename, detail: ElementGrammarDetail, level):
        decode_comment = '// decode exi type: base64Binary (simple)'
        type_value = f'{element_typename}->{detail.particle.name}'
        type_content = type_value + f'.{detail.particle.value_parameter_name}'
        type_content_len = type_value + f'.{detail.particle.length_parameter_name}'

        type_define = detail.particle.prefixed_define_for_base_type
        next_grammar_id = detail.next_grammar

        temp = self.generator.get_template('DecodeTypeBase64BinarySimple.jinja')
        decode_content = temp.render(decode_comment=decode_comment,
                                     type_value=type_value,
                                     type_content=type_content,
                                     type_content_len=type_content_len,
                                     type_define=type_define,
                                     type_option=detail.particle.is_optional,
                                     next_grammar_id=next_grammar_id,
                                     indent=self.indent, level=level)

        return decode_content

    def __get_content_decode_base64_binary(self, element_typename, detail: ElementGrammarDetail, level):
        decode_comment = '// decode exi type: base64Binary'
        if detail.particle.is_attribute:
            decode_comment += ' (Attribute)'
        if detail.particle.parent_has_choice_sequence:
            type_value = \
                f'{element_typename}->choice_{detail.particle.parent_choice_sequence_number}.{detail.particle.name}'
            type_content = type_value + f'.{detail.particle.value_parameter_name}'
            type_content_len = type_value + f'.{detail.particle.length_parameter_name}'
        elif detail.particle.has_simple_content:
            type_value = f'{element_typename}->{detail.particle.name}.CONTENT'
            type_content = type_value + f'.{detail.particle.value_parameter_name}'
            type_content_len = type_value + f'.{detail.particle.length_parameter_name}'
        else:
            if detail.particle.max_occurs > 1:
                decode_comment += ' (Array)'
                type_array_length = f'{element_typename}->{detail.particle.name}.arrayLen'
                type_value = f'{element_typename}->{detail.particle.name}'
                type_content_len = type_value + f'.array[{type_array_length}].{detail.particle.length_parameter_name}'
                type_content = type_value + f'.array[{type_array_length}].{detail.particle.value_parameter_name}'
            else:
                type_value = f'{element_typename}->{detail.particle.name}'
                type_content = type_value + f'.{detail.particle.value_parameter_name}'
                type_content_len = type_value + f'.{detail.particle.length_parameter_name}'

        type_define = detail.particle.prefixed_define_for_base_type
        next_grammar_id = detail.next_grammar

        temp = self.generator.get_template('DecodeTypeBase64Binary.jinja')
        decode_content = temp.render(decode_comment=decode_comment,
                                     type_value=type_value,
                                     type_content=type_content,
                                     type_content_len=type_content_len,
                                     type_define=type_define,
                                     type_option=detail.particle.is_optional,
                                     type_array=detail.particle.max_occurs > 1,
                                     type_array_length=f'{element_typename}->{detail.particle.name}.arrayLen',
                                     type_array_define=detail.particle.prefixed_define_for_array,
                                     next_grammar_id=next_grammar_id,
                                     indent=self.indent, level=level)

        return decode_content

    def __get_content_decode_boolean(self, element_typename, detail: ElementGrammarDetail, level):
        decode_comment = '// decode: boolean'
        if detail.particle.is_attribute:
            decode_comment += ' (Attribute)'
        type_value = f'{element_typename}->{detail.particle.name}'
        next_grammar_id = detail.next_grammar

        temp = self.generator.get_template('DecodeTypeBoolean.jinja')
        decode_content = temp.render(decode_comment=decode_comment,
                                     bits_to_decode=detail.particle.bit_count_for_coding,
                                     type_value=type_value,
                                     type_option=detail.particle.is_optional,
                                     next_grammar_id=next_grammar_id,
                                     indent=self.indent, level=level)

        return decode_content

    def __get_content_decode_byte(self, element_typename, detail: ElementGrammarDetail, level):
        type_value = f'{element_typename}->{detail.particle.name}'
        next_grammar_id = detail.next_grammar

        if detail.particle.integer_is_unsigned:
            decode_comment = '// decode: unsigned byte (restricted integer)'
        else:
            decode_comment = '// decode: byte (restricted integer)'
        if detail.particle.is_attribute:
            decode_comment += ' (Attribute)'
        temp = self.generator.get_template('DecodeTypeRestrictedInt.jinja')
        decode_content = temp.render(decode_comment=decode_comment,
                                     bits_to_decode=8,
                                     type_value=type_value,
                                     type_offset=(0 if detail.particle.integer_is_unsigned else -128),
                                     type_int=tools.TYPE_TRANSLATION_C[detail.particle.integer_base_type],
                                     type_option=detail.particle.is_optional,
                                     next_grammar_id=next_grammar_id,
                                     indent=self.indent, level=level)

        return decode_content

    def __get_content_decode_restricted(self, element_typename, detail: ElementGrammarDetail, level):
        decode_comment = '// decode: restricted integer (4096 or fewer values)'
        if detail.particle.is_attribute:
            decode_comment += ' (Attribute)'
        type_value = f'{element_typename}->{detail.particle.name}'
        type_offset = detail.particle.min_value
        next_grammar_id = detail.next_grammar

        temp = self.generator.get_template('DecodeTypeRestrictedInt.jinja')
        decode_content = temp.render(decode_comment=decode_comment,
                                     bits_to_decode=detail.particle.bit_count_for_coding,
                                     type_value=type_value,
                                     type_offset=type_offset,
                                     type_int=tools.TYPE_TRANSLATION_C[detail.particle.integer_base_type],
                                     type_option=detail.particle.is_optional,
                                     next_grammar_id=next_grammar_id,
                                     indent=self.indent, level=level)

        return decode_content

    def __get_content_decode_short(self, element_typename, detail: ElementGrammarDetail, level):
        type_value = f'{element_typename}->{detail.particle.name}'
        next_grammar_id = detail.next_grammar

        if detail.particle.integer_is_unsigned:
            template_file = 'DecodeTypeUnsignedShort.jinja'
            decode_comment = '// decode: unsigned short'
        else:
            template_file = 'DecodeTypeShort.jinja'
            decode_comment = '// decode: short'
        if detail.particle.is_attribute:
            decode_comment += ' (Attribute)'
        temp = self.generator.get_template(template_file)

        decode_content = temp.render(decode_comment=decode_comment,
                                     type_value=type_value,
                                     type_option=detail.particle.is_optional,
                                     next_grammar_id=next_grammar_id,
                                     indent=self.indent, level=level)

        return decode_content

    def __get_content_decode_short_array(self, element_typename, detail: ElementGrammarDetail, level):
        type_array = f'{element_typename}->{detail.particle.name}.{detail.particle.value_parameter_name}'
        type_array_len = f'{element_typename}->{detail.particle.name}.{detail.particle.length_parameter_name}'
        next_grammar_id = detail.next_grammar

        template_file = 'DecodeTypeElementArray.jinja'
        if detail.particle.integer_is_unsigned:
            decode_comment = '// decode: unsigned short array'
            decode_fn = 'decode_exi_type_uint16'
        else:
            decode_comment = '// decode: short array'
            decode_fn = 'decode_exi_type_integer16'
        temp = self.generator.get_template(template_file)

        decode_content = temp.render(decode_comment=decode_comment,
                                     type_define=detail.particle.prefixed_define_for_array,
                                     type_array=type_array,
                                     type_array_len=type_array_len,
                                     decode_fn=decode_fn,
                                     type_value=type_array,
                                     type_option=detail.particle.is_optional,
                                     next_grammar_id=next_grammar_id,
                                     indent=self.indent, level=level)

        return decode_content

    def __get_content_decode_int(self, element_typename, detail: ElementGrammarDetail, level):
        type_value = f'{element_typename}->{detail.particle.name}'
        next_grammar_id = detail.next_grammar

        if detail.particle.integer_is_unsigned:
            template_file = 'DecodeTypeUnsignedInt.jinja'
            decode_comment = '// decode: unsigned int'
        else:
            template_file = 'DecodeTypeInt.jinja'
            decode_comment = '// decode: int'
        if detail.particle.is_attribute:
            decode_comment += ' (Attribute)'
        temp = self.generator.get_template(template_file)
        decode_content = temp.render(decode_comment=decode_comment,
                                     type_value=type_value,
                                     type_option=detail.particle.is_optional,
                                     next_grammar_id=next_grammar_id,
                                     indent=self.indent, level=level)

        return decode_content

    def __get_content_decode_long_int(self, element_typename, detail: ElementGrammarDetail, level):
        type_value = f'{element_typename}->{detail.particle.name}'
        next_grammar_id = detail.next_grammar

        if detail.particle.integer_is_unsigned:
            template_file = 'DecodeTypeUnsignedLongInt.jinja'
            decode_comment = '// decode: unsigned long int'
        else:
            template_file = 'DecodeTypeLongInt.jinja'
            decode_comment = '// decode: long int'
        if detail.particle.is_attribute:
            decode_comment += ' (Attribute)'
        temp = self.generator.get_template(template_file)
        decode_content = temp.render(decode_comment=decode_comment,
                                     type_value=type_value,
                                     type_option=detail.particle.is_optional,
                                     next_grammar_id=next_grammar_id,
                                     indent=self.indent, level=level)

        return decode_content

    def __get_content_decode_string(self, element_typename, detail: ElementGrammarDetail, level):
        decode_comment = '// decode: string (len, characters)'
        if detail.particle.is_attribute:
            decode_comment += ' (Attribute)'
        type_value = f'{element_typename}->{detail.particle.name}'
        type_length = type_value + f'.{detail.particle.length_parameter_name}'
        type_chars = type_value + f'.{detail.particle.value_parameter_name}'
        type_chars_size = detail.particle.prefixed_define_for_base_type
        next_grammar_id = detail.next_grammar

        if detail.particle.max_occurs > 1:
            decode_comment += ' (Array)'
            type_array_length = f'{element_typename}->{detail.particle.name}.arrayLen'
            type_length = type_value + f'.array[{type_array_length}].{detail.particle.length_parameter_name}'
            type_chars = type_value + f'.array[{type_array_length}].{detail.particle.value_parameter_name}'

        temp = self.generator.get_template('DecodeTypeString.jinja')
        decode_content = temp.render(decode_comment=decode_comment,
                                     type_value=type_value,
                                     type_length=type_length,
                                     type_chars=type_chars,
                                     type_chars_size=type_chars_size,
                                     type_option=detail.particle.is_optional,
                                     type_attribute=detail.particle.is_attribute,
                                     type_array=detail.particle.max_occurs > 1,
                                     type_array_length=f'{element_typename}->{detail.particle.name}.arrayLen',
                                     type_array_define=detail.particle.prefixed_define_for_array,
                                     next_grammar_id=next_grammar_id,
                                     indent=self.indent, level=level)

        return decode_content

    def __get_content_decode_element_array(self, element_typename, detail: ElementGrammarDetail, level):
        decode_comment = '// decode: element array'
        if detail.particle.is_attribute:
            decode_comment += ' (Attribute)'
        type_array = f'{element_typename}->{detail.particle.name}.{detail.particle.value_parameter_name}'
        type_array_len = f'{element_typename}->{detail.particle.name}.{detail.particle.length_parameter_name}'
        decode_fn = f'{CONFIG_PARAMS["decode_function_prefix"]}{detail.particle.prefixed_type}'
        next_grammar_id = detail.next_grammar

        temp = self.generator.get_template('DecodeTypeElementArray.jinja')
        # FIXME support optional element arrays (need to define type_value as well)
        decode_content = temp.render(decode_comment=decode_comment,
                                     type_define=detail.particle.prefixed_define_for_array,
                                     type_array=type_array,
                                     type_array_len=type_array_len,
                                     decode_fn=decode_fn,
                                     next_grammar_id=next_grammar_id,
                                     indent=self.indent, level=level)

        return decode_content

    def __get_content_decode_namespace_element(self, element_typename, particle: Particle, next_grammar, level):
        decode_comment = '// decode: namespace element'
        decode_fn = f'{CONFIG_PARAMS["decode_function_prefix"]}{particle.prefixed_type}'
        type_value = f'{element_typename}->{particle.name}'
        next_grammar_id = next_grammar

        temp = self.generator.get_template('DecodeTypeElement.jinja')
        decode_content = temp.render(decode_comment=decode_comment,
                                     decode_fn=decode_fn,
                                     type_option=particle.is_optional,
                                     type_value=type_value,
                                     next_grammar_id=next_grammar_id,
                                     indent=self.indent, level=level)

        return decode_content

    def __get_content_decode_element(self, element_typename, detail: ElementGrammarDetail, level):
        decode_comment = '// decode: element'
        if detail.particle.is_attribute:
            decode_comment += ' (Attribute)'
        decode_fn = f'{CONFIG_PARAMS["decode_function_prefix"]}{detail.particle.prefixed_type}'
        type_value = f'{element_typename}->{detail.particle.name}'
        next_grammar_id = detail.next_grammar

        temp = self.generator.get_template('DecodeTypeElement.jinja')
        decode_content = temp.render(decode_comment=decode_comment,
                                     decode_fn=decode_fn,
                                     type_option=detail.particle.is_optional,
                                     type_value=type_value,
                                     next_grammar_id=next_grammar_id,
                                     indent=self.indent, level=level)

        return decode_content

    def __get_content_decode_enum_array(self, element_typename, detail: ElementGrammarDetail, level):
        decode_comment = '// decode: enum array'
        if detail.particle.is_attribute:
            decode_comment += ' (Attribute)'
        type_value = f'{element_typename}->{detail.particle.name}.{detail.particle.value_parameter_name}'
        type_array_len = f'{element_typename}->{detail.particle.name}.{detail.particle.length_parameter_name}'
        type_enum = detail.particle.prefixed_type
        next_grammar_id = detail.next_grammar

        temp = self.generator.get_template('DecodeTypeEnumArray.jinja')
        decode_content = temp.render(decode_comment=decode_comment,
                                     type_array_len=type_array_len,
                                     type_define=detail.particle.prefixed_define_for_array,
                                     bits_to_decode=detail.particle.bit_count_for_coding,
                                     type_option=detail.particle.is_optional,
                                     type_value=type_value,
                                     type_enum=type_enum,
                                     next_grammar_id=next_grammar_id,
                                     indent=self.indent, level=level)

        return decode_content

    def __get_content_decode_enum(self, element_typename, detail: ElementGrammarDetail, level):
        decode_comment = '// decode: enum'
        if detail.particle.is_attribute:
            decode_comment += ' (Attribute)'
        type_value = f'{element_typename}->{detail.particle.name}'
        type_enum = detail.particle.prefixed_type
        next_grammar_id = detail.next_grammar

        temp = self.generator.get_template('DecodeTypeEnum.jinja')
        decode_content = temp.render(decode_comment=decode_comment,
                                     bits_to_decode=detail.particle.bit_count_for_coding,
                                     type_option=detail.particle.is_optional,
                                     type_attribute=detail.particle.is_attribute,
                                     type_value=type_value,
                                     type_enum=type_enum,
                                     next_grammar_id=next_grammar_id,
                                     indent=self.indent, level=level)

        return decode_content

    def __get_content_decode_no_event(self, element_typename, detail: ElementGrammarDetail, level):
        decode_comment = '// decode: event not accepted'
        temp = self.generator.get_template('DecodeTypeNoEvent.jinja')
        decode_content = temp.render(decode_comment=decode_comment,
                                     indent=self.indent, level=level)

        return decode_content

    def __get_content_decode_not_implemented(self, element_typename, detail: ElementGrammarDetail, level):
        decode_comment = f"// tbd! decode: '{detail.particle.type_short}', base type '{detail.particle.typename}"
        temp = self.generator.get_template('DecodeTypeNotImplemented.jinja')
        decode_content = temp.render(decode_comment=decode_comment,
                                     indent=self.indent, level=level)

        return decode_content

    def __get_type_content(self, grammar: ElementGrammar, detail: ElementGrammarDetail, level):
        if detail.particle is None:
            temp = self.generator.get_template('BaseDecodeEndElement.jinja')
            return temp.render(next_grammar=detail.next_grammar, indent=self.indent, level=level)

        # default content for types not covered below
        type_content = self.__get_content_decode_not_implemented(grammar.element_typename, detail, level)

        if detail.is_any and detail.any_is_dummy:
            type_content = self.__get_content_decode_no_event(grammar.element_typename, detail, level)
        elif detail.particle.is_enum:
            if detail.particle.is_array:
                type_content = self.__get_content_decode_enum_array(grammar.element_typename, detail, level)
            else:
                type_content = self.__get_content_decode_enum(grammar.element_typename, detail, level)
        elif detail.particle.integer_base_type and detail.particle.integer_base_type != 'char':
            if detail.particle.type_is_restricted_int:  # max 12 bits (0..4095)
                type_content = self.__get_content_decode_restricted(grammar.element_typename, detail, level)
            elif detail.particle.integer_base_type == 'boolean':
                type_content = self.__get_content_decode_boolean(grammar.element_typename, detail, level)
            elif detail.particle.integer_base_type == 'int8':
                type_content = self.__get_content_decode_byte(grammar.element_typename, detail, level)
            elif detail.particle.integer_base_type == 'int16':
                type_content = self.__get_content_decode_short(grammar.element_typename, detail, level)
            elif detail.particle.integer_base_type == 'int32':
                type_content = self.__get_content_decode_int(grammar.element_typename, detail, level)
            elif detail.particle.integer_base_type == 'int64':
                type_content = self.__get_content_decode_long_int(grammar.element_typename, detail, level)
            elif detail.particle.integer_base_type == 'uint8':
                type_content = self.__get_content_decode_byte(grammar.element_typename, detail, level)
            elif detail.particle.integer_base_type == 'uint16':
                if detail.particle.is_array:
                    type_content = self.__get_content_decode_short_array(grammar.element_typename, detail, level)
                else:
                    type_content = self.__get_content_decode_short(grammar.element_typename, detail, level)
            elif detail.particle.integer_base_type == 'uint32':
                type_content = self.__get_content_decode_int(grammar.element_typename, detail, level)
            elif detail.particle.integer_base_type == 'uint64':
                type_content = self.__get_content_decode_long_int(grammar.element_typename, detail, level)
            else:
                log_write_error(f"Unhandled numeric type: '{detail.particle.name}': "
                                f"'{detail.particle.type_short}', " +
                                f"integer_base_type = '{detail.particle.integer_base_type}'")
        elif detail.particle.typename not in self.analyzer_data.schema_builtin_types.keys():
            if not detail.particle.simple_type_is_string:
                if detail.particle.is_array:
                    type_content = self.__get_content_decode_element_array(grammar.element_typename, detail, level)
                else:
                    type_content = self.__get_content_decode_element(grammar.element_typename, detail, level)
            else:
                log_write_error(f"Unhandled fallthrough type: '{detail.particle.name}': {grammar.element_typename}")
        else:
            if detail.particle.is_complex:
                type_content = self.__get_content_decode_element(grammar.element_typename, detail, level)
            elif detail.particle.simple_type_is_string:
                type_content = self.__get_content_decode_string(grammar.element_typename, detail, level)
            elif detail.particle.typename == 'nonNegativeInteger' and detail.particle.type_short == 'unsignedLong':
                type_content = self.__get_content_decode_long_int(grammar.element_typename, detail, level)
            elif detail.particle.typename == 'hexBinary':
                type_content = self.__get_content_decode_hex_binary(grammar.element_typename, detail, level)
            elif detail.particle.typename == 'base64Binary':
                if detail.particle.is_simple_content:
                    type_content = self.__get_content_decode_base64_binary_simple(grammar.element_typename,
                                                                                  detail, level)
                else:
                    type_content = self.__get_content_decode_base64_binary(grammar.element_typename, detail, level)
            elif detail.particle.typename == 'integer':
                if detail.particle.integer_bit_size == 64:
                    if not detail.particle.integer_is_unsigned:
                        type_content = self.__get_content_decode_long_int(grammar.element_typename, detail, level)
            else:
                log_write_error(f"Unhandled type: '{detail.particle.name}': '{detail.particle.type_short}', " +
                                f"base type '{detail.particle.typename}'")

        return type_content

    def __get_event_content(self, grammar: ElementGrammar, level):
        event_content = ''

        if grammar.details[0].flag != GrammarFlag.ERROR:
            detail: ElementGrammarDetail = None
            for detail in grammar.details:
                if detail.flag == GrammarFlag.END:
                    event_comment = f'// Event: {detail.flag}; ' + \
                                    f'next={detail.next_grammar}'
                elif detail.particle is not None:
                    if detail.particle.abstract or detail.particle.abstract_type:
                        event_comment = (f'// Abstract element or type: {detail.particle.name}, '
                                         f'{detail.particle.type_short} ({detail.particle.typename})')
                    else:
                        event_comment = f'// Event: {detail.flag} ({detail.particle.name}, ' + \
                                        f'{detail.particle.type_short} ({detail.particle.typename})); ' + \
                                        f'next={detail.next_grammar}'
                else:
                    # unsupported particle which appears in the event list
                    event_comment = f'// Event: {detail.flag} (None); next={detail.next_grammar}'

                # currently not used, should be removed if it seems not to be useful!
                # add_debug_code = self.get_status_for_add_debug_code(grammar.element_typename)
                # type_parameter = CONFIG_PARAMS['decode_function_prefix'] + grammar.element_typename
                temp = self.generator.get_template('BaseDecodeCaseEventId.jinja')
                event_content += temp.render(event_id=detail.event_index,
                                             event_id_comment=event_comment,
                                             type_content=self.__get_type_content(grammar, detail, 5),
                                             # add_debug_code=add_debug_code,
                                             # type_parameter=type_parameter,
                                             indent=self.indent, level=level)
                event_content += '\n'

        return self.trim_lf(event_content)

    def __get_grammar_content_namespace_elements(self, element: ElementData, grammars: List[ElementGrammar], level):
        grammar_content = ''

        for grammar in grammars:
            if grammar.details[0].flag == GrammarFlag.START:
                names = [particle.name for particle in element.particles]
                names.sort()

                bits_to_read = tools.get_bits_to_decode(len(names))
                grammar_comment = f'// Grammar: ID={grammar.grammar_id}; read bits={bits_to_read}; START (BodyMessage)'
                next_grammar = grammar.details[0].next_grammar
                type_parameter = CONFIG_PARAMS['decode_function_prefix'] + element.prefixed_name

                event_content = ''
                event_index = 0
                for name in names:
                    hits = [x for x in element.particles if x.name == name]
                    type_content = self.__get_content_decode_namespace_element(element.typename, hits[0],
                                                                               next_grammar, level + 3)

                    event_comment = f'// Event: {hits[0].name}'
                    temp = self.generator.get_template('BaseDecodeCaseEventId.jinja')
                    event_content += temp.render(event_id=event_index,
                                                 event_id_comment=event_comment,
                                                 type_content=type_content,
                                                 indent=self.indent, level=level + 2)
                    event_content += '\n'
                    event_index += 1

                temp = self.generator.get_template('BaseDecodeCaseGrammarId.jinja')
                grammar_content += temp.render(grammar_id=grammar.grammar_id,
                                               grammar_id_comment=grammar_comment,
                                               bits_to_read=bits_to_read,
                                               event_content=event_content,
                                               add_debug_code=self.get_status_for_add_debug_code(element.prefixed_name),
                                               type_parameter=type_parameter,
                                               indent=self.indent, level=level)
            elif grammar.details[0].flag == GrammarFlag.END:
                temp = self.generator.get_template('BaseDecodeCaseGrammarId.jinja')
                grammar_content += temp.render(grammar_id=grammar.grammar_id,
                                               grammar_id_comment=grammar.grammar_comment,
                                               bits_to_read=grammar.bits_to_read,
                                               event_content=self.__get_event_content(grammar, 4),
                                               indent=self.indent, level=level)

            grammar_content += '\n'

        return self.trim_lf(grammar_content)

    def __get_grammar_content(self, grammars: List[ElementGrammar], level):
        grammar_content = ''

        for grammar in grammars:
            if grammar.details[0].flag == GrammarFlag.ERROR:
                continue

            add_debug_code = 0
            type_parameter = ''
            for detail in grammar.details:
                if detail.flag == GrammarFlag.START and detail.particle is not None:
                    prefixed_type = detail.particle.prefixed_name
                    add_debug_code = self.get_status_for_add_debug_code(prefixed_type)
                    type_parameter = CONFIG_PARAMS['decode_function_prefix'] + prefixed_type
                    break

            temp = self.generator.get_template('BaseDecodeCaseGrammarId.jinja')
            grammar_content += temp.render(grammar_id=grammar.grammar_id,
                                           grammar_id_comment=grammar.grammar_comment,
                                           bits_to_read=grammar.bits_to_read,
                                           event_content=self.__get_event_content(grammar, 4),
                                           add_debug_code=add_debug_code,
                                           type_parameter=type_parameter,
                                           indent=self.indent, level=level)

            grammar_content += '\n'

        return self.trim_lf(grammar_content)

    def __get_function_content(self, element: ElementData, grammars: List[ElementGrammar]):
        typename = element.typename
        content = ''

        start_grammar_id = self.get_start_grammar_id(grammars)
        if start_grammar_id >= 0:
            if element.is_in_namespace_elements:
                grammar_content = self.__get_grammar_content_namespace_elements(element, grammars, 2)
            else:
                grammar_content = self.__get_grammar_content(grammars, 2)

            temp = self.generator.get_template('BaseDecodeFunction.jinja')
            content += temp.render(element_comment=element.element_comment,
                                   particle_comment=element.particle_comment,
                                   function_name=CONFIG_PARAMS['decode_function_prefix'] + element.prefixed_type,
                                   struct_type=element.prefixed_type, parameter_name=typename,
                                   start_grammar_id=start_grammar_id,
                                   init_function=CONFIG_PARAMS['init_function_prefix'] + element.prefixed_type,
                                   grammar_content=grammar_content,
                                   add_debug_code=self.get_status_for_add_debug_code(element.prefixed_type),
                                   indent=self.indent, level=1)
            content += '\n\n'
        else:
            temp = self.generator.get_template('DecodeEmptyFunction.jinja')
            content += temp.render(element_comment=element.element_comment,
                                   function_name=CONFIG_PARAMS['decode_function_prefix'] + element.prefixed_type,
                                   struct_type=element.prefixed_type, parameter_name=typename,
                                   add_debug_code=self.get_status_for_add_debug_code(element.prefixed_type),
                                   indent=self.indent, level=1)
            content += '\n\n'

        return content

    def __get_root_content(self):
        root_content = ''
        root_comment = '// main function for decoding'
        fn_name = CONFIG_PARAMS['decode_function_prefix'] + self.parameters['prefix'] + \
            CONFIG_PARAMS['root_struct_name']
        struct_type = self.parameters['prefix'] + CONFIG_PARAMS['root_struct_name']
        parameter_name = CONFIG_PARAMS['root_parameter_name']
        init_fn = CONFIG_PARAMS['init_function_prefix'] + self.parameters['prefix'] + CONFIG_PARAMS['root_struct_name']

        if len(self.analyzer_data.root_elements) == 0:
            log_write_error(f'No root elements in analyzer data. Main function {fn_name} is not generated.')
        elif len(self.analyzer_data.root_elements) > 1:
            decode_fn = []
            for elem in self.analyzer_data.root_elements:
                if self.__is_iso20:
                    # TODO: The following if filters the simple types DigestValue, MgmtData and KeyName.
                    #       Simple types has to be decoded directly and not with an decoding function.
                    #       So it has to be checked if these types can be ignored here or
                    #       the decoding has to be implemented.
                    #       Currently an empty case with the event code is generated.
                    prefix_name_short = f'{elem.prefix}{elem.name_short}'
                    if elem.type_definition == 'complex':
                        decode_fn.append([CONFIG_PARAMS['decode_function_prefix'] + elem.prefixed_type,
                                          parameter_name + '->' + elem.name_short])
                    else:
                        decode_fn.append([f'{CONFIG_PARAMS["decode_function_prefix"]}{prefix_name_short}', ''])
                else:
                    if elem.typename in self.analyzer_data.schema_builtin_types:
                        decode_fn.append([f'{CONFIG_PARAMS["decode_function_prefix"]}{elem.prefix}{elem.name_short}',
                                          f'{parameter_name}->{elem.prefix}{elem.name_short}'])
                    else:
                        decode_fn.append([CONFIG_PARAMS['decode_function_prefix'] + elem.prefixed_type,
                                          parameter_name + '->' + elem.typename])

            decode_fn.sort()

            bits = tools.get_bits_to_decode(len(self.analyzer_data.root_elements))

            temp = self.generator.get_template('DecodeRootFunction.jinja')
            root_content += temp.render(function_comment=root_comment,
                                        function_name=fn_name,
                                        struct_type=struct_type, parameter_name=parameter_name,
                                        init_function=init_fn,
                                        bits_to_read=bits,
                                        decode_functions=decode_fn,
                                        indent=self.indent)
            root_content += '\n'
        else:
            name_short = self.analyzer_data.root_elements[0].name_short
            if name_short in self.analyzer_data.namespace_elements:
                function = ''
                parameter = ''
                parameter_index = 0
                for name in sorted(self.analyzer_data.namespace_elements[name_short]):
                    if name == name_short:
                        function = CONFIG_PARAMS['decode_function_prefix'] + self.parameters['prefix'] + name
                        parameter = parameter_name + '->' + name
                        if parameter.casefold().endswith('type'):
                            parameter = parameter[:len(parameter) - 4]
                        break

                    parameter_index += 1

                bits = tools.get_bit_count_for_value(len(self.analyzer_data.namespace_elements[name_short]))
                temp = self.generator.get_template('DecodeRootV2GMessage.jinja')
                root_content += temp.render(function_comment=root_comment,
                                            function_name=fn_name,
                                            struct_type=struct_type, parameter_name=parameter_name,
                                            bits_to_encode=bits,
                                            function=function,
                                            parameter=parameter, parameter_index=parameter_index,
                                            indent=self.indent)
                root_content += '\n'
            else:
                log_write_error(f'No match found in namespace elements. Main function {fn_name} is not generated.')

        return root_content

    def __render_file(self):
        try:
            temp = self.generator.get_template("DatatypesDecoder.c.jinja")
            code = temp.render(filename=self.c_params["filename"], filekey=self.c_params["identifier"],
                               includes_code=self.__include_content, code=self.__code_content)
            tools.save_code_to_file(self.c_params["filename"], code, self.parameters['folder'])
        except KeyError as err:
            log_write_error(f'Exception in {self.__class__.__name__}.{self.__render_file.__name__} '
                            f'(KeyError): {err}')

    # ---------------------------------------------------------------------------
    # general generator functions
    # ---------------------------------------------------------------------------
    def generate_file(self):
        if self.c_params is None:
            log_write_error(f'Caution! No c-parameters passed. '
                            f'{self.__class__.__name__}.{self.generate_file.__name__}')
            return

        self.__include_content = tools_generator.get_includes_content(self.c_params)
        self.__code_content = ''
        self.__function_content = ''

        analyzed_elements = {}
        static_declarations = []

        self.reset_grammar_ids()
        self.init_lists_for_generating_elements()
        self.init_list_with_known_type_names()

        curr_idx = 0
        while_count = 0
        while len(self.elements_to_generate) > 0:
            # loop should not run forever
            while_count += 1
            if while_count > 10000:
                log_write_error('Module decoder: Generator loop aborted! Loop counter exceeded.')
                break

            element: ElementData = self.elements_to_generate[curr_idx]
            elem_typename = element.typename
            skip_element = self.test_on_skip(element)

            if skip_element:
                curr_idx += 1
                if curr_idx > len(self.elements_to_generate):
                    log_write_error('Module decoder: Generator loop aborted! Index larger than existing elements.')
                    break
            else:
                self.log(f'Grammar for {elem_typename}')
                self.log(element.element_comment)
                self.log(element.particle_comment)

                # get forward declarations
                static_declarations.append(self.get_function_declaration(elem_typename, True))

                # determine grammar ids for calculating bits to read from stream
                self.generate_element_grammars(element)

                if self.grammar_end_element == 0:
                    self.grammar_end_element = self.grammar_id
                    self.grammar_unknown = self.grammar_id + 1
                    self.grammar_id += 2

                self.append_end_and_unknown_grammars(element.typename)

                self.log('')
                self.generate_event_info(self.element_grammars, element)
                self.log('')
                analyzed_elements[elem_typename] = self.element_grammars

                self.__function_content += self.__get_function_content(element, self.element_grammars)

                # add element to list of generated ane remove from list to generate and reset element index
                self.elements_generated.append(elem_typename)
                self.elements_to_generate.remove(element)
                curr_idx = 0

        # from here on all forward declarations are known
        for line in static_declarations:
            self.__code_content += line + '\n'

        self.__code_content += '\n'
        self.__code_content += self.__function_content

        self.__code_content += '\n'
        self.__code_content += self.__get_root_content()

        self.__render_file()
