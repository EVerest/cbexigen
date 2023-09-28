# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 chargebyte GmbH
# Copyright (c) 2022 - 2023 Contributors to EVerest

import copy
from typing import List
from cbexigen import tools_generator, tools
from cbexigen.elementData import Particle, ElementData, Choice
from cbexigen.elementGrammar import GrammarFlag, ElementGrammar, ElementGrammarDetail
from cbexigen.tools_config import CONFIG_PARAMS
from cbexigen.tools_logging import (
    log_write,
    log_write_error,
    log_init_logger,
    log_write_logger,
    log_deinit_logger,
    log_exists_logger,
)

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

    @staticmethod
    def _get_choice_sequence(element: ElementData, particle: Particle) -> []:
        """
        Return an ordered list of all particles belonging to the same choice sequence as
        the given particle.
        """
        if particle.parent_has_choice_sequence:
            for choice_obj in element.choices:
                choice_sequence = choice_obj.choice_sequences[particle.parent_choice_sequence_number - 1]
                for choice_item in choice_sequence:
                    if particle.name == choice_item[0]:  # first element is name, second element is index
                        li: list[Particle] = [element.particle_from_name(x[0]) for x in choice_sequence]
                        return li
            log_write_error(f"failed to find choice sequence for of {particle.name}")

        # particle is not in a choice sequence, or fallback on failure to find
        return []

    class ChoiceOptions:
        """
        create:
        - an ordered list of all particles (proper or abstract) belonging to the same choice
            group as the given particle.
        - a list of the choice group item names (for comparison)
        - the min_occurs of this particle group
        - the max_occurs of this particle group
        """
        def __init__(self, element: ElementData, particle: Particle) -> None:
            self._parent_choice_sequence_number = -1
            self._is_last_particle_in_choice_sequence = False
            self._is_followed_by_mandatory_particles_in_choice_sequence = False
            self._particles_to_skip_in_same_choice_seq = 0

            self.particles: list[Particle] = []
            self.item_names = []
            self.min_occurs = -1
            self.max_occurs = -1
            self.choice_sequences = []
            # in which of the choices is this particle contained
            self.choice_index = -1
            self.choice: Choice = None

            if element.has_choice:
                element_choice: Choice

                if particle.parent_has_choice_sequence:
                    self._parent_choice_sequence_number = particle.parent_choice_sequence_number
                    for element_choice_index, element_choice in enumerate(element.choices):
                        if element_choice.choice_sequence_count < self._parent_choice_sequence_number:
                            continue
                        # this choice has sufficient sequences
                        if particle.name in [x[0] for x in element_choice.choice_sequences[self._parent_choice_sequence_number - 1]]:
                            # we actually are in the given choice sequence
                            self.choice = element_choice
                            self.choice_sequences = element_choice.choice_sequences
                            choice_sequence = element_choice.choice_sequences[self._parent_choice_sequence_number - 1]
                            # find our index within this choice sequence
                            part_choice_sequence_index = -1
                            for i, part in enumerate(choice_sequence):
                                if particle.name == part[0]:
                                    part_choice_sequence_index = i
                                    break
                            if part_choice_sequence_index == -1:
                                log_write_error(f"Failed to find particle '{particle.name}' in its own choice sequence")
                            if part_choice_sequence_index == 0:
                                # remember in which of the choices this sequence was found
                                self.choice_index = element_choice_index
                                # if this particle is the first in a choice sequence, it's a choice
                                # so the first particles from all sequences are the choice
                                for choice_sequence in element_choice.choice_sequences:
                                    self.particles.append(element.particle_from_name(choice_sequence[0][0]))
                                    self.item_names.append(choice_sequence[0][0])
                                self.min_occurs = element_choice.min_occurs
                                self.max_occurs = element_choice.multi_choice_max
                            else:
                                self.min_occurs = particle.min_occurs
                                self.max_occurs = particle.max_occurs

                            is_counting = False
                            particles_in_same_choice_seq = \
                                [x for x in element.particles
                                 if x.parent_choice_sequence_number == self._parent_choice_sequence_number]
                            for part in particles_in_same_choice_seq:
                                if particle.min_occurs >= 1:
                                    self._is_followed_by_mandatory_particles_in_choice_sequence = True
                                    break
                                if part == particle:
                                    is_counting = True
                                    continue
                                if not is_counting:
                                    continue
                                # if part.name in the choice sequence and part index > particle index
                                # first, find myself in sequence, THEN count the ones after
                                if part.min_occurs_old == 0 or part.min_occurs == 0:
                                    self._particles_to_skip_in_same_choice_seq += 1
                                else:
                                    self._particles_to_skip_in_same_choice_seq = 0
                                    break

                            if part_choice_sequence_index == len(choice_sequence) - 1:
                                self._is_last_particle_in_choice_sequence = True

                            break
                    return

                for element_choice_index, element_choice in enumerate(element.choices):  # choice object from list of choice objects
                    if element_choice.choice_sequence_count:
                        log_write_error("FIXME evaluate choice of sequences:")
                        log_write_error(element_choice.choice_sequences)
                        for sequence_index, sequence_item in enumerate(element_choice.choice_sequences):
                            # the choice initially consists of the first elements of the sequences
                            if len(sequence_item) < 1:
                                log_write_error(f"choice of sequences: sequence {sequence_index} is empty")
                            else:
                                self.particles.append(element.particle_from_name(sequence_item[0][0]))
                                self.item_names.append(sequence_item[0][0])
                            log_write_error(self.item_names)
                        self.min_occurs = element_choice.min_occurs
                        self.max_occurs = element_choice.multi_choice_max
                        return  # FIXME choice occurrences

                    for choice_item in element_choice.choice_items:  # list of choice names from choice object
                        if particle.name == choice_item[0]:
                            self.particles = [element.particle_from_name(x[0]) for x in element_choice.choice_items]
                            self.item_names = element_choice.choice_items
                            self.min_occurs = element_choice.min_occurs
                            self.max_occurs = element_choice.multi_choice_max
                            self.choice_index = element_choice_index
                            self.choice = element_choice
                            return
            elif element.has_abstract_sequence:
                for abstract_choice_list, _min_occurs, _max_occurs in element.abstract_sequences:
                    for choice_item in abstract_choice_list:
                        if particle.name == choice_item:
                            self.particles = [element.particle_from_name(x) for x in abstract_choice_list]
                            self.item_names = abstract_choice_list
                            self.min_occurs = _min_occurs
                            self.max_occurs = _max_occurs
                            return
            # particle is not a choice, or fallback on failure to find
            # return

        @property
        def number_of_particles_to_skip(self) -> int:
            # return the number of particles in the subsequent parallel choice sequences,
            # which need to be skipped when ignoring parallel sequences (which are aligned
            # linearly)
            # or
            # if not the last particle in the choice sequence and the remaining are optional,
            # the number of particles until the end of the choice
            if not self.choice or not self.choice.choice_sequence_count:
                return 0
            if not self._is_last_particle_in_choice_sequence:
                return 0
            # PGPKeyPacket occurrence in the first of two sequences must not return > 0
            # FIXME obsolete?
            if self._is_followed_by_mandatory_particles_in_choice_sequence:
                return 0

            result = self._particles_to_skip_in_same_choice_seq
            # note: sequence_index is 1-based, not 0-based
            # add the number of particles in the parallel choice sequences
            for seq in self.choice.choice_sequences[self._parent_choice_sequence_number:]:
                result += len(seq)
            return result

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

        # find the last mandatory particle's index
        index_last_nonoptional_particle = -1
        particle: Particle  # type hint
        for particle_index, particle in enumerate(element.particles):
            # FIXME this could be done backwards with a "break"
            choice_options = self.ChoiceOptions(element, particle)
            combined_min_occurs_from_choice = \
                choice_options.min_occurs if choice_options.particles else particle.min_occurs
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

        def _debug_element_particle_properties(element: ElementData):
            particle: Particle
            for particle in element.particles:
                log_write(f"Investigating particle '{particle.name}'")
                log_write(f"\tmin_occurs: {particle.min_occurs}")
                log_write(f"\tmax_occurs: {particle.max_occurs}")
                if particle.min_occurs_old != -1 and not particle.parent_has_sequence:
                    log_write(f"\tpeculiar: min_occurs_old: {particle.min_occurs_old}")
                if particle.max_occurs_old != -1 and not particle.parent_has_sequence:
                    log_write(f"\tpeculiar: max_occurs_old: {particle.max_occurs_old}")
                if _particle_is_in_choice(element, particle):
                    choice_options = self.ChoiceOptions(element, particle)
                    log_write(f"\tis in a choice group, min_occurs = {choice_options.min_occurs}, " +
                              f"max_occurs = {choice_options.max_occurs}")
                    log_write([x.name if x is not None else '' for x in choice_options.particles])
                if _particle_is_in_abstract_choice(element, particle):
                    choice_options = self.ChoiceOptions(element, particle)
                    log_write(f"\tis in an abstract choice group, min_occurs = {choice_options.min_occurs}, " +
                              f"max_occurs = {choice_options.max_occurs}")
                    log_write([x.name if x is not None else '' for x in choice_options.particles])
                if particle.parent_has_sequence:
                    log_write("\tis in a sequence")
                    log_write(f"\tmin_occurs_old: {particle.min_occurs_old}")
                    log_write(f"\tmax_occurs_old: {particle.max_occurs_old}")
                if particle.parent_has_choice_sequence:
                    log_write("\tis in a sequence which is choice, " +
                              f"number {particle.parent_choice_sequence_number}:")
                    log_write("\t\t" + repr([x.name if x is not None else '' for x in self._get_choice_sequence(element, particle)]))
                    choice_options = self.ChoiceOptions(element, particle)
                    num_part_to_skip = choice_options.number_of_particles_to_skip
                    if num_part_to_skip:
                        log_write(f"\tparticles to skip: {choice_options.number_of_particles_to_skip}")
                    if choice_options.particles:
                        log_write("\tis in a resulting choice, " +
                                  f"{choice_options.item_names}")

        # _debug_element_particle_properties(element)

        grammar = self.create_empty_grammar()

        def _add_subsequent_grammar_details(element: ElementData, particle: Particle,
                                            particle_index: int, index_last_nonoptional_particle: int,
                                            particle_is_part_of_sequence: bool,
                                            is_recursion: bool = False):
            # we push the grammar to a list below, and assign a new object to this variable;
            # this assignment does not apply globally if the grammar is passed in
            nonlocal grammar
            choice_options = self.ChoiceOptions(element, particle)
            if particle_index + choice_options.number_of_particles_to_skip > index_last_nonoptional_particle:
                # all the following particles are optional, so END needs to be an expected event
                # at the beginning of the event/grammar detail list
                if not particle_is_part_of_sequence:
                    grammar.details.append(ElementGrammarDetail(flag=GrammarFlag.END))
                else:
                    if str(particle.parent_sequence[0]) == particle.name:
                        grammar.details.append(ElementGrammarDetail(flag=GrammarFlag.END))

            def _add_particle_or_choice_list_to_details(
                    element: ElementData, grammar: ElementGrammar, particle: Particle, previous_choice_list,
                    flag=GrammarFlag.START,
                    is_in_array_last=False, is_in_array_not_last=False, is_extra_grammar=False):
                """
                If a particle is part of a choice group, this adds all the group's particles
                to the grammar at once, and remembers which group was being handled, so that
                the subsequent particles aren't added again.

                Otherwise, it just adds the particle.
                """
                choice_options = self.ChoiceOptions(element, particle)
                if choice_options.particles and not (choice_options.choice_sequences and particle.parent_choice_sequence_number > 1):
                    if choice_options.item_names != previous_choice_list:
                        for choice in choice_options.particles:
                            grammar.details.append(ElementGrammarDetail(flag=flag, particle=choice,
                                                                        is_in_array_last=is_in_array_last,
                                                                        is_in_array_not_last=is_in_array_not_last,
                                                                        is_extra_grammar=is_extra_grammar))
                        previous_choice_list.extend(choice_options.item_names)
                else:
                    grammar.details.append(ElementGrammarDetail(flag=flag, particle=part,
                                                                is_in_array_last=is_in_array_last,
                                                                is_in_array_not_last=is_in_array_not_last,
                                                                is_extra_grammar=is_extra_grammar))
                    previous_choice_list.clear()

            previous_choice_list = []  # to check whether this choice has already been handled

            # for the current particle, check all successors in the particle list
            part: Particle
            n_to_skip = set()
            for n, part in enumerate(element.particles[particle_index:], start=particle_index):
                if n in n_to_skip:
                    # a list of particles in the linear list not to be considered
                    continue
                if part.max_occurs == 1 and not part.max_occurs_changed:
                    if part.parent_has_sequence:
                        particle_is_part_of_sequence = True

                    if not particle_is_part_of_sequence or n == particle_index:
                        _add_particle_or_choice_list_to_details(element, grammar, part, previous_choice_list)

                        if n < len(element.particles) - 1:
                            if not element.particles[n + 1].parent_has_sequence:
                                particle_is_part_of_sequence = False

                                if part.min_occurs_old == 1:
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

                    # non-optional or last particle in element: end of grammar list
                    choice_options = self.ChoiceOptions(element, part)
                    part_min = choice_options.min_occurs if choice_options.particles else 0
                    if part.min_occurs == 1 or part_min == 1 or (n == len(element.particles) - 1):
                        if not is_recursion:
                            # end of grammar for current particle
                            self.append_to_element_grammars(grammar, element.typename)
                            grammar = self.create_empty_grammar()
                        break
                    if part.parent_has_choice_sequence:
                        if n == len(element.particles) - 1 - choice_options.number_of_particles_to_skip:
                            grammar.details.append(ElementGrammarDetail(flag=GrammarFlag.END))
                            if not is_recursion:
                                # end of grammar for current particle
                                self.append_to_element_grammars(grammar, element.typename)
                                grammar = self.create_empty_grammar()
                            break
                        for i in range(choice_options.number_of_particles_to_skip):
                            n_to_skip.add(n+1+i)
                            log_write_error(f"Skipping subsequent particles {n_to_skip} for particle '{part.name}'")
                elif part.max_occurs > 1 or part.max_occurs_changed:
                    if part.max_occurs < 25:
                        _max = part.max_occurs
                        # if max_occurs was reduced, make sure to create the proper grammar after the one occurence
                        # This should be done only if the caller is not the encoder
                        add_extra = False
                        if part.max_occurs >= 1 and part.max_occurs_changed:
                            _max += 1
                            add_extra = True

                        for m in range(1, _max + 1):
                            if m < _max:
                                _add_particle_or_choice_list_to_details(element, grammar, part, previous_choice_list,
                                                                        is_in_array_not_last=True)
                            else:
                                _add_particle_or_choice_list_to_details(element, grammar, part, previous_choice_list,
                                                                        is_in_array_last=True,
                                                                        is_extra_grammar=add_extra)
                            if m > part.min_occurs and m > 1:
                                # this is an optional occurrence (and grammar 0 already contains END),
                                # so recurse with the subsequent particles
                                _add_subsequent_grammar_details(element, particle, n + 1,
                                                                index_last_nonoptional_particle,
                                                                particle_is_part_of_sequence,
                                                                is_recursion=True)

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
            choice_options = self.ChoiceOptions(element, particle)
            if choice_options.particles and choice_options.item_names == previous_choice_list:
                # skip if particle in same choice group as a previously processed one
                element.particles_next_grammar_ids[particle_index] = self.grammar_id
                continue
            else:
                previous_choice_list.clear()
                if choice_options.particles:
                    previous_choice_list.extend(choice_options.item_names)

            _add_subsequent_grammar_details(element, particle, particle_index,
                                            index_last_nonoptional_particle, particle_is_part_of_sequence)
            grammar = self.create_empty_grammar()

        # at this point, the grammar detail lists for this element's grammars are complete

        grammar: ElementGrammar
        # reorder: ANY as last real particle(s)
        for grammar in self.element_grammars:
            self.__expand_any_grammar(grammar)

    def __expand_any_grammar(self, grammar):
        # take the list of grammars details
        # for every 'ANY' particle detail (there can theoretically be multiple):
        #    move it to the end, instead of alphabetically
        #    add an extra grammar detail after the 'END' detail (needs to be countable)
        #
        # FIXME: make the appended 'ANY' detail a special pseudo detail (different handling)
        sorted_element_grammar_details: list[ElementGrammarDetail] = []
        any_type_details: list[ElementGrammarDetail] = []
        end_details: list[ElementGrammarDetail] = []
        grammar_detail: ElementGrammarDetail
        for grammar_detail in grammar.details:
            if grammar_detail.flag == GrammarFlag.END:
                end_details.append(grammar_detail)
            elif grammar_detail.is_any:
                any_type_details.append(grammar_detail)
            else:
                sorted_element_grammar_details.append(grammar_detail)
        if end_details:
            # generic/dummy ANYs first, then END, then implemented string/binary ANYs
            sorted_element_grammar_details.extend(any_type_details)
            sorted_element_grammar_details.extend(end_details)
            # sorted_element_grammar_details.extend(any_type_details)
            for any_detail in any_type_details:
                # create new property for duplicated events
                # TBD any_detail.property = foo
                final_any_detail: ElementGrammarDetail = copy.copy(any_detail)
                final_any_detail.any_is_dummy = False
                sorted_element_grammar_details.append(final_any_detail)
        else:
            # assumption: without an END, only the implemented string/binary ANYs get event codes
            # (no such case within V2G, cannot be confirmed, needs to be checked in EXI standard)
            for any_detail in any_type_details:
                any_detail.any_is_dummy = False
            sorted_element_grammar_details.extend(any_type_details)

        # overwrite the original list
        grammar.details = sorted_element_grammar_details

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

            # case 1: just one element, START as singular grammar detail
            if len_details == 1 and grammar.details[0].flag == GrammarFlag.START:
                grammar.details[0].event_index = 0
                # the next grammar must be that of the subsequent particle
                grammar.details[0].next_grammar = grammars[idx_grammar + 1].grammar_id
                self.log(', '.join([
                                 f'Grammar ID={grammar.grammar_id}',
                                 f'eventCode={grammar.details[0].event_index}',
                                 f'decode={grammar.details[0].particle.typename} ' +
                                 f"(Particle '{grammar.details[0].particle.name}'" +
                                 (" (attribute)" if grammar.details[0].particle.is_attribute else "") + ")",
                                 f'next ID={grammar.details[0].next_grammar}',
                            ]))
            else:
                end_elem_detail_index = -1
                event_code = 0
                grammar_detail: ElementGrammarDetail  # type hint
                # first, find the index of the END grammar (used below)
                for grammar_detail_index, grammar_detail in enumerate(grammar.details):
                    if grammar_detail.flag == GrammarFlag.END:
                        end_elem_detail_index = grammar_detail_index
                        break

                for grammar_detail_index, grammar_detail in enumerate(grammar.details):
                    grammar_detail.event_index = grammar_detail_index

                    if grammar_detail.flag == GrammarFlag.END:
                        # the next grammar is the ERROR grammar
                        grammar_detail.next_grammar = self.grammar_unknown
                        self.log(', '.join([
                                        f'Grammar ID={grammar.grammar_id}',
                                        f'eventCode={grammar_detail.event_index}',
                                        GrammarFlag.END,
                                        f'next ID={grammar_detail.next_grammar}',
                                    ]))

                    elif grammar_detail.flag == GrammarFlag.START:
                        # find the particle's index in the element
                        # FIXME can this break on repeated occurrences, as in PGPKeyDataType?
                        part_index: int = None
                        part: Particle
                        for part_index, part in enumerate(element.particles):
                            if grammar_detail.particle == part:
                                break

                        def _is_final_particle(element: ElementData, pindex: int) -> bool:
                            # particle is the last one, or is in the same choice group as the last one
                            if grammar_detail.is_in_array_not_last:
                                return False
                            if pindex == len(element.particles) - 1:
                                return True
                            choice_options = self.ChoiceOptions(element, element.particles[-1])
                            if choice_options.particles:
                                if element.particles[pindex] in choice_options.particles:
                                    return True
                            if choice_options.choice_sequences:
                                if pindex == len(element.particles) - 1 - choice_options.number_of_particles_to_skip:
                                    return True
                            return False

                        if end_elem_detail_index >= 0 and len_details == 2:
                            if grammar_detail.is_in_array_last:
                                if _is_final_particle(element, part_index):
                                    grammar_detail.next_grammar = self.grammar_end_element
                                else:
                                    grammar_detail.next_grammar = element.particles_next_grammar_ids[part_index]
                            else:
                                grammar_detail.next_grammar = grammars[idx_grammar + 1].grammar_id
                        else:
                            if part_index is not None:
                                if _is_final_particle(element, part_index):
                                    # next grammar is always END for the final particle
                                    grammar_detail.next_grammar = self.grammar_end_element
                                else:
                                    if grammar_detail.is_in_array_not_last:
                                        grammar_detail.next_grammar = grammars[idx_grammar + 1].grammar_id
                                    elif grammar_detail.is_in_array_last:
                                        grammar_detail.next_grammar = grammars[idx_grammar + 1].grammar_id
                                    else:
                                        grammar_detail.next_grammar = element.particles_next_grammar_ids[part_index]
                            else:
                                log_write_error("Failed to find element particle for " +
                                                f"{grammar_detail.particle.name}")

                        ptname = grammar_detail.particle.typename if grammar_detail.particle is not None else '(None)'
                        self.log(', '.join([
                                         f'Grammar ID={grammar.grammar_id}',
                                         f'eventCode={grammar_detail.event_index}',
                                         f'decode={ptname} ' +
                                         f"(Particle '{grammar_detail.particle_name}'" +
                                         (" (attribute)" if grammar_detail.particle.is_attribute else "") + ")",
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

    # ---------------------------------------------------------------------------
    # general generator functions
    # ---------------------------------------------------------------------------
    def generate_file(self):
        log_write_error('The function generate_file() is not implemented in subclass.')
        raise NotImplementedError
