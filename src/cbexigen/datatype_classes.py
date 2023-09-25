# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 - 2023 chargebyte GmbH
# Copyright (C) 2023 Contributors to EVerest

from xmlschema import XMLSchema11
from cbexigen import tools, tools_generator, tools_logging
from cbexigen.elementData import Particle, ElementData
from cbexigen.tools_config import CONFIG_PARAMS
from cbexigen.tools_logging import log_write_error, log_init_logger, log_write_logger, \
    log_deinit_logger, log_exists_logger
from cbexigen.typeDefinitions import AnalyzerData


# ---------------------------------------------------------------------------
# Datatype generating header file
# ---------------------------------------------------------------------------


class DatatypeHeader:
    def __init__(self, current_scheme: XMLSchema11, parameters, analyzer_data: AnalyzerData, enable_logging=True):
        self.generator = tools_generator.get_generator()
        self.config = CONFIG_PARAMS
        self.parameters = parameters
        self.h_params = parameters.get('h', None)
        self.analyzer_data = analyzer_data
        self.logging_enabled = enable_logging
        self.logger_name = ''
        self.scheme = current_scheme

        self.__is_iso20 = True if str(self.parameters['prefix']).startswith('iso20_') else False

        if self.logging_enabled:
            self.logger_name = str(self.h_params['filename'])
            if self.logger_name.casefold().endswith('.h') or self.logger_name.casefold().endswith('.c'):
                self.logger_name = self.logger_name[:len(self.logger_name) - 2]

            if not log_exists_logger(self.logger_name):
                log_init_logger(self.logger_name, f'{self.logger_name}.txt')

        self.__generated_t = []
        self.__generate = []
        self.__global_define_list = {}

    # ---------------------------------------------------------------------------
    # logging functions
    # ---------------------------------------------------------------------------
    def disable_logging(self):
        if self.logging_enabled and self.logger_name != '':
            log_deinit_logger(self.logger_name)
            self.logging_enabled = False

    def log(self, message):
        if self.logging_enabled:
            log_write_logger(self.logger_name, message)

    # ---------------------------------------------------------------------------
    # general helper functions
    # ---------------------------------------------------------------------------
    def __clear_lists(self):
        self.__generated_t.clear()
        self.__generate.clear()
        self.__global_define_list.clear()

    @staticmethod
    def __get_particle_comment(particle: Particle):
        comment = '// '
        if particle.is_attribute:
            comment += 'Attribute: '

        comment += particle.name + ', ' + particle.type_short

        if particle.base_type != '':
            comment += ' (base: ' + particle.base_type + ')'

        return comment

    def __is_array_define_in_global_list(self, particle: Particle):
        result = False

        if particle.prefixed_define_for_array in self.__global_define_list.keys():
            value = self.__global_define_list[particle.prefixed_define_for_array]
            if value == particle.max_occurs:
                result = True
            else:
                err = f'Define exists for {particle.prefixed_define_for_array} but has different value! ' \
                      f'current={particle.max_occurs}, global={value}'
                log_write_error(err)

        return result

    def __is_base_type_define_in_global_list(self, particle: Particle):
        result = False

        if particle.prefixed_define_for_base_type in self.__global_define_list.keys():
            err = False
            value = str(self.__global_define_list[particle.prefixed_define_for_base_type])
            if particle.max_length > 0:
                str_length = str(particle.max_length)
                if particle.base_type == 'string':
                    str_length += ' + ASCII_EXTRA_CHAR'

                if value == str_length:
                    result = True
                else:
                    err = True
            else:
                if value == str(particle.define_max_value):
                    result = True
                else:
                    err = True

            if err:
                text = f'Define exists for {particle.prefixed_define_for_base_type} but has different value! ' \
                       f'current={particle.max_length}, global={value}'
                log_write_error(text)

        return result

    # ---------------------------------------------------------------------------
    # generator helper functions
    # ---------------------------------------------------------------------------

    def __generate_defines(self):
        temp = self.generator.get_template('BaseDefines.jinja')
        return temp.render(defines=self.__global_define_list)

    def __generate_functions_enum(self):
        comment = '// enum for function numbers'
        enum_type = self.parameters['prefix'] + 'generatedFunctionNumbersType'
        items = []
        for value in self.scheme.elements.target_dict.values():
            if value.default_namespace:
                items.append(self.parameters['prefix'] + value.local_name)
        items.sort()

        temp = self.generator.get_template('BaseEnum.jinja')
        return temp.render(list=items, element_comment=comment, enum_type=enum_type)

    def __generate_enum_array_struct(self, particle):
        # generate struct for array with length variable
        comment = self.__get_particle_comment(particle)
        particle_type = particle.prefixed_type
        temp = self.generator.get_template("SubStructSimpleArray.jinja")

        return temp.render(struct_name=particle.name,
                           struct_type=particle_type,
                           type_def=particle.prefixed_define_for_array,
                           variable_comment=comment)

    def __generate_array_struct(self, particle: Particle):
        # generate struct for array with length variable
        comment = self.__get_particle_comment(particle)
        particle_type = particle.prefixed_type
        temp = self.generator.get_template("SubStructArray.jinja")

        if particle.integer_base_type:
            if particle.integer_base_type in tools.TYPE_TRANSLATION_C:
                particle_type = tools.TYPE_TRANSLATION_C[particle.integer_base_type]
                temp = self.generator.get_template("SubStructSimpleArray.jinja")
            else:
                log_write_error(f"No integer type found for integer base type {particle.integer_base_type}")

        return temp.render(struct_name=particle.name,
                           struct_type=particle_type,
                           type_def=particle.prefixed_define_for_array,
                           variable_comment=comment)

    def __generate_char_array_struct(self, particle: Particle, indent_level=1):
        # generate struct for array with length variable
        indent = ' ' * self.config['c_code_indent_chars']
        comment = self.__get_particle_comment(particle)
        type_array = 0
        struct_def = ''

        temp = self.generator.get_template("SubStructChar.jinja")
        return temp.render(indent=indent, level=indent_level,
                           struct_name=particle.name,
                           struct_type="char",
                           type_def=particle.prefixed_define_for_base_type,
                           type_array=type_array,
                           struct_def=struct_def,
                           variable_comment=comment)

    def __generate_char_array_struct_from_string(self, particle: Particle, with_used=False, indent_level=1):
        # generate struct for array with length variable
        indent = ' ' * self.config['c_code_indent_chars']
        comment = self.__get_particle_comment(particle)
        type_array = 1 if particle.max_occurs > 1 else 0
        struct_def = particle.prefixed_define_for_array if particle.max_occurs > 1 else ''

        temp = self.generator.get_template("SubStructCharWithUsed.jinja" if with_used else "SubStructChar.jinja")
        return temp.render(indent=indent, level=indent_level,
                           struct_name=particle.name,
                           struct_type="char",
                           type_def=particle.prefixed_define_for_base_type,
                           type_array=type_array,
                           struct_def=struct_def,
                           variable_comment=comment)

    def __generate_byte_array_struct_from_binary(self, particle: Particle, with_used=False, indent_level=1):
        # generate struct for array with length variable
        indent = ' ' * self.config['c_code_indent_chars']
        comment = self.__get_particle_comment(particle)
        type_array = 1 if particle.max_occurs > 1 else 0
        struct_def = particle.prefixed_define_for_array if particle.max_occurs > 1 else ''

        temp = self.generator.get_template("SubStructByteWithIsUsed.jinja" if with_used else "SubStructByte.jinja")
        return temp.render(indent=indent, level=indent_level,
                           struct_name=particle.name,
                           struct_type="uint8_t",
                           type_def=particle.prefixed_define_for_base_type,
                           type_array=type_array,
                           struct_def=struct_def,
                           variable_comment=comment)

    def __generate_variable_with_used(self, particle: Particle, is_in_types=False):
        # generate variable with type or struct type and isUsed flag
        comment = self.__get_particle_comment(particle)
        type_str = ''

        if particle.integer_base_type is not None:
            if particle.integer_base_type in tools.TYPE_TRANSLATION_C:
                type_str = tools.TYPE_TRANSLATION_C[particle.integer_base_type]
            else:
                log_write_error(f"No integer type found for integer base type {particle.integer_base_type}")
        else:
            type_str = particle.prefixed_type

        temp = self.generator.get_template('SubStructVariableWithUsed.jinja') \
            if particle.is_complex or is_in_types else self.generator.get_template('SubVariableWithUsed.jinja')

        return temp.render(variable_name=particle.name,
                           variable_type=type_str,
                           variable_comment=comment)

    def __generate_variables_with_union_and_used(self, elements):
        temp = self.generator.get_template('SubStructVariablesWithUnionAndUsed.jinja')
        return temp.render(elements=elements)

    def __generate_variable(self, particle: Particle, is_in_types=False):
        # generate variable with type or struct type
        comment = self.__get_particle_comment(particle)
        type_str = ''

        if particle.integer_base_type is not None:
            if particle.integer_base_type in tools.TYPE_TRANSLATION_C:
                type_str = tools.TYPE_TRANSLATION_C[particle.integer_base_type]
            else:
                log_write_error(f"No integer type found for integer base type {particle.integer_base_type}")
        else:
            type_str = particle.prefixed_type

        temp = self.generator.get_template('SubStructVariable.jinja') \
            if particle.is_complex or is_in_types else self.generator.get_template('SubVariable.jinja')

        return temp.render(variable_name=particle.name,
                           variable_type=type_str,
                           variable_comment=comment)

    def __generate_string(self, particle: Particle, with_used=False, indent_level=1):
        return self.__generate_char_array_struct_from_string(particle, with_used, indent_level)

    def __generate_base64binary(self, particle: Particle, with_used=False, indent_level=1):
        return self.__generate_byte_array_struct_from_binary(particle, with_used, indent_level)

    def __generate_sequence_content(self, name, comment, content, indent_level=1):
        indent = ' ' * self.config['c_code_indent_chars']
        temp = self.generator.get_template('SubStructSequence.jinja')
        return temp.render(indent=indent, level=indent_level,
                           sequence_comment=comment, sequence_name=name, sequence_content=content)

    def __get_particle_content(self, particle: Particle, elements, indent_level=1):
        content = ''
        last = None

        # particle type is in list, so a separate type is generated
        if particle.type in self.analyzer_data.known_elements:
            if particle.max_occurs > 1:
                # generate struct for array with length variable
                if particle.is_enum:
                    content += self.__generate_enum_array_struct(particle)
                else:
                    if particle.simple_type_is_string:
                        content += self.__generate_string(particle)
                    else:
                        content += self.__generate_array_struct(particle)
            elif particle.min_occurs == 0:
                # generate variable with isUsed flag
                if particle.is_substitute:
                    elements[particle.prefixed_type] = particle.name
                    last = particle
                else:
                    if particle.type not in self.analyzer_data.known_enums:
                        content += self.__generate_variable_with_used(particle, True)
                    else:
                        content += self.__generate_variable_with_used(particle)
            else:
                # just generate variable with type
                if particle.type in self.analyzer_data.known_enums:
                    content += self.__generate_variable(particle) + '\n'
                else:
                    content += self.__generate_variable(particle, True) + '\n'
        # particle type is not in list, but min_occurs == 0, generate variable with isUsed
        elif particle.min_occurs == 0:
            # generate variable with isUsed flag
            if particle.is_substitute:
                elements[particle.type_short] = particle.name
                last = particle
            else:
                particle_type = tools_generator.get_particle_type(particle)
                if particle.simple_type_is_string:
                    content += self.__generate_string(particle, True, indent_level)
                elif particle_type == 'binary':
                    content += self.__generate_base64binary(particle, True, indent_level) + '\n'
                else:
                    content += self.__generate_variable_with_used(particle)
        else:
            # particle type is not in list, so we just generate a variable with translated base type
            # but if type is anyURI then generate char struct with length variable
            particle_type = tools_generator.get_particle_type(particle)
            if particle_type == 'uri':
                content += self.__generate_char_array_struct(particle)
            elif particle.simple_type_is_string:
                content += self.__generate_string(particle)
            elif particle_type == 'binary':
                content += self.__generate_base64binary(particle, False, indent_level) + '\n'
            else:
                # max_occurs > 1, generate array type
                if particle.max_occurs > 1:
                    content += self.__generate_array_struct(particle)
                else:
                    content += self.__generate_variable(particle) + '\n'

        return last, content

    def __get_struct_content(self, element: ElementData):
        struct_content = ""
        elements = {}
        last_particle = None

        if not element.has_sequence:
            for particle in element.particles:
                last, content = self.__get_particle_content(particle, elements)
                struct_content += content
                if last:
                    last_particle = last

            if len(elements) == 1:
                if last_particle:
                    struct_content += self.__generate_variable_with_used(last_particle)
            elif len(elements) > 1:
                struct_content += self.__generate_variables_with_union_and_used(elements)
        else:
            union_content = ''
            for index, sequence in enumerate(element.sequences):
                seq_content = ''
                for item in sequence:
                    particle = tools_generator.get_particle_from_element_by_name(item[0], item[1], element)
                    if particle:
                        _, content = self.__get_particle_content(particle, elements, 3)
                        seq_content += content

                comment = "// sequence of choice " + str(index + 1)
                name = self.config['choice_sequence_prefix'] + str(index + 1)
                union_content += self.__generate_sequence_content(name, comment, seq_content, 2) + '\n\n'

            temp = self.generator.get_template('SubUnion.jinja')
            struct_content += temp.render(union_content=union_content)

        return struct_content

    def __get_root_content(self):
        elements = []
        comment = '// root elements of EXI doc'
        name = self.parameters['prefix'] + self.config['root_struct_name']
        self.analyzer_data.known_prototypes[name] = self.config['root_parameter_name']

        element: ElementData
        for element in self.analyzer_data.root_elements:
            if self.__is_iso20:
                # TODO: The following if filters the simple types DigestValue, MgmtData and KeyName.
                #       So it has to be checked if these types can be ignored here.
                if element.type_definition == 'complex':
                    elements.append((element.prefixed_type, element.name_short))
                    self.analyzer_data.known_prototypes[element.prefixed_type] = element.name_short
            else:
                if element.base_type == '':
                    elements.append((element.prefixed_type, element.name_short))
                    self.analyzer_data.known_prototypes[element.prefixed_name] = element.name_short
                else:
                    elements.append((element.prefixed_type, element.type_short))
                    self.analyzer_data.known_prototypes[element.prefixed_type] = element.type_short

        # generate struct for array with length variable
        temp = self.generator.get_template('BaseStructWithUnionAndUsed.jinja')
        if len(self.analyzer_data.root_elements) == 1:
            temp = self.generator.get_template('BaseStruct.jinja')

        return temp.render(struct_name=name,
                           element_comment=comment,
                           elements=elements)

    def __get_prototype_content(self):
        comment = '// init for structs'

        # this works here because the first prototypes are added in get_root_content()
        for element in self.analyzer_data.generate_elements:
            if element.type_definition != 'enum':
                if element.prefixed_name not in self.analyzer_data.known_prototypes:
                    if element.prefixed_type not in self.analyzer_data.known_prototypes:
                        self.analyzer_data.known_prototypes[element.prefixed_type] = element.type_short

        # generate prototypes for elements
        temp = self.generator.get_template('BasePrototype.jinja')
        return temp.render(comment=comment,
                           elements=self.analyzer_data.known_prototypes)

    def __append_to_global_define_list(self, element: ElementData):
        # TODO: check if particle is in OCCURRENCE_LIMITS_CORRECTED, should then result in an array definition

        for particle in element.particles:
            if particle.is_array:
                if not self.__is_array_define_in_global_list(particle):
                    self.__global_define_list[particle.prefixed_define_for_array] = particle.max_occurs
            if particle.define_for_base_type != '':
                if not self.__is_base_type_define_in_global_list(particle):
                    if particle.max_length > 0:
                        if particle.base_type == 'string':
                            self.__global_define_list[particle.prefixed_define_for_base_type] = \
                                f'{particle.max_length} + ASCII_EXTRA_CHAR'
                        else:
                            self.__global_define_list[particle.prefixed_define_for_base_type] = particle.max_length
                    else:
                        self.__global_define_list[particle.prefixed_define_for_base_type] = particle.define_max_value

    def generate_file(self):
        if self.h_params is None:
            log_write_error(f'Caution! No h-parameters passed. '
                            f'{self.__class__.__name__}.{self.generate_file.__name__}')
            return

        content = ""
        element_list = []

        # clear lists and copy the list of elements to generate
        self.__clear_lists()
        for element in self.analyzer_data.generate_elements:
            self.__generate.append(element)

        # the enums are generated first
        for element in self.analyzer_data.generate_elements:
            if element.type_definition == 'enum':
                element_list.clear()
                if element.has_enum_list:
                    comment = element.element_comment
                    for value in element.enum_list:
                        text = value
                        for char in self.config['c_replace_chars']:
                            text = text.replace(char, '_')

                        element_list.append(f'{element.prefixed_type}_{text}')
                else:
                    element_type = self.scheme.types.get(element.type_short)
                    if element_type is None:
                        element_type = self.scheme.types.target_dict.get(element.type)
                        if element_type is None:
                            continue

                    comment = element.element_comment
                    for value in element_type.enumeration:
                        text = value
                        for char in self.config['c_replace_chars']:
                            text = text.replace(char, '_')

                        element_list.append(f'{element.prefixed_type}_{text}')

                temp = self.generator.get_template('BaseEnum.jinja')
                content += temp.render(list=element_list, enum_type=element.prefixed_type, element_comment=comment)
                content += '\n\n'
                # update generated elements list
                self.__generated_t.append(element.type_short)
                self.__generate.remove(element)

        curr_idx = 0
        while_count = 0
        while len(self.__generate) > 0:
            # loop should not run forever
            while_count += 1
            if while_count > 10000:
                log_write_error('Module datatypes: Generator loop aborted! Loop counter exceeded.')
                break

            element = self.__generate[curr_idx]
            # building struct/element name
            elem_name = element.typename

            skip_element = False
            for particle in element.particles:
                if particle.is_complex:
                    if particle.typename_simple not in self.__generated_t:
                        # skip here! generate type first before we can use it
                        skip_element = True
                        break

            if skip_element:
                curr_idx += 1
                if curr_idx > len(self.__generate):
                    log_write_error('Module datatypes: Generator loop aborted! Index larger than existing elements.')
                    break
            else:
                self.__append_to_global_define_list(element)
                struct_content = self.__get_struct_content(element)
                # avoid empty structs
                if struct_content == '':
                    struct_content += '    int _unused;'

                temp = self.generator.get_template('BaseStructWithFullComment.jinja')
                content += temp.render(struct_name=element.prefixed_type,
                                       content=struct_content,
                                       element_comment=element.element_comment,
                                       particle_comment=element.particle_comment)
                content += '\n'

                # add element to list of generated ane remove from list to generate and reset element index
                self.__generated_t.append(elem_name)
                self.__generate.remove(element)
                curr_idx = 0

        content += '\n\n'
        content += self.__get_root_content()

        include = tools_generator.get_includes_content(self.h_params)
        defines = self.__generate_defines()
        prototype = self.__get_prototype_content()
        enum_code = self.__generate_functions_enum()

        # file
        try:
            temp = self.generator.get_template('BaseDatatypes.h.jinja')
            code = temp.render(filename=self.h_params['filename'],
                               filekey=self.h_params['identifier'],
                               include=include,
                               defines=defines,
                               enum_code=enum_code,
                               code=content,
                               prototype=prototype)
            tools.save_code_to_file(self.h_params['filename'], code, self.parameters['folder'])
        except KeyError as err:
            tools_logging.log_write_error(f'Exception in {self.__class__.__name__}.{self.generate_file.__name__} '
                                          f'(KeyError): {err}')


# ---------------------------------------------------------------------------
# Datatype generating code file
# ---------------------------------------------------------------------------


class DatatypeCode:
    def __init__(self, current_scheme, parameters, analyzer_data: AnalyzerData, enable_logging=True):
        self.generator = tools_generator.get_generator()
        self.config = CONFIG_PARAMS
        self.parameters = parameters
        self.c_params = parameters.get('c', None)
        self.analyzer_data = analyzer_data
        self.logging_enabled = enable_logging
        self.logger_name = ''

        self.__is_iso20 = True if str(self.parameters['prefix']).startswith('iso20_') else False

        if self.logging_enabled:
            self.logger_name = str(self.c_params['filename'])
            if self.logger_name.casefold().endswith('.h') or self.logger_name.casefold().endswith('.c'):
                self.logger_name = self.logger_name[:len(self.logger_name) - 2]

            if not log_exists_logger(self.logger_name):
                log_init_logger(self.logger_name, f'{self.logger_name}.txt')

    # ---------------------------------------------------------------------------
    # logging functions
    # ---------------------------------------------------------------------------
    def disable_logging(self):
        if self.logging_enabled and self.logger_name != '':
            log_deinit_logger(self.logger_name)
            self.logging_enabled = False

    def log(self, message):
        if self.logging_enabled:
            log_write_logger(self.logger_name, message)

    # ---------------------------------------------------------------------------
    # generator helper functions
    # ---------------------------------------------------------------------------
    @staticmethod
    def __get_type_member_array(particle: Particle):
        result = particle.name + '.arrayLen'

        if particle.max_occurs == 1:
            particle_type = tools_generator.get_particle_type(particle)
            if particle_type == 'string':
                result = particle.name + '.charactersLen'
            elif particle_type == 'binary':
                result = particle.name + '.bytesLen'

        return result

    @staticmethod
    def __get_sequence_from_optional_particle(name, element: ElementData):
        result = -1

        for index, sequence in enumerate(element.sequences):
            for item in sequence:
                if item[0] == name:
                    particle = tools_generator.get_particle_from_element_by_name(item[0], item[1], element)
                    if particle:
                        if particle.min_occurs == 0:
                            result = index + 1
                            break

        return result

    # ---------------------------------------------------------------------------
    # content delivery functions
    # ---------------------------------------------------------------------------
    def __get_root_content(self):
        elements = {}
        comment = '// root elements of EXI doc'
        function_name = self.config['init_function_prefix'] + self.parameters['prefix'] + \
            self.config['root_struct_name']
        struct_type = self.parameters['prefix'] + self.config['root_struct_name']
        parameter_name = self.config['root_parameter_name']

        if len(self.analyzer_data.root_elements) > 1:
            for element in self.analyzer_data.root_elements:
                if self.__is_iso20:
                    # TODO: The following if filters the simple types DigestValue, MgmtData and KeyName.
                    #       So it has to be checked if these types can be ignored here.
                    if element.type_definition == 'complex':
                        elements[element.name_short] = element.name_short
                else:
                    if element.base_type == '':
                        elements[element.name_short] = element.name_short
                    else:
                        elements[element.typename] = element.typename

        # generate init function for struct with isUsed = 0u
        temp = self.generator.get_template("BaseInitWithUsed.jinja")

        return temp.render(function_name=function_name,
                           struct_type=struct_type,
                           parameter_name=parameter_name,
                           element_comment=comment,
                           elements=elements)

    def __get_function_content(self):
        ele = []
        arr = []
        result = ''
        comment = ''

        for element in self.analyzer_data.generate_elements:
            if not element.type_definition == 'enum':
                ele.clear()
                arr.clear()

                function_name = self.config['init_function_prefix'] + element.prefixed_type
                struct_type = element.prefixed_type
                parameter_name = element.type_short

                if element.type_short == 'AnonType':
                    function_name = self.config['init_function_prefix'] + element.prefixed_name
                    struct_type = element.prefixed_name
                    parameter_name = element.name_short

                for particle in element.particles:
                    # TODO: check if particle is in OCCURRENCE_LIMITS_CORRECTED,
                    #       should then result in an array definition
                    # TODO: if we have an array type with min_occurs == 0, then a isUsed should be created, too
                    if particle.max_occurs > 1:
                        arr.append(self.__get_type_member_array(particle))
                    elif particle.min_occurs == 0:
                        if particle.type not in self.analyzer_data.known_enums:
                            particle_type = tools_generator.get_particle_type(particle)
                            if particle_type == 'string':
                                arr.append(particle.name + '.charactersLen')
                            elif particle_type == 'binary':
                                if element.has_sequence:
                                    seq = self.__get_sequence_from_optional_particle(particle.name, element)
                                    if seq > 0:
                                        arr.append(self.config['choice_sequence_prefix'] + str(seq) + '.' +
                                                   particle.name + '.bytesLen')
                                else:
                                    arr.append(particle.name + '.bytesLen')
                            else:
                                ele.append(particle.name)
                        else:
                            ele.append(particle.name)

                # generate init function with arrayLen = 0u and isUsed = 0u
                temp = self.generator.get_template("BaseInitWithArrayLenAndUsed.jinja")
                result += temp.render(function_name=function_name,
                                      struct_type=struct_type,
                                      parameter_name=parameter_name,
                                      element_comment=comment,
                                      elements=ele,
                                      arrays=arr)
                result += '\n'

        return result

    # ---------------------------------------------------------------------------
    # general generator functions
    # ---------------------------------------------------------------------------
    def generate_file(self):
        if self.c_params is None:
            log_write_error(f'Caution! No c-parameters passed. '
                            f'{self.__class__.__name__}.{self.generate_file.__name__}')
            return

        includes = tools_generator.get_includes_content(self.c_params)

        content = ''
        content += self.__get_root_content()
        content += self.__get_function_content()

        # file
        try:
            temp = self.generator.get_template("BaseDatatypes.c.jinja")
            code = temp.render(filename=self.c_params["filename"], filekey=self.c_params["identifier"],
                               includes_code=includes, code=content)
            tools.save_code_to_file(self.c_params["filename"], code, self.parameters['folder'])
        except KeyError as err:
            tools_logging.log_write_error(f'Exception in {self.__class__.__name__}.{self.generate_file.__name__} '
                                          f'(KeyError): {err}')
