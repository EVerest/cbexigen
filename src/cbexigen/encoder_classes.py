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
# Exi encoder generating header file
# ---------------------------------------------------------------------------


class ExiEncoderHeader(ExiBaseCoderHeader):
    def __init__(self, parameters, enable_logging=True):
        super(ExiEncoderHeader, self).__init__(parameters=parameters, enable_logging=enable_logging)

        self.__is_iso20 = True if str(self.parameters['prefix']).startswith('iso20_') else False

        self.__include_content = ''
        self.__code_content = ''

    def __get_root_content(self):
        content = '// main function for encoding\n'

        name = self.parameters['prefix'] + self.config['root_struct_name']
        content += 'int ' + self.config['encode_function_prefix'] + name + '('
        content += 'exi_bitstream_t* stream, '
        content += 'struct ' + name + '* ' + self.config['root_parameter_name'] + ');'

        return content

    def __render_file(self):
        try:
            temp = self.generator.get_template('DataTypesEncoder.h.jinja')
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
# Exi encoder generating code file
# ---------------------------------------------------------------------------


class ExiEncoderCode(ExiBaseCoderCode):
    def __init__(self, parameters, analyzer_data, enable_logging=True):
        super(ExiEncoderCode, self).__init__(parameters, analyzer_data, enable_logging)

        self.__is_iso20 = True if str(self.parameters['prefix']).startswith('iso20_') else False

        self.__include_content = ''
        self.__code_content = ''
        self.__function_content = ''

    # ---------------------------------------------------------------------------
    # generator helper functions
    # ---------------------------------------------------------------------------
    def get_function_declaration(self, element_name, is_forward_declaration):
        content = 'static '
        content += 'int ' + self.config['encode_function_prefix'] + self.parameters['prefix'] + element_name + '('
        content += 'exi_bitstream_t* stream, '
        content += 'struct ' + self.parameters['prefix'] + element_name + '* ' + element_name + ')'

        if is_forward_declaration:
            content += ';'

        return content

    # ---------------------------------------------------------------------------
    # content delivery functions
    # ---------------------------------------------------------------------------
    def __get_content_encode_hex_binary(self, element_typename, detail: ElementGrammarDetail, level):
        length_parameter = f'{element_typename}->{detail.particle.name}.{detail.particle.length_parameter_name}'
        value_parameter = f'{element_typename}->{detail.particle.name}.{detail.particle.value_parameter_name}'
        size_parameter = f'{detail.particle.prefixed_define_for_base_type}'

        temp = self.generator.get_template('EncodeTypeHexBinary.jinja')
        content = temp.render(length_parameter=length_parameter,
                              value_parameter=value_parameter,
                              size_parameter=size_parameter,
                              next_grammar=detail.next_grammar,
                              indent=self.indent, level=level)

        return self.trim_lf(content)

    def __get_content_encode_base64_binary_simple(self, element_typename, detail: ElementGrammarDetail, level):
        size_parameter = f'{detail.particle.prefixed_define_for_base_type}'
        length_parameter = f'{element_typename}->{detail.particle.name}.{detail.particle.length_parameter_name}'
        value_parameter = f'{element_typename}->{detail.particle.name}.{detail.particle.value_parameter_name}'

        temp = self.generator.get_template('EncodeTypeBase64BinarySimple.jinja')
        content = temp.render(length_parameter=length_parameter,
                              value_parameter=value_parameter,
                              size_parameter=size_parameter,
                              next_grammar=detail.next_grammar,
                              indent=self.indent, level=level)

        return self.trim_lf(content)

    def __get_content_encode_base64_binary(self, element_typename, detail: ElementGrammarDetail, level):
        size_parameter = f'{detail.particle.prefixed_define_for_base_type}'
        type_array_index = detail.particle.name + '_currentIndex'

        if detail.particle.parent_has_choice_sequence:
            length_parameter = f'{element_typename}->choice_{detail.particle.parent_choice_sequence_number}.' \
                               f'{detail.particle.name}.{detail.particle.length_parameter_name}'
            value_parameter = f'{element_typename}->choice_{detail.particle.parent_choice_sequence_number}.' \
                              f'{detail.particle.name}.{detail.particle.value_parameter_name}'
        elif detail.particle.has_simple_content:
            length_parameter = f'{element_typename}->{detail.particle.name}.CONTENT.' \
                               f'{detail.particle.length_parameter_name}'
            value_parameter = f'{element_typename}->{detail.particle.name}.CONTENT.' \
                              f'{detail.particle.value_parameter_name}'
        else:
            length_parameter = f'{element_typename}->{detail.particle.name}.{detail.particle.length_parameter_name}'
            value_parameter = f'{element_typename}->{detail.particle.name}.{detail.particle.value_parameter_name}'

            if detail.particle.is_array:
                length_parameter = (f'{element_typename}->{detail.particle.name}'
                                    f'.array[{type_array_index}].{detail.particle.length_parameter_name}')
                value_parameter = (f'{element_typename}->{detail.particle.name}'
                                   f'.array[{type_array_index}].{detail.particle.value_parameter_name}')

        temp = self.generator.get_template('EncodeTypeBase64Binary.jinja')
        content = temp.render(length_parameter=length_parameter,
                              value_parameter=value_parameter,
                              size_parameter=size_parameter,
                              type_array=detail.particle.is_array,
                              type_array_index=type_array_index,
                              next_grammar=detail.next_grammar,
                              indent=self.indent, level=level)

        return self.trim_lf(content)

    def __get_content_encode_restricted(self, element_typename, detail: ElementGrammarDetail, level):
        value_parameter = f'{element_typename}->{detail.particle.name}'
        bits_to_encode = detail.particle.bit_count_for_coding
        min_value = detail.particle.min_value

        temp = self.generator.get_template('EncodeTypeRestricted.jinja')
        content = temp.render(value_parameter=value_parameter,
                              bits_to_encode=bits_to_encode,
                              min_value=min_value,
                              next_grammar=detail.next_grammar,
                              indent=self.indent, level=level)

        return content

    def __get_content_encode_boolean(self, element_typename, detail: ElementGrammarDetail, level):
        value_parameter = f'{element_typename}->{detail.particle.name}'

        temp = self.generator.get_template('EncodeTypeBoolean.jinja')
        content = temp.render(value_parameter=value_parameter,
                              next_grammar=detail.next_grammar,
                              indent=self.indent, level=level)

        return content

    def __get_content_encode_byte(self, element_typename, detail: ElementGrammarDetail, level):
        value_parameter = f'{element_typename}->{detail.particle.name}'
        value_offset = (0 if detail.particle.integer_is_unsigned else -128)

        if detail.particle.integer_is_unsigned:
            temp = self.generator.get_template('EncodeTypeUnsignedByte.jinja')
        else:
            temp = self.generator.get_template('EncodeTypeByte.jinja')

        content = temp.render(value_parameter=value_parameter,
                              value_offset=value_offset,
                              next_grammar=detail.next_grammar,
                              indent=self.indent, level=level)

        return content

    def __get_content_encode_short(self, element_typename, detail: ElementGrammarDetail, level):
        value_parameter = f'{element_typename}->{detail.particle.name}'

        if detail.particle.integer_is_unsigned:
            temp = self.generator.get_template('EncodeTypeUnsignedShort.jinja')
        else:
            temp = self.generator.get_template('EncodeTypeShort.jinja')

        content = temp.render(value_parameter=value_parameter,
                              next_grammar=detail.next_grammar,
                              indent=self.indent, level=level)

        return content

    def __get_content_encode_unsigned_short_array(self, element_typename, detail: ElementGrammarDetail, level):
        value_parameter = f'{element_typename}->{detail.particle.name}.{detail.particle.value_parameter_name}'
        index_parameter = detail.particle.name + '_currentIndex'

        temp = self.generator.get_template('EncodeTypeUnsignedShortArray.jinja')
        content = temp.render(value_parameter=value_parameter,
                              index_parameter=index_parameter,
                              next_grammar=detail.next_grammar,
                              indent=self.indent, level=level)

        return content

    def __get_content_encode_int(self, element_typename, detail: ElementGrammarDetail, level):
        value_parameter = f'{element_typename}->{detail.particle.name}'

        if detail.particle.integer_is_unsigned:
            temp = self.generator.get_template('EncodeTypeUnsignedInt.jinja')
        else:
            temp = self.generator.get_template('EncodeTypeInt.jinja')

        content = temp.render(value_parameter=value_parameter,
                              next_grammar=detail.next_grammar,
                              indent=self.indent, level=level)

        return content

    def __get_content_encode_long_int(self, element_typename, detail: ElementGrammarDetail, level):
        value_parameter = f'{element_typename}->{detail.particle.name}'

        if detail.particle.integer_is_unsigned:
            temp = self.generator.get_template('EncodeTypeUnsignedInt64.jinja')
        else:
            temp = self.generator.get_template('EncodeTypeInt64.jinja')

        content = temp.render(value_parameter=value_parameter,
                              next_grammar=detail.next_grammar,
                              indent=self.indent, level=level)

        return content

    def __get_content_encode_string(self, element_typename, detail: ElementGrammarDetail, level):
        length_parameter = f'{element_typename}->{detail.particle.name}.{detail.particle.length_parameter_name}'
        value_parameter = f'{element_typename}->{detail.particle.name}.{detail.particle.value_parameter_name}'
        size_parameter = f'{detail.particle.prefixed_define_for_base_type}'

        type_array_index = detail.particle.name + '_currentIndex'
        if detail.particle.is_array:
            length_parameter = (f'{element_typename}->{detail.particle.name}'
                                f'.array[{type_array_index}].{detail.particle.length_parameter_name}')
            value_parameter = (f'{element_typename}->{detail.particle.name}'
                               f'.array[{type_array_index}].{detail.particle.value_parameter_name}')

        temp = self.generator.get_template('EncodeTypeString.jinja')
        content = temp.render(length_parameter=length_parameter,
                              value_parameter=value_parameter,
                              size_parameter=size_parameter,
                              type_attribute=detail.particle.is_attribute,
                              type_array=detail.particle.is_array,
                              type_array_index=type_array_index,
                              next_grammar=detail.next_grammar,
                              indent=self.indent, level=level)

        return self.trim_lf(content)

    def __get_content_encode_element_array(self, element_typename, detail: ElementGrammarDetail, level):
        type_parameter = self.config['encode_function_prefix'] + detail.particle.prefixed_type
        value_parameter = f'{element_typename}->{detail.particle.name}.{detail.particle.value_parameter_name}'
        index_parameter = detail.particle.name + '_currentIndex'

        temp = self.generator.get_template('EncodeTypeElementArray.jinja')
        content = temp.render(type_parameter=type_parameter,
                              value_parameter=value_parameter,
                              index_parameter=index_parameter,
                              next_grammar=detail.next_grammar,
                              indent=self.indent, level=level)

        return content

    def __get_content_encode_namespace_element(self, element_typename, particle: Particle, next_grammar, level):
        type_parameter = self.config['encode_function_prefix'] + particle.prefixed_type
        value_parameter = f'{element_typename}->{particle.name}'

        temp = self.generator.get_template('EncodeTypeElement.jinja')
        content = temp.render(type_parameter=type_parameter,
                              value_parameter=value_parameter,
                              next_grammar=next_grammar,
                              indent=self.indent, level=level)

        return content

    def __get_content_encode_element(self, element_typename, detail: ElementGrammarDetail, level):
        type_parameter = self.config['encode_function_prefix'] + detail.particle.prefixed_type
        value_parameter = f'{element_typename}->{detail.particle.name}'

        temp = self.generator.get_template('EncodeTypeElement.jinja')
        content = temp.render(type_parameter=type_parameter,
                              value_parameter=value_parameter,
                              next_grammar=detail.next_grammar,
                              indent=self.indent, level=level)

        return content

    def __get_content_encode_enum_array(self, element_typename, detail: ElementGrammarDetail, level):
        index_parameter = detail.particle.name + '_currentIndex'
        value_parameter = f'{element_typename}->{detail.particle.name}.{detail.particle.value_parameter_name}'
        bits_to_encode = detail.particle.bit_count_for_coding

        temp = self.generator.get_template('EncodeTypeEnumArray.jinja')
        content = temp.render(value_parameter=value_parameter,
                              bits_to_encode=bits_to_encode,
                              index_parameter=index_parameter,
                              next_grammar=detail.next_grammar,
                              indent=self.indent, level=level)

        return content

    def __get_content_encode_enum(self, element_typename, detail: ElementGrammarDetail, level):
        value_parameter = f'{element_typename}->{detail.particle.name}'
        bits_to_encode = detail.particle.bit_count_for_coding

        temp = self.generator.get_template('EncodeTypeEnum.jinja')
        content = temp.render(value_parameter=value_parameter,
                              bits_to_encode=bits_to_encode,
                              type_attribute=detail.particle.is_attribute,
                              next_grammar=detail.next_grammar,
                              indent=self.indent, level=level)

        return content

    def __get_content_encode_not_implemented(self, element_typename, detail: ElementGrammarDetail, level):
        encode_comment = f"// tbd! decode: '{detail.particle.type_short}', " + \
            f"base type '{detail.particle.typename}'"

        temp = self.generator.get_template('EncodeTypeNotImplemented.jinja')
        content = temp.render(encode_comment=encode_comment,
                              indent=self.indent, level=level)

        return content

    def __get_type_content(self, grammar: ElementGrammar, detail: ElementGrammarDetail, level):
        if detail.particle is None:
            temp = self.generator.get_template('BaseDecodeEndElement.jinja')
            return temp.render(next_grammar=detail.next_grammar, indent=self.indent, level=level)

        # default content for types not covered below
        type_content = self.__get_content_encode_not_implemented(grammar.element_typename, detail, level)

        if detail.particle.is_enum:
            if detail.particle.is_array:
                type_content = self.__get_content_encode_enum_array(grammar.element_typename, detail, level)
            else:
                type_content = self.__get_content_encode_enum(grammar.element_typename, detail, level)
        elif detail.particle.integer_base_type and detail.particle.integer_base_type != 'char':
            if detail.particle.type_is_restricted_int:  # max 12 bits (0..4095)
                type_content = self.__get_content_encode_restricted(grammar.element_typename, detail, level)
            elif detail.particle.integer_base_type == 'boolean':
                type_content = self.__get_content_encode_boolean(grammar.element_typename, detail, level)
            elif detail.particle.integer_base_type == 'int8':
                type_content = self.__get_content_encode_byte(grammar.element_typename, detail, level)
            elif detail.particle.integer_base_type == 'int16':
                type_content = self.__get_content_encode_short(grammar.element_typename, detail, level)
            elif detail.particle.integer_base_type == 'int32':
                type_content = self.__get_content_encode_int(grammar.element_typename, detail, level)
            elif detail.particle.integer_base_type == 'int64':
                type_content = self.__get_content_encode_long_int(grammar.element_typename, detail, level)
            elif detail.particle.integer_base_type == 'uint8':
                type_content = self.__get_content_encode_byte(grammar.element_typename, detail, level)
            elif detail.particle.integer_base_type == 'uint16':
                if detail.particle.is_array:
                    type_content = \
                        self.__get_content_encode_unsigned_short_array(grammar.element_typename, detail, level)
                else:
                    type_content = self.__get_content_encode_short(grammar.element_typename, detail, level)
            elif detail.particle.integer_base_type == 'uint32':
                type_content = self.__get_content_encode_int(grammar.element_typename, detail, level)
            elif detail.particle.integer_base_type == 'uint64':
                type_content = self.__get_content_encode_long_int(grammar.element_typename, detail, level)
            else:
                log_write_error(f"Unhandled numeric type: '{detail.particle.name}': "
                                f"'{detail.particle.type_short}', " +
                                f"integer_base_type = '{detail.particle.integer_base_type}'")
        elif detail.particle.typename not in self.analyzer_data.schema_builtin_types.keys():
            if not detail.particle.simple_type_is_string:
                if detail.particle.is_array:
                    type_content = self.__get_content_encode_element_array(grammar.element_typename, detail, level)
                else:
                    type_content = self.__get_content_encode_element(grammar.element_typename, detail, level)
            else:
                log_write_error(f"Unhandled fallthrough type: '{detail.particle.name}': {grammar.element_typename}")
        else:
            if detail.particle.is_complex:
                type_content = self.__get_content_encode_element(grammar.element_typename, detail, level)
            elif detail.particle.simple_type_is_string:
                type_content = self.__get_content_encode_string(grammar.element_typename, detail, level)
            elif detail.particle.typename == 'nonNegativeInteger' and detail.particle.type_short == 'unsignedLong':
                type_content = self.__get_content_encode_long_int(grammar.element_typename, detail, level)
            elif detail.particle.typename == 'hexBinary':
                type_content = self.__get_content_encode_hex_binary(grammar.element_typename, detail, level)
            elif detail.particle.typename == 'base64Binary':
                if detail.particle.is_simple_content:
                    type_content = self.__get_content_encode_base64_binary_simple(grammar.element_typename,
                                                                                  detail, level)
                else:
                    type_content = self.__get_content_encode_base64_binary(grammar.element_typename, detail, level)
            elif detail.particle.typename == 'integer':
                if detail.particle.integer_bit_size == 64:
                    if not detail.particle.integer_is_unsigned:
                        type_content = self.__get_content_encode_long_int(grammar.element_typename, detail, level)
            else:
                log_write_error(f"Unhandled type: '{detail.particle.name}': '{detail.particle.type_short}', " +
                                f"base type '{detail.particle.typename}'")

        return type_content

    def __get_event_content_for_end_element(self, detail: ElementGrammarDetail, bits_to_write, is_single, level):
        content = ''

        event_comment = f'// Event: {detail.flag}; '
        event_comment += f'next={detail.next_grammar}'
        temp = self.generator.get_template('EncodeEventEndElement.jinja')
        content += temp.render(bits_to_write=bits_to_write,
                               value_to_write=detail.event_index,
                               event_comment=event_comment,
                               next_grammar=detail.next_grammar,
                               is_single_detail=is_single,
                               indent=self.indent, level=level)

        return self.left_trim_lf(content)

    def __get_event_content_for_array_element(self, detail: ElementGrammarDetail, grammar, option, level):
        content = ''
        event_comment = f'// Event: {detail.flag} ({detail.particle.typename}); next={detail.next_grammar}'
        is_single_detail = True if grammar.details_count == 1 else False
        index_parameter = detail.particle.name + '_currentIndex'
        length_parameter = f'{grammar.element_typename}->{detail.particle.name}.arrayLen'
        current_level = level + 2 if option >= 0 else level + 3

        temp = self.generator.get_template('EncodeEventArrayElement.jinja')
        content += temp.render(option=option,
                               index_parameter=index_parameter,
                               length_parameter=length_parameter,
                               bits_to_write=grammar.bits_to_write,
                               value_to_write=detail.event_index,
                               event_comment=event_comment,
                               type_content=self.__get_type_content(grammar, detail, current_level),
                               is_single_detail=is_single_detail,
                               add_debug_code=self.get_status_for_add_debug_code(detail.particle.prefixed_name),
                               type_parameter=CONFIG_PARAMS['encode_function_prefix'] + detail.particle.prefixed_name,
                               indent=self.indent, level=level)

        content += '\n'

        return self.left_trim_lf(content)

    def __get_event_content_for_optional_array_element(self, detail: ElementGrammarDetail, grammar, option, level):
        event_comment = f'// Event: {detail.flag} ({detail.particle.name}, {detail.particle.typename})' \
                        f'; next={detail.next_grammar} (optional array)'
        type_parameter = CONFIG_PARAMS['encode_function_prefix'] + detail.particle.prefixed_name
        index_parameter = detail.particle.name + '_currentIndex'
        length_parameter = (f'{grammar.element_typename}->{detail.particle.name}'
                            f'.{detail.particle.length_parameter_name}')

        temp = self.generator.get_template('EncodeEventOptionalArrayElement.jinja')
        content = temp.render(option=option,
                              index_parameter=index_parameter,
                              length_parameter=length_parameter,
                              bits_to_write=grammar.bits_to_write,
                              value_to_write=detail.event_index,
                              event_comment=event_comment,
                              type_content=self.__get_type_content(grammar, detail, 5),
                              add_debug_code=self.get_status_for_add_debug_code(detail.particle.prefixed_name),
                              type_parameter=type_parameter,
                              indent=self.indent, level=level)

        content += '\n'

        return self.left_trim_lf(content)

    def __get_event_content_for_optional_element(self, detail: ElementGrammarDetail, grammar, option, level):
        content = ''

        if detail.flag == GrammarFlag.END:
            content += self.__get_event_content_for_end_element(detail, grammar.bits_to_write, False, level)
        else:
            if detail.particle is not None and not (detail.is_any and detail.any_is_dummy):
                event_comment = f'// Event: {detail.flag} ({detail.particle.name}, {detail.particle.typename})' \
                                f'; next={detail.next_grammar}'
                type_parameter = CONFIG_PARAMS['encode_function_prefix'] + detail.particle.prefixed_name
                if detail.particle.parent_has_choice_sequence:
                    parameter = f'{grammar.element_typename}->choice_{detail.particle.parent_choice_sequence_number}'
                else:
                    parameter = grammar.element_typename + '->' + detail.particle.name

                temp = self.generator.get_template('EncodeEventOptionalElement.jinja')
                content += temp.render(option=option,
                                       parameter=parameter,
                                       bits_to_write=grammar.bits_to_write,
                                       value_to_write=detail.event_index,
                                       event_comment=event_comment,
                                       type_content=self.__get_type_content(grammar, detail, 5),
                                       add_debug_code=self.get_status_for_add_debug_code(detail.particle.prefixed_name),
                                       type_parameter=type_parameter,
                                       indent=self.indent, level=level)
            else:
                # unsupported particle which appears in the event list
                if detail.is_any and detail.any_is_dummy:
                    event_comment = f'// No code for unsupported generic event: {detail.particle_name} (index={detail.event_index})'
                    temp = self.generator.get_template('EncodeEventOptionalElementNoEvent.jinja')
                    content += temp.render(event_comment=event_comment,
                                           indent=self.indent, level=level)
                else:
                    event_comment = f'// Event: {detail.particle_name} (index={detail.event_index}); next={detail.next_grammar}'
                    temp = self.generator.get_template('EncodeEventOptionalElementNone.jinja')
                    content += temp.render(option=option,
                                           event_comment=event_comment,
                                           indent=self.indent, level=level)

        content += '\n'

        return self.left_trim_lf(content)

    def __get_event_content_for_single_element(self, detail: ElementGrammarDetail, grammar: ElementGrammar, level):
        content = ''

        if detail.flag == GrammarFlag.END:
            content += self.__get_event_content_for_end_element(detail, grammar.bits_to_write, True, level)
        else:
            event_comment = f'// Event: {detail.flag} ({detail.particle.typename}); next={detail.next_grammar}'
            type_parameter = CONFIG_PARAMS['encode_function_prefix'] + detail.particle.prefixed_name
            temp = self.generator.get_template('EncodeEventSingleElement.jinja')
            content += temp.render(bits_to_write=grammar.bits_to_write,
                                   value_to_write=detail.event_index,
                                   event_comment=event_comment,
                                   type_content=self.__get_type_content(grammar, detail, 4),
                                   add_debug_code=self.get_status_for_add_debug_code(detail.particle.prefixed_name),
                                   type_parameter=type_parameter,
                                   indent=self.indent, level=level)

        return self.trim_lf(content)

    def __get_event_content(self, grammar: ElementGrammar, level):
        content = ''
        first = grammar.details[0]

        if first.flag != GrammarFlag.ERROR:
            if grammar.details_count == 1:
                if first.is_mandatory_array:
                    content += self.__get_event_content_for_array_element(first, grammar, 0, level)
                else:
                    content += self.__get_event_content_for_single_element(first, grammar, level)
            else:
                option = 0
                end_index = -1
                detail: ElementGrammarDetail
                for index, detail in enumerate(grammar.details):
                    if detail.flag == GrammarFlag.END:
                        # ensure that the END detail gets encoded last, even if not final detail due to ANY
                        end_index = index
                        continue

                    if index == grammar.details_count - 1 and option != 0 and not detail.is_any:
                        # the final detail gets just "else"
                        option = -1

                    # FIXME / HACK: 'PGPKeyPacket' is regarded as optional by the grammar generation, due to
                    # incorrect handling of choices of sequences - force it here
                    # if detail.particle_name == 'PGPKeyPacket':
                    #     option = -1
                    #     log_write_error("FIXME / HACK: forcing 'PGPKeyPacket' particle to be non-optional - fix the grammar!")

                    # log_write_error(f"__get_event_content(): option = {option} for grammar '{grammar.element_typename}', index {detail.event_index}, detail '{detail.particle_name}'")

                    if detail.is_mandatory_array:
                        if option >= 0:
                            content += self.__get_event_content_for_array_element(first, grammar, option, level)
                        else:
                            content += self.__get_event_content_for_array_element(detail, grammar, option, level)
                    elif detail.is_optional_array:
                        content += self.__get_event_content_for_optional_array_element(detail, grammar, option, level)
                    else:
                        content += self.__get_event_content_for_optional_element(detail, grammar, option, level)
                    if not (detail.is_any and detail.any_is_dummy):
                        # increment only if code was created
                        option += 1

                if end_index >= 0:
                    # finally, place code for END detail at and of block
                    option = -1
                    content += self.__get_event_content_for_optional_element(grammar.details[end_index], grammar, option, level)

        return self.trim_lf(content)

    def __get_event_content_namespace_element(self, element: ElementData, grammar: ElementGrammar, level):
        content = ''

        if grammar.details[0].flag == GrammarFlag.START:
            names = []
            for particle in element.particles:
                names.append(particle.name)
            names.sort()

            bits_to_write = tools.get_bits_to_decode(len(names))
            next_grammar = grammar.details[0].next_grammar

            for index, name in enumerate(names):
                hits = [x for x in element.particles if x.name == name]
                event_comment = f'// Event: {hits[0].name}'
                parameter = f'{element.typename}->{name}'
                type_content = self.__get_content_encode_namespace_element(element.typename, hits[0],
                                                                           next_grammar, level + 2)

                temp = self.generator.get_template('EncodeEventOptionalElement.jinja')
                content += temp.render(parameter=parameter,
                                       option=index,
                                       bits_to_write=bits_to_write,
                                       value_to_write=index,
                                       event_comment=event_comment,
                                       type_content=type_content,
                                       add_debug_code=self.get_status_for_add_debug_code(element.prefixed_type),
                                       type_parameter=CONFIG_PARAMS['encode_function_prefix'] + element.prefixed_type,
                                       indent=self.indent, level=level)

            content += '\n'
            temp = self.generator.get_template('EncodeEventErrorUnknownId.jinja')
            content += temp.render(indent=self.indent, level=level)

        return self.left_trim_lf(content)

    def __get_grammar_content(self, grammars: List[ElementGrammar], level, element: ElementData = None):
        grammar_content = ''

        for grammar in grammars:
            if grammar.details[0].flag == GrammarFlag.ERROR:
                continue

            # first reorder details, move first END Element to end of list
            self.move_end_element_to_end_of_list(grammar)

            if element is None or grammar.details[0].flag == GrammarFlag.END:
                grammar_id_comment = grammar.grammar_comment
                event_content = self.__get_event_content(grammar, level + 1)
            else:
                bits_to_write = tools.get_bits_to_decode(len(element.particles))
                grammar_id_comment = f'// Grammar: ID={grammar.grammar_id}; read/write bits={bits_to_write}; '
                grammar_id_comment += f'{grammar.details[0].flag} ({grammar.details[0].particle.name})'
                event_content = self.__get_event_content_namespace_element(element, grammar, level + 1)

            temp = self.generator.get_template('BaseEncodeCaseGrammarId.jinja')
            grammar_content += temp.render(grammar_id=grammar.grammar_id,
                                           grammar_id_comment=grammar_id_comment,
                                           event_content=event_content,
                                           indent=self.indent, level=level)

            grammar_content += '\n'

        return self.trim_lf(grammar_content)

    def __get_function_content(self, element: ElementData, grammars: List[ElementGrammar]):
        typename = element.typename
        content = ''

        start_grammar_id = self.get_start_grammar_id(grammars)
        if start_grammar_id >= 0:
            if element.is_in_namespace_elements:
                grammar_content = self.__get_grammar_content(grammars, 2, element)
            else:
                grammar_content = self.__get_grammar_content(grammars, 2)

            # if there is more than one array inside element, we have to handle the different indexes.
            # So the indexes are prefixed with the particle name.
            names = []
            has_array = self.has_element_array_particle(element)
            if has_array:
                names = self.get_element_array_particle_names(element)

            temp = self.generator.get_template('BaseEncodeFunction.jinja')
            content += temp.render(element_comment=element.element_comment,
                                   particle_comment=element.particle_comment,
                                   function_name=CONFIG_PARAMS['encode_function_prefix'] + element.prefixed_type,
                                   struct_type=element.prefixed_type, parameter_name=typename,
                                   start_grammar_id=start_grammar_id,
                                   grammar_content=grammar_content,
                                   has_array=has_array, names=names,
                                   add_debug_code=self.get_status_for_add_debug_code(element.prefixed_type),
                                   indent=self.indent, level=1)
            content += '\n\n'
        else:
            temp = self.generator.get_template('EncodeEmptyFunction.jinja')
            content += temp.render(element_comment=element.element_comment,
                                   function_name=CONFIG_PARAMS['encode_function_prefix'] + element.prefixed_type,
                                   struct_type=element.prefixed_type, parameter_name=typename,
                                   add_debug_code=self.get_status_for_add_debug_code(element.prefixed_type),
                                   indent=self.indent, level=1)
            content += '\n\n'

        return content

    def __get_root_content(self):
        root_content = ''
        root_comment = '// main function for encoding'
        fn_name = CONFIG_PARAMS['encode_function_prefix'] + self.parameters['prefix'] + \
            CONFIG_PARAMS['root_struct_name']
        struct_type = self.parameters['prefix'] + CONFIG_PARAMS['root_struct_name']
        parameter_name = CONFIG_PARAMS['root_parameter_name']

        if len(self.analyzer_data.root_elements) == 0:
            log_write_error(f'No root elements in analyzer data. Main function {fn_name} is not generated.')
        elif len(self.analyzer_data.root_elements) > 1:
            encode_fn = []
            for elem in self.analyzer_data.root_elements:
                if self.__is_iso20:
                    # TODO: The following if filters the simple types DigestValue, MgmtData and KeyName.
                    #       Simple types have to be encoded directly and not with an encoding function.
                    #       So it has to be checked if these types can be ignored here or
                    #       the encoding has to be implemented.
                    prefix_name_short = f'{elem.prefix}{elem.name_short}'
                    if elem.type_definition == 'complex':
                        encode_fn.append([CONFIG_PARAMS['encode_function_prefix'] + elem.prefixed_type,
                                          parameter_name + '->' + elem.name_short])
                    else:
                        encode_fn.append([f'{CONFIG_PARAMS["encode_function_prefix"]}{prefix_name_short}', ''])
                else:
                    if elem.typename in self.analyzer_data.schema_builtin_types:
                        encode_fn.append([f'{CONFIG_PARAMS["encode_function_prefix"]}{elem.prefix}{elem.name_short}',
                                          f'{parameter_name}->{elem.prefix}{elem.name_short}'])
                    else:
                        encode_fn.append([CONFIG_PARAMS['encode_function_prefix'] + elem.prefixed_type,
                                          parameter_name + '->' + elem.typename])

            encode_fn.sort()

            bits = tools.get_bit_count_for_value(len(self.analyzer_data.root_elements))

            temp = self.generator.get_template('EncodeRootFunction.jinja')
            root_content += temp.render(function_comment=root_comment,
                                        function_name=fn_name,
                                        struct_type=struct_type, parameter_name=parameter_name,
                                        bits_to_encode=bits,
                                        encode_functions=encode_fn,
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
                        function = CONFIG_PARAMS['encode_function_prefix'] + self.parameters['prefix'] + name
                        parameter = parameter_name + '->' + name
                        if parameter.casefold().endswith('type'):
                            parameter = parameter[:len(parameter) - 4]
                        break

                    parameter_index += 1

                bits = tools.get_bit_count_for_value(len(self.analyzer_data.namespace_elements[name_short]))

                temp = self.generator.get_template('EncodeRootV2GMessage.jinja')
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
            temp = self.generator.get_template("DataTypesEncoder.c.jinja")
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
                log_write_error('Module encoder: Generator loop aborted! Loop counter exceeded.')
                break

            element: ElementData = self.elements_to_generate[curr_idx]
            elem_typename = element.typename
            skip_element = self.test_on_skip(element)

            if skip_element:
                curr_idx += 1
                if curr_idx > len(self.elements_to_generate):
                    log_write_error('Module encoder: Generator loop aborted! Index larger than existing elements.')
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
