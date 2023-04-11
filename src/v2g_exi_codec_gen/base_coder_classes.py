# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 chargebyte GmbH
# Copyright (c) 2022 - 2023 Contributors to EVerest

from typing import List
from v2g_exi_codec_gen import tools_generator, tools
from v2g_exi_codec_gen.elementData import Particle, ElementData, Choice
from v2g_exi_codec_gen.elementGrammar import GrammarFlag, ElementGrammar, ElementGrammarDetail
from v2g_exi_codec_gen.tools_config import CONFIG_PARAMS
from v2g_exi_codec_gen.tools_logging import log_write_error, log_init_logger, log_write_logger, \
    log_deinit_logger, log_exists_logger

# ---------------------------------------------------------------------------
# Exi decoder and encoder common base header class
# ---------------------------------------------------------------------------


class ExiBaseCoderHeader:
    def __init__(self, parameters, enable_logging=True):
        self.generator = tools_generator.get_generator()
        self.config = CONFIG_PARAMS
        self.parameters = parameters
        self.h_params = parameters.get('h', None)
        self.logging_enabled = enable_logging
        self.logger_name = ''

        if self.logging_enabled:
            self.logger_name = str(self.h_params['filename'])
            if self.logger_name.casefold().endswith('.h') or self.logger_name.casefold().endswith('.c'):
                self.logger_name = self.logger_name[:len(self.logger_name) - 2]

            if not log_exists_logger(self.logger_name):
                log_init_logger(self.logger_name, f'{self.logger_name}.txt')

    def disable_logging(self):
        if self.logging_enabled and self.logger_name != '':
            log_deinit_logger(self.logger_name)
            self.logging_enabled = False

    def log(self, message):
        if self.logging_enabled:
            log_write_logger(self.logger_name, message)

    def generate_file(self):
        log_write_error('The function generate_file() is not implemented in subclass.')
        raise NotImplementedError

# ---------------------------------------------------------------------------
# Exi decoder and encoder common base code class
# ---------------------------------------------------------------------------


class ExiBaseCoderCode:
    def __init__(self, parameters, analyzer_data, enable_logging=True):
        self.generator = tools_generator.get_generator()
        self.config = CONFIG_PARAMS
        self.parameters = parameters
        self.c_params = parameters.get('c', None)
        self.analyzer_data = analyzer_data
        self.logging_enabled = enable_logging
        self.logger_name = ''

        if self.logging_enabled:
            self.logger_name = str(self.c_params['filename'])
            if self.logger_name.casefold().endswith('.h') or self.logger_name.casefold().endswith('.c'):
                self.logger_name = self.logger_name[:len(self.logger_name) - 2]

            if not log_exists_logger(self.logger_name):
                log_init_logger(self.logger_name, f'{self.logger_name}.txt')

        self.indent = tools.get_indent()

        self.elements_generated = None
        self.elements_to_generate = None
        self.known_type_names = None
        self.grammar_id = 0
        self.grammar_end_element = 0
        self.grammar_unknown = 0
        self.element_grammars = None

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
    # debug log helper functions
    # ---------------------------------------------------------------------------
    def get_status_for_add_debug_code(self, prefixed_type_name):
        if self.analyzer_data.add_debug_code_enabled:
            fn = ''

            if self.__class__.__name__ == 'ExiEncoderCode':
                fn = str(CONFIG_PARAMS['encode_function_prefix'] + prefixed_type_name)
            elif self.__class__.__name__ == 'ExiDecoderCode':
                fn = str(CONFIG_PARAMS['decode_function_prefix'] + prefixed_type_name)

            fn_up = fn.upper()
            if fn_up not in self.analyzer_data.debug_code_messages:
                self.analyzer_data.debug_code_messages[fn_up] = [self.analyzer_data.debug_code_current_message_id, fn]
                self.analyzer_data.debug_code_current_message_id += 1

        return self.analyzer_data.add_debug_code_enabled

    # ---------------------------------------------------------------------------
    # general helper functions
    # ---------------------------------------------------------------------------
    @staticmethod
    def left_trim_lf(text):
        if text.startswith('\n'):
            return text[1:]

        return text

    @staticmethod
    def trim_lf(text):
        if text.endswith('\n'):
            return text[:len(text) - 1]

        return text

    def init_lists_for_generating_elements(self):
        self.elements_generated = []
        self.elements_to_generate = []
        for element in self.analyzer_data.generate_elements:
            if element.type_definition == 'complex':
                self.elements_to_generate.append(element)

    def init_list_with_known_type_names(self):
        self.known_type_names = []
        for element in self.analyzer_data.generate_elements:
            if element.type_definition == 'complex' or element.type_definition == 'enum':
                self.known_type_names.append(element.name_short)

    @staticmethod
    def create_empty_grammar():
        result = ElementGrammar()
        result.details = []

        return result

    @staticmethod
    def has_element_array_particle(element: ElementData):
        result = False

        for particle in element.particles:
            if particle.is_array:
                result = True
                break

        return result

    @staticmethod
    def get_element_array_particle_names(element: ElementData):
        result = []

        for particle in element.particles:
            if particle.is_array:
                result.append(particle.name)

        return result

    # ---------------------------------------------------------------------------
    # generator helper functions
    # ---------------------------------------------------------------------------
    def reset_grammar_ids(self):
        self.grammar_id = 0
        self.grammar_end_element = 0
        self.grammar_unknown = 0

    def reset_element_grammars(self):
        self.element_grammars: list[ElementGrammar] = []

    def is_in_namespace_elements(self, element: ElementData):
        if element.type_short in self.analyzer_data.namespace_elements.keys():
            return True

        return False

    def test_on_skip(self, element: ElementData):
        result = False

        for particle in element.particles:
            if particle.is_complex:
                # building particle type
                type_name = particle.type_short
                if type_name == 'AnonType':
                    type_name = particle.name

                if type_name not in self.elements_generated:
                    # skip here! generate type first before we can use it
                    result = True
                    break

        return result

    @staticmethod
    def move_end_element_to_end_of_list(grammar: ElementGrammar):
        if grammar.details_count > 1:
            if grammar.details[0].flag == GrammarFlag.END:
                grammar.details.append(grammar.details[0])
                grammar.details.remove(grammar.details[0])

    @staticmethod
    def get_start_grammar_id(grammars: List[ElementGrammar]):
        result = -1
        has_start = False

        if len(grammars) > 2:
            for grammar in grammars:
                for detail in grammar.details:
                    if detail.flag == GrammarFlag.START:
                        has_start = True
                        break

                if has_start:
                    result = grammar.grammar_id
                    break

        return result

    def _get_choice_options(self, element: ElementData, particle: Particle):
        """
        Return a list containing:
        - an ordered list of all particles (proper or abstract) belonging to the same choice
            group as the given particle.
        - a list of the choice group item names (for comparison)
        - the min_occurs of this particle group
        - the max_occurs of this particle group
        """
        if element.has_choice:
            element_choice: Choice
            for element_choice in element.choices:  # choice object from list of choice objects
                for choice_item in element_choice.choice_items:  # list of choice names from choice object
                    if particle.name == choice_item[0]:  # first element is name, second element is index
                        li: list[Particle] = [element.particle_from_name(x[0]) for x in element_choice.choice_items]
                        return [li, element_choice.choice_items, element_choice.min_occurs, element_choice.multi_choice_max]  # FIXME choice occurrences
        elif element.has_abstract_sequence:
            for abstract_choice_list, min_occurs, max_occurs in element.abstract_sequences:
                for choice_item in abstract_choice_list:
                    if particle.name == choice_item:
                        li: list[Particle] = [element.particle_from_name(x) for x in abstract_choice_list]
                        return [li, abstract_choice_list, min_occurs, max_occurs]
        # particle is not a choice, or fallback on failure to find
        return []

    def append_end_and_unknown_grammars(self, typename):
        grammar = self.create_empty_grammar()
        grammar.details.append(ElementGrammarDetail(flag=GrammarFlag.END))
        self.append_id_to_element_grammars(grammar, self.grammar_end_element, typename)

        grammar = self.create_empty_grammar()
        grammar.details.append(ElementGrammarDetail(flag=GrammarFlag.ERROR))
        self.append_id_to_element_grammars(grammar, self.grammar_unknown, typename)

    def append_id_to_element_grammars(self, grammar: ElementGrammar, grammar_id, element_typename):
        grammar.grammar_id = grammar_id
        grammar.element_typename = element_typename
        self.element_grammars.append(grammar)

        self.log(grammar.grammar_comment)

    def append_to_element_grammars(self, grammar: ElementGrammar, element_typename):
        grammar.grammar_id = self.grammar_id
        grammar.element_typename = element_typename
        self.element_grammars.append(grammar)

        self.log(grammar.grammar_comment)
        self.grammar_id += 1

    def generate_element_grammars(self, element: ElementData):
        self.reset_element_grammars()
        particle_is_part_of_sequence = False

        # if the current element type is in the namespace elements dict,
        # just generate one start tag and an end tag.
        if element.is_in_namespace_elements and len(element.particles) > 0:
            part: Particle = element.particles[0]
            grammar = self.create_empty_grammar()
            grammar.details.append(ElementGrammarDetail(flag=GrammarFlag.START, particle=part))
            self.append_to_element_grammars(grammar, element.typename)
            return

        index_last_nonoptional_particle = -1
        particle: Particle  # type hint
        for particle_index, particle in enumerate(element.particles):
            # FIXME this could be done backwards with a "break"
            choices = self._get_choice_options(element, particle)
            combined_min_occurs_from_choice = choices[2] if choices else particle.min_occurs
            if combined_min_occurs_from_choice == 1:
                index_last_nonoptional_particle = particle_index

        def _particle_is_in_choice(element: ElementData, particle: Particle):
            """
            Return True if the given particle is part of (any) choice group in the
            given element.
            Else return False.
            """
            if not element.has_choice:
                return False
            for element_choice in element.choices:
                for choice_item in element_choice.choice_items:
                    if particle.name == choice_item[0]:
                        return True
            return False

        def _particle_is_in_abstract_choice(element: ElementData, particle: Particle):
            """
            Return True if the given particle is part of (any) abstract "sequence" choice
            group in the given element.
            Else return False.
            """
            if not element.has_abstract_sequence:
                return False
            for abstract_choice_list, min_occurs, max_occurs in element.abstract_sequences:
                for choice_item in abstract_choice_list:
                    if particle.name == choice_item:
                        return True
            return False

        def _get_choice_sequence(element: ElementData, particle: Particle) -> []:
            """
            Return an ordered list of all particles belonging to the same choice sequence as
            the given particle.
            """
            if particle.parent_has_choice_sequence:
                for choice_obj in element.choices:
                    choice_sequence = choice_obj.choice_sequences[particle.parent_choice_sequence_number - 1]  # list of [name, index] list
                    for choice_item in choice_sequence:
                        if particle.name == choice_item[0]:  # first element is name, second element is index
                            li: list[Particle] = [element.particle_from_name(x[0]) for x in choice_sequence]
                            return li
                log_write_error(f"failed to find choice sequence for of {particle.name}")

            # particle is not in a choice sequence, or fallback on failure to find
            return []

        def _debug_element_particle_properties(element: ElementData):
            particle: Particle
            for particle in element.particles:
                log_write_error(f"Investigating particle '{particle.name}'")
                log_write_error(f"\tmin_occurs: {particle.min_occurs}")
                log_write_error(f"\tmax_occurs: {particle.max_occurs}")
                if particle.min_occurs_old != -1 and not particle.parent_has_sequence:
                    log_write_error(f"\tpeculiar: min_occurs_old: {particle.min_occurs_old}")
                if particle.max_occurs_old != -1 and not particle.parent_has_sequence:
                    log_write_error(f"\tpeculiar: max_occurs_old: {particle.max_occurs_old}")
                if _particle_is_in_choice(element, particle):
                    group = []
                    group, choice_name_list, min_o, max_o = self._get_choice_options(element, particle)
                    log_write_error(f"\tis in a choice group, min_occurs = {min_o}, max_occurs = {max_o}")
                    log_write_error([x.name if x is not None else '' for x in group])
                if _particle_is_in_abstract_choice(element, particle):
                    group = []
                    group, choice_name_list, min_o, max_o = self._get_choice_options(element, particle)
                    log_write_error(f"\tis in an abstract choice group, min_occurs = {min_o}, max_occurs = {max_o}")
                    log_write_error([x.name if x is not None else '' for x in group])
                if particle.parent_has_sequence:
                    log_write_error("\tis in a sequence")
                    log_write_error(f"\tmin_occurs_old: {particle.min_occurs_old}")
                    log_write_error(f"\tmax_occurs_old: {particle.max_occurs_old}")
                if particle.parent_has_choice_sequence:
                    log_write_error(f"\tparent is in a sequence which is choice, number {particle.parent_choice_sequence_number}")
                    log_write_error([x.name if x is not None else '' for x in _get_choice_sequence(element, particle)])

        # _debug_element_particle_properties(element)

        grammar = self.create_empty_grammar()

        def _add_subsequent_grammar_details(element: ElementData, particle: Particle,
                                            grammar: ElementGrammar,
                                            particle_index: int, index_last_nonoptional_particle: int,
                                            particle_is_part_of_sequence: bool):
            if particle_index > index_last_nonoptional_particle:
                # all the following particles are optional, so END needs to be an expected event
                # at the beginning of the event/grammar detail list
                if not particle_is_part_of_sequence:
                    grammar.details.append(ElementGrammarDetail(flag=GrammarFlag.END))
                else:
                    if str(particle.parent_sequence[0]) == particle.name:
                        grammar.details.append(ElementGrammarDetail(flag=GrammarFlag.END))

            def _add_particle_or_choice_list_to_details(element, grammar, particle, previous_choice_list):
                choice_list = self._get_choice_options(element, particle)
                if choice_list:
                    if choice_list[1] != previous_choice_list:
                        for choice in choice_list[0]:
                            grammar.details.append(ElementGrammarDetail(flag=GrammarFlag.START, particle=choice))
                        previous_choice_list.extend(choice_list[1])
                else:
                    grammar.details.append(ElementGrammarDetail(flag=GrammarFlag.START, particle=part))
                    previous_choice_list.clear()

            previous_choice_list = []  # to check whether this choice has already been handled

            # for the current particle, check all successors in the particle list
            for n, part in enumerate(element.particles[particle_index:], start=particle_index):
                if part.max_occurs == 1 and not part.max_occurs_changed:
                    if part.parent_has_sequence:
                        particle_is_part_of_sequence = True

                    if not particle_is_part_of_sequence or n == particle_index:
                        _add_particle_or_choice_list_to_details(element, grammar, part, previous_choice_list)

                        if n < len(element.particles) - 1:
                            if not element.particles[n + 1].parent_has_sequence:
                                particle_is_part_of_sequence = False

                                if part.min_occurs_old == 1 or (n == len(element.particles) - 1):
                                    self.append_to_element_grammars(grammar, element.typename)
                                    grammar = self.create_empty_grammar()
                                    break  # end of grammar for current particle
                    else:
                        if not part.parent_has_sequence:
                            grammar.details.append(ElementGrammarDetail(flag=GrammarFlag.START, particle=part))
                            particle_is_part_of_sequence = False
                        else:
                            if str(part.parent_sequence[0]) == part.name:
                                # not-optional or last particle in element: end of grammar list
                                if part.min_occurs_old == 1 or (n == len(element.particles) - 1):
                                    _add_particle_or_choice_list_to_details(element, grammar, part, previous_choice_list)
                                    self.append_to_element_grammars(grammar, element.typename)
                                    grammar = self.create_empty_grammar()
                                    break  # end of grammar for current particle

                    # not-optional or last particle in element: end of grammar list
                    choice_for_part = self._get_choice_options(element, part)
                    part_min = choice_for_part[2] if choice_for_part else 0
                    # FIXME: do these need to be >= 1?
                    if part.min_occurs == 1 or part_min == 1 or (n == len(element.particles) - 1):
                        self.append_to_element_grammars(grammar, element.typename)
                        grammar = self.create_empty_grammar()
                        break  # end of grammar for current particle
                elif part.max_occurs > 1 or part.max_occurs_changed:
                    if part.max_occurs < 25:
                        _max = part.max_occurs
                        # if max_occurs was reduced to 1, make sure to create the proper grammar after the one occurence
                        # This should be done only if the caller is not the encoder
                        if self.__class__.__name__ != 'ExiEncoderCode':
                            # FIXME: should also apply to max_occurs > 1?
                            if part.max_occurs == 1 and part.max_occurs_changed:
                                _max += 1
                        for m in range(0, _max):
                            if m >= part.min_occurs and m > 0:  # optional, and grammar 0 already contains END
                                _add_subsequent_grammar_details(element, particle, grammar, n + 1,
                                                                index_last_nonoptional_particle,
                                                                particle_is_part_of_sequence)

                            _add_particle_or_choice_list_to_details(element, grammar, part, previous_choice_list)
                            self.append_to_element_grammars(grammar, element.typename)
                            grammar = self.create_empty_grammar()
                    else:
                        for m in [0, 1]:
                            # FIXME: LOOP not implemented
                            # FIXME: fix this to correspond to the above - as yet unused
                            if m >= part.min_occurs and m > 0:  # grammar 0 already contains END
                                grammar.details.append(ElementGrammarDetail(flag=GrammarFlag.END))

                            if m == 0:
                                grammar.details.append(ElementGrammarDetail(flag=GrammarFlag.START, particle=part))
                            else:
                                grammar.details.append(ElementGrammarDetail(flag=GrammarFlag.LOOP, particle=part))

                            self.append_to_element_grammars(grammar, element.typename)
                            grammar = self.create_empty_grammar()

                    break  # why?
                else:
                    log_write_error('missing handling of unexpected case min_occurs = ' +
                                    f'{part.min_occurs}: {part.name}')

            element.particles_next_grammar_ids[particle_index] = self.grammar_id

        previous_choice_list = []
        for particle_index, particle in enumerate(element.particles):
            choice_list = self._get_choice_options(element, particle)
            if choice_list and choice_list[1] == previous_choice_list:
                # skip if particle in same choice group as a previously processed one
                element.particles_next_grammar_ids[particle_index] = self.grammar_id
                continue
            else:
                previous_choice_list.clear()
                if choice_list:
                    previous_choice_list.extend(choice_list[1])

            _add_subsequent_grammar_details(element, particle, grammar, particle_index,
                                            index_last_nonoptional_particle, particle_is_part_of_sequence)
            grammar = self.create_empty_grammar()

    def generate_event_info(self, grammars: List[ElementGrammar], element: ElementData):
        len_grammars = len(grammars)
        # if there are just ERROR or END/ERROR in the list, the element is ignored
        if len_grammars <= 2:
            return

        for idx_grammar, grammar in enumerate(grammars):
            len_details = grammar.details_count
            if len_details == 0:
                log_write_error(f'ERROR! Empty item list. Grammar {grammar.grammar_id}')
                continue

            # case 1: just one element, START
            if len_details == 1 and grammar.details[0].flag == GrammarFlag.START:
                grammar.details[0].event_index = 0
                grammar.details[0].next_grammar = grammars[idx_grammar + 1].grammar_id
                self.log(', '.join([
                                 f'Grammar ID={grammar.grammar_id}',
                                 f'eventCode={grammar.details[0].event_index}',
                                 f'decode={grammar.details[0].particle.typename} ' +
                                 f"(Particle '{grammar.details[0].particle.name}')",
                                 f'next ID={grammar.details[0].next_grammar}',
                            ]))
            else:
                end_elem_detail_index = -1
                event_code = 0
                grammar_detail: ElementGrammarDetail  # type hint
                for grammar_detail_index, grammar_detail in enumerate(grammar.details):
                    if grammar_detail.flag == GrammarFlag.END:
                        end_elem_detail_index = grammar_detail_index
                        continue

                    if grammar_detail.flag == GrammarFlag.START:
                        grammar_detail.event_index = event_code

                        if grammar_detail_index < len_details:
                            if end_elem_detail_index >= 0 and len_details == 2:
                                grammar_detail.next_grammar = grammars[idx_grammar + 1].grammar_id
                            else:
                                # find the particle's index in the element
                                part_index: int = None
                                for part_index, part in enumerate(element.particles):
                                    if grammar_detail.particle == part:
                                        break

                                if part_index is not None:
                                    def _is_final_particle(element: ElementData, pindex: int) -> bool:
                                        # particle is the last one, or is in the same choice group as the last one
                                        if pindex == len(element.particles) - 1:
                                            return True
                                        choice_group = self._get_choice_options(element, element.particles[-1])
                                        if choice_group and choice_group[0]:
                                            if element.particles[pindex] in choice_group[0]:
                                                return True
                                        return False

                                    if _is_final_particle(element, part_index):
                                        # next grammar is always END for the final particle
                                        grammar_detail.next_grammar = grammars[-2].grammar_id
                                    else:
                                        grammar_detail.next_grammar = element.particles_next_grammar_ids[part_index]
                                else:
                                    log_write_error("Failed to find element particle for " +
                                                    f"{grammar_detail.particle.name}")

                        ptname = grammar_detail.particle.typename if grammar_detail.particle is not None else '(None)'
                        pname = grammar_detail.particle.name if grammar_detail.particle is not None else ''
                        self.log(', '.join([
                                         f'Grammar ID={grammar.grammar_id}',
                                         f'eventCode={grammar_detail.event_index}',
                                         f'decode={ptname} ' +
                                         f"(Particle '{pname}')",
                                         f'next ID={grammar_detail.next_grammar}',
                                    ]))
                        event_code += 1

                        if grammar_detail.next_grammar == -1:
                            # this is never reached
                            grammar_detail.next_grammar = element.particles_next_grammar_ids[idx_grammar]
                            log_write_error("Fallback: Failed to find element particle for " +
                                            f"{grammar_detail.particle.name}, next ID={grammar_detail.next_grammar}")
                    else:
                        # the END element gets ERROR as next grammar
                        grammar_detail.next_grammar = grammars[len_grammars - 1].grammar_id

                if end_elem_detail_index >= 0:
                    grammar.details[end_elem_detail_index].event_index = event_code
                    grammar.details[end_elem_detail_index].next_grammar = grammars[len_grammars - 1].grammar_id
                    self.log(', '.join([
                                     f'Grammar ID={grammar.grammar_id}',
                                     f'eventCode={grammar.details[end_elem_detail_index].event_index}',
                                     GrammarFlag.END,
                                     f'next ID={grammar.details[end_elem_detail_index].next_grammar}',
                                 ]))

    # ---------------------------------------------------------------------------
    # general generator functions
    # ---------------------------------------------------------------------------
    def generate_file(self):
        log_write_error('The function generate_file() is not implemented in subclass.')
        raise NotImplementedError
