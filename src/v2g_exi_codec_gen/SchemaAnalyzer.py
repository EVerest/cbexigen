# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 chargebyte GmbH
# Copyright (c) 2022 - 2023 Contributors to EVerest

from xmlschema import XMLSchema11, XsdElement, XsdType, XsdAttribute
from xmlschema.validators import XsdSimpleType, XsdComplexType, XsdGroup

from v2g_exi_codec_gen import tools
from v2g_exi_codec_gen.typeDefinitions import AnalyzerData, OCCURRENCE_LIMITS_CORRECTED
from v2g_exi_codec_gen.elementData import Particle, Choice, ElementData
from v2g_exi_codec_gen.tools_logging import log_write, log_write_dict, log_write_element, msg_write, \
    log_write_element_pos_data
from v2g_exi_codec_gen.tools_config import CONFIG_PARAMS, get_config_module


class SchemaAnalyzer(object):

    def __init__(self, schema, schema_base, analyzer_data: AnalyzerData, schema_prefix):
        self.__schema = schema
        self.__schema_base = schema_base
        self.__schema_file = None
        self.__current_schema: XMLSchema11

        self.__root_elements = analyzer_data.root_elements
        self.__generate_elements = analyzer_data.generate_elements
        self.__generate_elements_types = analyzer_data.generate_elements_types

        self.__known_elements = analyzer_data.known_elements
        self.__known_particles = analyzer_data.known_particles
        self.__known_enums = analyzer_data.known_enums
        self.__known_prototypes = analyzer_data.known_prototypes

        self.__max_occurs_changed = analyzer_data.max_occurs_changed
        self.__namespace_elements = analyzer_data.namespace_elements
        self.__schema_builtin_types = analyzer_data.schema_builtin_types

        self.config = CONFIG_PARAMS
        self.__schema_prefix = schema_prefix

    def open(self):
        if self.__schema is None or self.__schema_base is None:
            return

        self.__schema_file = open(self.__schema)
        self.__current_schema: XMLSchema11 = XMLSchema11(self.__schema_file,
                                                         base_url=self.__schema_base,
                                                         build=False)

        # if self.__schema_prefix == 'iso20_':
        #     add = f"{CONFIG_ARGS['schema_base_dir']}\ISO_15118-20\FDIS\V2G_CI_CommonMessages.xsd"
        #     self.__current_schema.add_schema(add)

        self.__current_schema.build()

    def close(self):
        if self.__schema_file is not None:
            self.__schema_file.close()

    def get_current_schema(self):
        return self.__current_schema

    def get_current_schema_file(self):
        return self.__schema_file

    # ---------------------------------------------------------------------------
    # general helper functions
    # ---------------------------------------------------------------------------
    @staticmethod
    def __get_name(element: XsdElement):
        result = ""

        if element.name:
            result = element.name

        return result

    @staticmethod
    def __get_name_short(element: XsdElement):
        result = ""

        if element.local_name:
            result = element.local_name

        return result

    @staticmethod
    def __get_type_name(element: [XsdElement, XsdAttribute]):
        result = ""

        if not hasattr(element, "type"):
            return result

        if element.type:
            if element.type.qualified_name:
                result = element.type.qualified_name
            else:
                result = "AnonymousType"

        return result

    @staticmethod
    def __get_type_name_short(element: [XsdElement, XsdAttribute]):
        result = ""

        if not hasattr(element, "type"):
            return result

        if element.type:
            if element.type.local_name:
                result = element.type.local_name
            else:
                result = "AnonType"

        return result

    @staticmethod
    def __get_base_type_name(element: [XsdElement, XsdAttribute]):
        result = ""

        if not hasattr(element, "type"):
            return result

        if element.type.base_type:
            if element.type.base_type.local_name:
                result = element.type.base_type.local_name
            else:
                result = "anyType"

        return result

    @staticmethod
    def __get_primitive_type_name(element: [XsdElement, XsdAttribute]):
        result = ""

        if not hasattr(element, "type"):
            return result

        if not hasattr(element.type, "primitive_type"):
            return result

        if element.type.primitive_type:
            if element.type.primitive_type.local_name:
                result = element.type.primitive_type.local_name
            else:
                result = "anyType"

        return result

    @staticmethod
    def __get_bit_info_for_integer(min_value, max_value):
        int_range = max_value - min_value + 1

        if int_range > (1 << 32):
            return 64
        elif int_range > (1 << 16):
            return 32
        elif int_range > (1 << 8):
            return 16
        else:
            return 8

    @staticmethod
    def __get_int_type_for_integer(type_short: str, base_type: str) -> str:
        if type_short in tools.TYPE_TRANSLATION:
            return tools.TYPE_TRANSLATION[type_short]
        elif base_type in tools.TYPE_TRANSLATION:
            return tools.TYPE_TRANSLATION[base_type]
        else:
            # 'base64Binary', 'string', ...
            # Expected return value is string, but if '' is returned,
            # an exception is raised in datatypes_classes __generate_variable.
            # So the return value is reset to None.
            return None

    @staticmethod
    def __is_abstract(element: [XsdElement, XsdSimpleType, XsdComplexType]):
        result = False

        if hasattr(element, 'abstract'):
            if element.abstract is not None:
                result = element.abstract

        return result

    @staticmethod
    def __is_abstract_type(element: [XsdElement, XsdSimpleType, XsdComplexType]):
        result = False

        if hasattr(element, 'type'):
            if hasattr(element.type, 'abstract'):
                if element.type.abstract is not None:
                    result = element.type.abstract

        return result

    # ---------------------------------------------------------------------------
    # analyzer helper functions
    # ---------------------------------------------------------------------------
    @staticmethod
    def __build_type_comment(child_type: XsdType, level):
        comment = ""

        print((level + 1) * "    " + child_type.local_name)

        return comment

    def __build_particle_comment(self, element: XsdElement, level):
        comment = level * "    " + "Particle: "

        comment += self.__get_child_list(element) + "; "

        if self.__is_abstract(element):
            comment += "abstract=" + str(element.abstract) + "; "

        return comment

    @staticmethod
    def __get_child_count(element: [XsdElement, XMLSchema11]):
        count = 0
        for _ in element.iterchildren():
            count += 1

        return count

    @staticmethod
    def __get_substitute_count(element: [XsdElement, XMLSchema11]):
        count = 0
        for _ in element.iter_substitutes():
            count += 1

        return count

    @staticmethod
    def __get_substitute_list(element: [XsdElement]):
        substitute_list = ""

        for substitute in element.iter_substitutes():
            if substitute.name is None:
                continue

            if len(substitute_list) > 0:
                substitute_list += ", "
            substitute_list += substitute.local_name

        return substitute_list

    @staticmethod
    def __has_complex_child(element: XsdElement):
        result = False

        for child in element.iterchildren():
            if child.name is None:
                continue

            if child.type.is_complex():
                result = True
                break

        return result

    # ---------------------------------------------------------------------------
    # data delivery functions
    # ---------------------------------------------------------------------------
    @staticmethod
    def __get_child_list(element: XsdElement):
        child_list = ""

        for child in element.iterchildren():
            if child.name is None:
                continue

            if len(child_list) > 0:
                child_list += ", "
            child_list += child.local_name

            if child.is_restriction(child):
                child_list += " " + str(child.occurs)

        return child_list

    def __add_to_known_elements(self, element: XsdElement):
        result = False

        if element.type.qualified_name not in self.__known_elements:
            self.__known_elements[element.type.qualified_name] = element.type.local_name
            result = True

        return result

    def __add_to_max_occurs(self, name, occurrence):
        result = False

        if name not in self.__max_occurs_changed:
            self.__max_occurs_changed[name] = occurrence
            result = True

        return result

    def __get_particle_from_attribute(self, attribute: XsdAttribute):
        particle = Particle(prefix=self.__schema_prefix)

        particle.name = attribute.local_name

        particle.type = self.__get_type_name(attribute)
        particle.type_short = self.__get_type_name_short(attribute)
        particle.base_type = self.__get_base_type_name(attribute)
        particle.top_level_type = self.__get_primitive_type_name(attribute)

        particle.is_attribute = True

        if attribute.use.casefold() == 'required':
            particle.min_occurs = 1
            particle.max_occurs = 1
        else:
            particle.min_occurs = 0
            particle.max_occurs = 1

        if attribute.type.is_restriction():
            if attribute.type.min_length is not None:
                particle.min_length = attribute.type.min_length

            if attribute.type.max_length is not None:
                particle.max_length = attribute.type.max_length

            if attribute.type.min_value is not None:
                particle.min_value = attribute.type.min_value

            if attribute.type.max_value is not None:
                particle.max_value = attribute.type.max_value

        if attribute.type.is_complex():
            particle.is_complex = True

        if hasattr(attribute.type, 'enumeration'):
            if attribute.type.enumeration is not None:
                particle.is_enum = True
                particle.enum_count = len(attribute.type.enumeration)

                element_data = self.__get_element_data_from_enum_attribute(attribute)
                self.__generate_elements.append(element_data)
                self.__known_elements[element_data.type] = element_data.type_short

        return particle

    def __get_particle_integer_properties(self, particle: Particle, element: XsdElement):
        class_name = str(element.type.__class__.__name__).casefold()
        if class_name.endswith('atomicbuiltin') or class_name.endswith('atomicrestriction'):
            if element.type.max_value is not None and element.type.min_value is not None:
                particle.integer_min = element.type.min_value
                particle.integer_max = element.type.max_value
                particle.integer_bit_size = self.__get_bit_info_for_integer(element.type.min_value,
                                                                            element.type.max_value)
                if element.type.min_value >= 0:  # EXI specific: a value restricted by min >= 0 becomes unsigned
                    particle.integer_is_unsigned = True
            particle.integer_base_type = self.__get_int_type_for_integer(particle.type_short, particle.base_type)

    def __get_particle(self, element: XsdElement):
        particle = Particle(prefix=self.__schema_prefix)

        if self.__is_abstract(element):
            particle.abstract = True

        if self.__is_abstract_type(element):
            particle.abstract_type = True

        particle.name = element.local_name

        particle.type = self.__get_type_name(element)
        particle.type_short = self.__get_type_name_short(element)
        particle.base_type = self.__get_base_type_name(element)
        particle.top_level_type = self.__get_primitive_type_name(element)

        if element.is_restriction(element):
            particle.min_occurs = element.effective_min_occurs
            if element.max_occurs is not None:
                particle.max_occurs = element.effective_max_occurs
            else:
                if element.local_name in OCCURRENCE_LIMITS_CORRECTED:
                    particle.max_occurs = OCCURRENCE_LIMITS_CORRECTED[element.local_name]
                    log_write(particle.name + " max_occurs changed from unbounded to " + str(particle.max_occurs))
                else:
                    particle.max_occurs = 1
                    log_write(particle.name + " max_occurs set to " + str(particle.max_occurs))

                particle.max_occurs_changed = True
                self.__add_to_max_occurs(particle.name, particle.max_occurs)

        if element.type.is_restriction():
            if element.type.min_length:
                particle.min_length = element.type.min_length

            if element.type.max_length:
                particle.max_length = element.type.max_length

            if element.type.min_value:
                particle.min_value = element.type.min_value

            if element.type.max_value:
                particle.max_value = element.type.max_value

        if element.type.is_complex():
            particle.is_complex = True

        if hasattr(element.type, 'enumeration'):
            if element.type.enumeration is not None:
                particle.is_enum = True
                particle.enum_count = len(element.type.enumeration)

        self.__get_particle_integer_properties(particle, element)

        return particle

    def __get_abstract_particle(self, element: XsdElement, substitute: XsdElement):
        particle = Particle(prefix=self.__schema_prefix)

        particle.is_substitute = True

        if self.__is_abstract(substitute):
            particle.abstract = True

        particle.name = substitute.local_name

        particle.type = self.__get_type_name(substitute)
        particle.type_short = self.__get_type_name_short(substitute)
        particle.base_type = self.__get_base_type_name(substitute)
        particle.top_level_type = self.__get_primitive_type_name(substitute)

        if substitute.is_restriction(substitute):
            particle.min_occurs = element.effective_min_occurs
            if element.max_occurs is not None:
                particle.max_occurs = element.effective_max_occurs
            else:
                if element.local_name in OCCURRENCE_LIMITS_CORRECTED:
                    particle.max_occurs = OCCURRENCE_LIMITS_CORRECTED[element.local_name]
                    log_write(particle.name + " max_occurs changed from unbounded to " + str(particle.max_occurs))
                else:
                    particle.max_occurs = 1
                    log_write(particle.name + " max_occurs set to " + str(particle.max_occurs))

                particle.max_occurs_changed = True
                self.__add_to_max_occurs(particle.name, particle.max_occurs)

        if substitute.type.is_restriction():
            if substitute.type.min_length:
                particle.min_length = substitute.type.min_length

            if substitute.type.max_length:
                particle.max_length = substitute.type.max_length

            if substitute.type.min_value:
                particle.min_value = substitute.type.min_value

            if substitute.type.max_value:
                particle.max_value = substitute.type.max_value

        if substitute.type.is_complex():
            particle.is_complex = True

        if hasattr(substitute.type, 'enumeration'):
            if substitute.type.enumeration is not None:
                particle.is_enum = True
                particle.enum_count = len(substitute.type.enumeration)

        self.__get_particle_integer_properties(particle, element)

        return particle

    @staticmethod
    def __test_for_parent_sequence(particle, child_element: XsdElement):
        """
            If there is a sequence inside another sequence, it is possible that the
            restrictions for max and min occurs change because the subsequence has it own values.
            Therefore, this is checked and the restrictions are taken from the subsequence.
            This was noticed with the following type: DSAKeyValueType
        """
        if hasattr(child_element.parent, 'model'):
            if child_element.parent.model.casefold() == 'sequence':
                if hasattr(child_element.parent.parent, 'model'):
                    if child_element.parent.parent.model.casefold() == 'sequence':
                        particle.parent_model_changed_restrictions = True
                        particle.min_occurs_old = particle.min_occurs
                        particle.max_occurs_old = particle.max_occurs
                        particle.min_occurs = child_element.parent.min_occurs
                        particle.max_occurs = child_element.parent.max_occurs

                        sequence = []
                        for item in child_element.parent.iter_model():
                            sequence.append(item.local_name)

                        if len(sequence) > 0:
                            particle.parent_sequence = sequence
                            particle.parent_has_sequence = True

    @staticmethod
    def __test_for_parent_simple_content(particle, child_element: XsdElement):
        """
            This function checks for nameless simple content, e.g. in SignatureValueType.
            if such content is found, a flag is set inside the particle for later
            evaluation in decoder- or encoder classes.
        """
        if hasattr(child_element, 'type'):
            if hasattr(child_element.type, 'content'):
                if child_element.type.content_type_label == 'simple':
                    particle.has_simple_content = True
                    particle.simple_content_names.append(child_element.local_name)

    def __get_particle_list(self, element: XsdElement, subst_list):
        particles = []

        for child in element.iterchildren():
            if child.name is None:
                continue

            if self.__is_abstract(child):
                # get substituted particles for child
                qname = self.__get_name(child)
                subst_group = self.__current_schema.substitution_groups.target_dict.get(qname)
                if subst_group:
                    for elem in subst_group:
                        particle = self.__get_abstract_particle(child, elem)
                        particles.append(particle)
                        subst_list.append(elem)
                        self.__known_particles[particle.name] = particle
                else:
                    msg_write("No Substitute group (child) found for " + qname)
            else:
                particle = self.__get_particle(child)
                self.__test_for_parent_sequence(particle, child)
                self.__test_for_parent_simple_content(particle, child)
                particles.append(particle)

        if self.__is_abstract_type(element):
            # get substituted particles for element
            qname = self.__get_name(element)
            subst_group = self.__current_schema.substitution_groups.target_dict.get(qname)
            if subst_group:
                for elem in subst_group:
                    particle = self.__get_abstract_particle(element, elem)
                    particles.append(particle)
                    subst_list.append(elem)
                    self.__known_particles[particle.name] = particle
            else:
                msg_write("No Substitute group (element) found for " + qname)

        return particles

    @staticmethod
    def __add_choice_info_if_exists(element: XsdElement, elem_data: ElementData):
        def sub_manipulate_element_data(model_group: XsdGroup):
            elem_data.has_choice = True

            choice = Choice()
            for index, group in enumerate(model_group.iter_model()):
                if hasattr(group, "model"):
                    if group.model == 'sequence':
                        current = []
                        for seq_item in group.iter_model():
                            name = seq_item.local_name if seq_item.local_name is not None else 'other'
                            current.append([name, index + 1])

                        choice.choice_sequences.append(current)
                else:
                    name = group.local_name if group.local_name is not None else 'other'
                    choice.choice_items.append([name, index + 1])

            choice.min_occurs = model_group.min_occurs
            choice.multi_choice_max = 1
            if model_group.max_occurs is None:
                choice.is_multi_choice = True
            else:
                if model_group.max_occurs > 1:
                    choice.is_multi_choice = True
                    choice.multi_choice_max = model_group.max_occurs

            elem_data.choices.append(choice)
        # END of SubFunction

        if hasattr(element.type, "content"):
            if hasattr(element.type.content, "model"):
                if element.type.content.model == 'sequence':
                    for element_model in element.type.content.iter_model():
                        if hasattr(element_model, "model"):
                            if element_model.model == "choice":
                                sub_manipulate_element_data(element_model)

                elif element.type.content.model == 'choice':
                    elem_data.has_choice = True
                    # todo: remove next lines if decoder is adjusted
                    # START remove lines
                    elem_data.is_choice = True

                    seq = []
                    seq_current = 0
                    seq_old = 0
                    for component in element.type.content.iter_components():
                        if component.name is not None and seq_current > 0:
                            seq.append([component.local_name, seq_current])
                            for particle in elem_data.particles:
                                if particle.name == component.local_name:
                                    if particle.parent_choice_sequence_number < 0:
                                        particle.parent_has_choice_sequence = True
                                        particle.parent_choice_sequence_number = seq_current
                                        break
                        else:
                            if hasattr(component, "model"):
                                if str.casefold(component.model) == "sequence":
                                    seq_current += 1
                                    if seq_current != seq_old:
                                        if len(seq) > 0:
                                            elem_data.sequences.append(seq)
                                            elem_data.has_sequence = True
                                        seq = []
                                        seq_old = seq_current

                    # do not forget the last one
                    if len(seq) > 0:
                        elem_data.sequences.append(seq)
                        elem_data.has_sequence = True
                    # END remove lines

                    sub_manipulate_element_data(element.type.content)

    def __get_element_data_from_enum_attribute(self, attribute: XsdAttribute):
        element_data = ElementData(prefix=self.__schema_prefix)

        element_data.name = attribute.name
        element_data.name_short = attribute.local_name

        element_data.type = self.__get_type_name(attribute)
        element_data.type_short = self.__get_type_name_short(attribute)
        element_data.base_type = self.__get_base_type_name(attribute)

        if hasattr(attribute, "type"):
            if attribute.type.derivation:
                element_data.derivation = attribute.type.derivation

            if attribute.type.is_element_only():
                element_data.content_type = "ELEMENT-ONLY"
            else:
                if attribute.type.content_type_label:
                    element_data.content_type = attribute.type.content_type_label
                else:
                    element_data.content_type = ""

            is_enum = False
            if hasattr(attribute.type, "enumeration"):
                if attribute.type.enumeration is not None:
                    element_data.type_definition = "enum"
                    is_enum = True
                    if element_data.name not in self.__known_enums:
                        self.__known_enums[element_data.type] = element_data.type

                    for value in attribute.type.enumeration:
                        element_data.enum_list.append(value)

                    element_data.has_enum_list = True

            if not is_enum:
                if attribute.type.is_simple():
                    element_data.type_definition = "simple"
                else:
                    element_data.type_definition = "complex"

            if attribute.type.id:
                element_data.type_id = attribute.type.id

        return element_data

    def __get_element_data(self, element: XsdElement, level, count, subst_list):
        element_data = ElementData(prefix=self.__schema_prefix)
        element_data.level = level
        element_data.count = count

        if element.ref:
            element_data.ref = element.ref.local_name

        element_data.name = self.__get_name(element)
        element_data.name_short = self.__get_name_short(element)

        element_data.type = self.__get_type_name(element)
        element_data.type_short = self.__get_type_name_short(element)
        element_data.base_type = self.__get_base_type_name(element)

        if hasattr(element, "type"):
            if element.type.derivation:
                element_data.derivation = element.type.derivation

            if element.type.is_element_only():
                element_data.content_type = "ELEMENT-ONLY"
            else:
                if element.type.content_type_label:
                    element_data.content_type = element.type.content_type_label
                else:
                    element_data.content_type = ""

            is_enum = False
            if hasattr(element.type, "enumeration"):
                if element.type.enumeration:
                    element_data.type_definition = "enum"
                    is_enum = True
                    if element_data.name not in self.__known_enums:
                        self.__known_enums[element_data.type] = element_data.name

            if not is_enum:
                if element.type.is_simple():
                    element_data.type_definition = "simple"
                else:
                    element_data.type_definition = "complex"

            if element.type.id:
                element_data.type_id = element.type.id

        element_data.abstract = self.__is_abstract(element)
        element_data.abstract_type = self.__is_abstract_type(element)

        if element.final:
            element_data.final = element.final

        if hasattr(element, "type"):
            element_data.particles = []
            attribute_list = element.attributes
            if len(attribute_list) > 0:
                for attribute_name in attribute_list:
                    attribute = element.type.attributes[attribute_name]
                    element_data.particles.append(self.__get_particle_from_attribute(attribute))

                if element.type.content_type_label == 'simple':
                    for content in element.attributes.iter_components():
                        if content.__class__.__name__ == 'XsdAttributeGroup':
                            log_write(f'Adding CONTENT Particle to Element {element.local_name}')

                            if element.type.content.base_type is not None:
                                base_type = element.type.content.base_type.local_name
                            else:
                                base_type = element.type.base_type.local_name

                            part = Particle(prefix=self.__schema_prefix,
                                            name='CONTENT',
                                            base_type=base_type,
                                            type=base_type,
                                            type_short=element_data.type_short,
                                            is_simple_content=True,
                                            min_occurs=1,
                                            max_occurs=1)
                            element_data.particles.append(part)

            particles = self.__get_particle_list(element, subst_list)
            for particle in particles:
                element_data.particles.append(particle)

            element_data.sequences = []
            self.__add_choice_info_if_exists(element, element_data)

        return element_data

    def __get_child_tree(self, element: XsdElement, level, recursive=True):
        level += 1
        # todo: make recursion depth as global parameter
        if level > 10:
            return

        substitute_list = []
        count = 0
        for child in element.iterchildren():
            if child.name is None:
                continue

            count += 1
            type_name = self.__get_type_name(child)
            msg_write(level * "    " + str(level) + "." + str(count) + " " + child.name + " -> " + type_name)

            if child.ref:
                msg_write((level + 1) * "    " + "ref to: " + child.ref.local_name + " -> " + child.ref.type.local_name)

            if self.__is_abstract(child):
                msg_write((level + 1) * "    " + "ABSTRACT")

                element_data = self.__get_element_data(child, level, count, substitute_list)
                if self.__add_to_known_elements(child):
                    self.__generate_elements.append(element_data)

                if child.type.is_extension():
                    msg_write((level + 1) * "    " + "ABSTRACT TYPE is extension")

                qname = self.__get_name(child)
                sg = self.__current_schema.substitution_groups.target_dict.get(qname)
                if sg:
                    for substitute in sg:
                        substitute_type_name = self.__get_type_name(substitute)
                        msg_write(level * "    " + str(level) + "." + str(count) + " " +
                                  substitute.name + " -> " + substitute_type_name)
                        if substitute.type.is_complex():
                            if self.__add_to_known_elements(substitute):
                                sl = []
                                substitute_data = self.__get_element_data(substitute, level, count, sl)
                                self.__generate_elements.append(substitute_data)

                            msg_write(self.__build_particle_comment(substitute, level + 1))
                            self.__get_child_tree(substitute, level)
                else:
                    msg_write((level + 1) * "    " + "No Substitute group found for " + qname)

            else:
                element_data = self.__get_element_data(child, level, count, substitute_list)
                if substitute_list:
                    msg_write((level + 1) * "    " + "Substitute list has elements ...")
                    for substitute in substitute_list:
                        substitute_type_name = self.__get_type_name(substitute)
                        msg_write(level * "    " + str(level) + "." + str(count) + " " +
                                  substitute.name + " -> " + substitute_type_name)
                        if substitute.type.is_complex():
                            if self.__add_to_known_elements(substitute):
                                sl = []
                                substitute_data = self.__get_element_data(substitute, level, count, sl)
                                self.__generate_elements.append(substitute_data)

                            msg_write(self.__build_particle_comment(substitute, level + 1))
                            self.__get_child_tree(substitute, level)

                if child.type.is_extension():
                    msg_write((level + 1) * "    " + "TYPE is extension")

                if child.type.is_complex() or element_data.type_definition == "enum":
                    if self.__add_to_known_elements(child):
                        self.__generate_elements.append(element_data)

                    if child.type.is_complex():
                        msg_write(self.__build_particle_comment(child, level + 1))
                        if recursive:
                            child_count = self.__get_child_count(child)
                            if child_count > 0:
                                self.__get_child_tree(child, level)

                if hasattr(child.type, "content"):
                    if hasattr(child.type.content, "model"):
                        if child.type.content.model == 'choice':
                            msg_write(level * "    " + "TYPE CONTENT of " + child.local_name + " is choice")

                            for content_model in child.type.content.iter_components():
                                if content_model.name is not None:
                                    msg_write((level + 1) * "    " + "name: " + content_model.name)
                                else:
                                    if hasattr(content_model, "model"):
                                        msg_write((level + 1) * "    " + "model: " + content_model.model)

    # ---------------------------------------------------------------------------
    # general analyzer functions
    # ---------------------------------------------------------------------------
    def analyze_schema_elements(self):
        level = 0
        count = 0

        subst_list = []

        msg_write("\nSchema: child count=" + str(self.__get_child_count(self.__current_schema)))
        for element_str in self.__current_schema.elements:
            element: XsdElement = self.__current_schema.elements.get(element_str)
            element_data = self.__get_element_data(element, level, count, subst_list)

            if element.type.is_complex():
                if element.type.qualified_name:
                    if element.type.qualified_name not in self.__known_elements:
                        self.__known_elements[element.type.qualified_name] = element.type.local_name
                        self.__generate_elements.append(element_data)
                        self.__root_elements.append(element_data)
                else:
                    if element.qualified_name not in self.__known_elements:
                        self.__known_elements[element.qualified_name] = element.local_name
                        self.__generate_elements.append(element_data)
                        self.__root_elements.append(element_data)

            self.__get_child_tree(element, level)
            count += 1

        # Build list of builtin types
        self.__build_schema_builtin_types_list()

        # Build list of generate elements types
        self.__build_generate_elements_types_list()

        # Build list of elements for namespaces
        self.__build_namespace_element_lists()

        # Scan the abstract elements for occurrence in namespace elements and replace particle list
        self.__scan_abstract_types_for_namespace_elements()

        # Scan for elements with content_type=empty
        # Caution! This has to be done after scanning for abstract types, not before.
        # Otherwise the types are not generated correctly.
        self.__scan_elements_for_empty_content()
        self.__scan_particles_for_empty_parent_type()

        # Adjust min_occurs for elements in choices
        self.__adjust_choice_elements()

        # Check memory option and make optimization
        if self.config['apply_optimizations'] == 1:
            self.__apply_array_optimizations()

        # Do the preparations for type generation
        self.__prepare_for_type_generation()

    def __build_schema_builtin_types_list(self):
        xs_namespace = self.__current_schema.namespaces['xs']
        for value in self.__current_schema.types.target_dict.values():
            if value.target_namespace == xs_namespace:
                if value.__class__.__name__ == 'XsdAtomicBuiltin':
                    if value.simple_type.base_type is not None:
                        self.__schema_builtin_types[value.local_name] = value.simple_type.base_type.local_name
                    else:
                        self.__schema_builtin_types[value.local_name] = value.simple_type.local_name

    def __build_namespace_element_lists(self):
        """
            This function builds the lists needed to generate the root struct and root decoding function.
            The list for namespace types is built also. With this list the namespace struct and decoder
            can be generated.
        """
        # Build the list for main struct or decoding function, probably something with exiDocument
        current_namespace = self.__current_schema.get_schema('')
        for ele in current_namespace.elements.values():
            items = []
            for value in current_namespace.elements.target_dict.values():
                if value.default_namespace:
                    name = self.__get_type_name_short(value)
                    if name == '' or name in ['AnonType', 'string']:
                        name = self.__get_name_short(value)
                    items.append(name)
            items.sort()
            self.__namespace_elements[ele.local_name] = items

        # Build the lists for the namespaces, e.g. MessageHeader or MessageBody and replace the particle list
        if hasattr(current_namespace, 'imports'):
            if len(current_namespace.imports) > 0:
                for imp in current_namespace.imports.values():
                    items = []
                    name = imp.complex_types[0].local_name
                    for ele in imp.elements.values():
                        particle = self.__get_particle(ele)
                        # min_occurs and is_substitute has to be set to original values
                        particle.min_occurs = 0
                        particle.is_substitute = True
                        items.append(particle)

                    if len(items) > 0:
                        for gen_elem in self.__generate_elements:
                            if gen_elem.type == '{' + imp.default_namespace + '}' + name:
                                gen_elem.particles = items
                                gen_elem.is_in_namespace_elements = True
                                self.__namespace_elements[name] = items
                                break

    def __build_generate_elements_types_list(self):
        xs_namespace = self.__current_schema.namespaces['xs']
        type_list = []
        for value in self.__current_schema.types.target_dict.values():
            if value.target_namespace != xs_namespace and value.content_type_label == 'element-only':
                type_list.append(value.local_name)

        log_write('')
        log_write('GENERATE ELEMENTS TYPES LIST')
        for element in self.__generate_elements:
            if element.type_short in type_list:
                self.__generate_elements_types[element.type_short] = element.base_type
                log_write(f'Element type={element.type_short}, base type={element.base_type}')

        log_write('')

    def __scan_abstract_types_for_namespace_elements(self):
        """
            This function scans the list of elements to generate for abstract types.
            In DIN 70121 schema are the types defined as abstract, in ISO 15118-2
            could be either the elements or some types defined as abstract.
            But this function checks, if an abstract element is found, all elements
            for an abstract particle with the same name as the abstract element.
            If this element name has an entry in the namespace element list,
            the particles of this element are replaced.
            This is mainly for the DIN schema to solve the hierarchical problem
            with Body and BodyElement.
        """
        for abstract_element in self.__generate_elements:
            if abstract_element.abstract_type:
                for element in self.__generate_elements:
                    for particle in element.particles:
                        if abstract_element.name_short == particle.name and particle.abstract_type:
                            if particle.name in self.__namespace_elements.keys():
                                log_write('')
                                log_write(f'Found particle match in namespace elements. '
                                          f'Replacing particles of {element.name_short} ({element.type_short})')
                                particle.is_substitute = True
                                particles = [particle]
                                for part in abstract_element.particles:
                                    particles.append(part)
                                element.particles = particles
                                element.is_in_namespace_elements = True
                                break

    def __scan_particles_for_empty_parent_type(self):
        empty_list = []
        for element in self.__generate_elements:
            if element.content_type == 'empty' or (len(element.particles) == 0 and element.type_definition != 'enum'):
                empty_list.append(element.name_short)

        for element in self.__generate_elements:
            if len(empty_list) > 0:
                for particle in element.particles:
                    if particle.is_complex and particle.name in empty_list:
                        particle.parent_type_is_empty = True

    def __get_parent_elements_from_empty_content_element(self, empty_content_element_name):
        parents = []

        for element in self.__generate_elements:
            for particle in element.particles:
                if particle.name == empty_content_element_name:
                    parents.append(element)
                    break

        return parents

    def __get_parent_elements_with_search_list_particles(self, search_list, element_name):
        parents = []

        for element in self.__generate_elements:
            if element.name_short != element_name:
                count = 0
                for particle in element.particles:
                    if particle.name in search_list:
                        count += 1

                if count == len(search_list):
                    parents.append(element)

        return parents

    @staticmethod
    def __replace_particle_list_in_parent(parent_element: ElementData, particle_list: list,
                                          replacement_list: list,
                                          min_occurs: int, max_occurs: int):
        """
        Drop the particles in particle_list from parent, and replace them (in place)
        with the sorted particles from replacement_list.
        """
        # the replacements need to be sorted alphabetically
        replacement_list.sort(key=lambda particle_key: particle_key.name)

        # the particles need to be sorted by index, for proper removal
        particle_list.sort(key=lambda x: x[0])

        # sanity-check the particle list for contiguity
        for i, pi in enumerate(particle_list):
            if i > 0 and particle_list[i][0] != (particle_list[i-1][0] + 1):
                log_write(f"particle indices are not contiguous for '{parent_element.name_short}' at {i}: " +
                          f"{particle_list[i][1].name}, index {particle_list[i][0]} after " +
                          f"{particle_list[i-1][1].name} index {particle_list[i-1][0]}")

        # drop all the particles listed in particle_list
        p_index: int
        for p_index, p in reversed(particle_list):
            if parent_element.particles[p_index] != p:
                log_write(f"particle '{p.name}' not found in '{parent_element.name_short}'")
            del parent_element.particles[p_index]

        # insert the replacements at the original position, assuming the lowest original particle
        # index is now the correct one
        parent_particles_old_hi = parent_element.particles[p_index:]
        parent_element.particles = parent_element.particles[:p_index]
        abstract_seq = []
        for part in replacement_list:
            log_write(f'    Add particle from list {part.name}.')
            parent_element.particles.append(part)
            abstract_seq.append(part.name)
        parent_element.particles.extend(parent_particles_old_hi)

        parent_element.has_abstract_sequence = True
        # FIXME abstract_seq may need to inherit min/max_occurs(_old)
        parent_element.abstract_sequences.append((abstract_seq, min_occurs, max_occurs))

    def __copy_particles_from_empty_content_elements(self, element: ElementData, parents):
        parent: ElementData
        for parent in parents:
            replacement_list = []
            log_write(f'  Copying particle(s) of {element.name_short} to {parent.name_short}.')
            particles_to_remove = []  # list of tuples (index within parent, particle)
            particle: Particle
            p_min_occurs: int = None
            p_max_occurs: int = None
            for particle in element.particles:
                exist = [x for x in parent.particles if x.name == particle.name]
                if len(exist) == 0:
                    log_write(f'    Add to list and set substitute to false {particle.name}.')
                    # FIXME abstract_seq may need to inherit min/max_occurs(_old)
                    p_min_occurs = particle.min_occurs
                    p_max_occurs = particle.max_occurs
                    particle.min_occurs = 0
                    particle.is_substitute = False
                    replacement_list.append(particle)
                else:
                    log_write(f'    Add to list and remove particle {particle.name}.')
                    replacement_list.append(particle)
                    if particle in parent.particles:
                        particles_to_remove.append((parent.particles.index(particle), particle))

            for particle in parent.particles:
                if particle.name == element.name_short:
                    log_write(f'    Add to list and remove particle {particle.name}.')
                    p_min_occurs = particle.min_occurs
                    p_max_occurs = particle.max_occurs
                    particle.min_occurs = 0
                    replacement_list.append(particle)
                    particles_to_remove.append((parent.particles.index(particle), particle))

            if len(replacement_list) > 0:
                self.__replace_particle_list_in_parent(parent, particles_to_remove, replacement_list,
                                                       p_min_occurs, p_max_occurs)

    def __copy_particles_from_empty_content_elements_particle(self, element: ElementData, parents):
        parent: ElementData
        for parent in parents:
            if parent.name_short != element.name_short:
                replacement_list = []
                particles_to_remove = []  # list of tuples (index within parent, particle)
                log_write(f'  Copying particle(s) of {element.name_short} to {parent.name_short}.')
                part_index: int
                p_min_occurs: int = None
                p_max_occurs: int = None
                for p in element.particles:
                    part: Particle
                    for part_index, part in enumerate(parent.particles):
                        if part.name == p.name:
                            log_write(f'    Add to list and remove particle {part.name}.')
                            # FIXME abstract_seq may need to inherit min/max_occurs(_old)
                            p_min_occurs = part.min_occurs
                            p_max_occurs = part.max_occurs
                            part.min_occurs = 0
                            part.is_substitute = False
                            particles_to_remove.append((part_index, part))
                            replacement_list.append(part)
                            break

                # finally, also add the original, abstract particle to the replacements
                log_write(f'    Add new particle to list {element.name_short}.')
                part_new = Particle(prefix=self.__schema_prefix,
                                    name=element.name_short,
                                    base_type=element.base_type,
                                    type=element.type,
                                    type_short=element.type_short,
                                    min_occurs=0,
                                    max_occurs=1)
                replacement_list.append(part_new)

                self.__replace_particle_list_in_parent(parent, particles_to_remove, replacement_list,
                                                       p_min_occurs, p_max_occurs)

    def __scan_elements_for_empty_content(self):
        """
            This function scans the list of elements to generate for content_type=empty.
            If such an element is found, but it has particles, these particles are copied
            to the elements having the empty one. Afterwards the particle list of the
            empty element is cleared.
            This helps to avoid generating types and code that is not used and
            bloats the generated code.

            Similar for abstract elements with a reference.
            Here is a list with names of the same base type generated and matching parents found.
            If the abstract element is missing in the parent particles, the element is created and added.
            These elements are just for getting the correct bit count and event IDs in de- or encoding.

            Caution!
            Deleting the empty element from the parent element is not a good idea,
            because it also deletes these empty elements, which are necessary for enumerating
            and generating IDs or codes.
        """
        element: ElementData
        for element in self.__generate_elements:
            if element.content_type == 'empty':
                log_write('')
                log_write(f'{element.name_short} ({element.type_short}) has empty content.')
                if len(element.particles) > 0:
                    parents = self.__get_parent_elements_from_empty_content_element(element.name_short)
                    if len(parents) > 0:
                        self.__copy_particles_from_empty_content_elements(element, parents)
                    else:
                        parents = self.__get_parent_elements_from_empty_content_element(element.particles[0].name)
                        if len(parents) > 0:
                            self.__copy_particles_from_empty_content_elements_particle(element, parents)

                    log_write(f'  Deleting {len(element.particles)} particle(s) of {element.name_short}.')
                    element.particles = []
            elif element.abstract and element.ref is not None:
                log_write('')
                log_write(f'{element.name_short} ({element.type_short}) is abstract and has a reference.')
                search_list = []
                particle: Particle
                for particle in element.particles:
                    if particle.base_type == element.type_short:
                        search_list.append(particle.name)

                if search_list:
                    parents = self.__get_parent_elements_with_search_list_particles(search_list, element.name_short)
                    for parent in parents:
                        found = False
                        for particle in parent.particles:
                            if particle.name == element.name_short:
                                found = True
                                break

                        if not found:
                            re_list = []
                            log_write(f'  Copying particle(s) of {element.name_short} to {parent.name_short}.')
                            p_min_occurs: int = None
                            p_max_occurs: int = None
                            for name in search_list:
                                part: Particle
                                for part in parent.particles:
                                    if part.name == name:
                                        log_write(f'    Add to list and remove particle {part.name}.')
                                        p_min_occurs = part.min_occurs
                                        p_max_occurs = part.max_occurs
                                        part.min_occurs = 0
                                        part.is_substitute = False
                                        re_list.append(part)
                                        parent.particles.remove(part)
                                        break

                            log_write(f'    Add new particle to list {element.name_short}.')
                            part = Particle(prefix=self.__schema_prefix,
                                            name=element.name_short,
                                            base_type=element.base_type,
                                            type=element.type,
                                            type_short=element.type_short,
                                            min_occurs=0,
                                            max_occurs=1)
                            re_list.append(part)

                            if len(re_list) > 0:
                                re_list.sort(key=lambda particle_key: particle_key.name)
                                abstract_seq = []
                                for part in re_list:
                                    log_write(f'    Add particle from list {part.name}.')
                                    parent.particles.append(part)
                                    abstract_seq.append(part.name)

                                parent.has_abstract_sequence = True
                                parent.abstract_sequences.append((abstract_seq, p_min_occurs, p_max_occurs))

    def __adjust_choice_elements(self):
        log_write('')
        log_write('Adjusting choice elements')
        for element in self.__generate_elements:
            if element.has_choice:
                choice_list = []
                for choice in element.choices:
                    for item in choice.choice_items:
                        choice_list.append(item[0])

                for particle in element.particles:
                    if particle.name in choice_list:
                        log_write(f'    Setting min_occurs of {particle.name} to 0.')
                        particle.content_model_changed_restrictions = True
                        particle.min_occurs_old = particle.min_occurs
                        particle.min_occurs = 0
                        # we may need to force this to avoid peculiar choice particle properties
                        # particle.max_occurs = 1

    def __apply_array_optimizations(self):
        config_module = get_config_module()
        parameter = self.__schema_prefix + 'array_optimizations'
        if hasattr(config_module, parameter):
            optimizations = getattr(config_module, parameter)
        else:
            return

        for element in self.__generate_elements:
            for particle in element.particles:
                if (particle.type_short in optimizations.keys()
                    and particle.max_occurs > optimizations[particle.type_short]):
                    particle.max_occurs = optimizations[particle.type_short]

    def __prepare_for_type_generation(self):
        # Sort the list of elements to be generated by level and count
        self.__generate_elements.sort(key=lambda item: item.count, reverse=False)
        self.__generate_elements.sort(key=lambda item: item.level, reverse=True)

    def write_analyzer_data_to_log(self):
        log_write("")
        log_write_dict("KNOWN ELEMENTS", self.__known_elements)
        log_write_dict("KNOWN PARTICLES", self.__known_particles)
        log_write_dict("KNOWN ENUMS", self.__known_enums)
        log_write_dict("KNOWN PROTOTYPES", self.__known_prototypes)
        log_write_dict("CHANGED MAX OCCURRENCE", self.__max_occurs_changed)
        log_write_dict("NAMESPACE ELEMENTS", self.__namespace_elements)

        log_write("ELEMENTS pos data:\n")
        for elem in self.__generate_elements:
            log_write_element_pos_data(elem)

        log_write("ELEMENTS to generate:\n")
        for elem in self.__generate_elements:
            log_write_element(elem)

        log_write("")
        log_write("ROOT ELEMENTS to generate:\n")
        for root_elem in self.__root_elements:
            log_write_element(root_elem)
