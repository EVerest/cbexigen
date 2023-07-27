# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 chargebyte GmbH
# Copyright (c) 2022 - 2023 Contributors to EVerest

from dataclasses import dataclass
from cbexigen.elementData import Particle


class GrammarFlag:
    START = 'START'
    LOOP = 'LOOP'
    END = 'END Element'
    ERROR = 'ERROR Element'


@dataclass
class ElementGrammarDetail:
    flag: str = None
    particle: Particle = None
    array_index: int = -1
    event_index: int = -1
    next_grammar: int = -1

    @property
    def is_optional(self):
        if self.particle is None:
            return False

        return self.particle.min_occurs == 0 and self.particle.max_occurs == 1

    @property
    def is_optional_array(self):
        if self.particle is None:
            return False

        return self.particle.min_occurs == 0 and self.particle.max_occurs > 1

    @property
    def is_mandatory(self):
        if self.particle is None:
            return False

        return self.particle.min_occurs == 1 and self.particle.max_occurs == 1

    @property
    def is_mandatory_array(self):
        if self.particle is None:
            return False

        return self.particle.min_occurs >= 1 and self.particle.max_occurs > 1

    @property
    def is_any(self):
        return self.particle is not None and self.particle.is_any


@dataclass
class ElementGrammar:
    grammar_id: int = -1
    # details: list[ElementGrammarDetail] = field(default_factory=list[ElementGrammarDetail])
    details = []
    element_typename: str = ''

    # TODO: refactor bits_to_read and bits_to_write to just one function with suitable name

    @property
    def bits_to_read(self):
        result = 0
        if self.details_count == 0 or self.details_count > 255:
            return result

        for detail in self.details:
            if detail.flag == GrammarFlag.ERROR:
                return result

        total = self.details_count + 1

        if total <= 2:
            result = 1
        elif total <= 4:
            result = 2
        elif total <= 8:
            result = 3
        elif total <= 16:
            result = 4
        elif total <= 32:
            result = 5
        elif total <= 64:
            result = 6
        elif total <= 128:
            result = 7
        elif total <= 256:
            result = 8

        return result

    @property
    def bits_to_write(self):
        return self.bits_to_read

    @property
    def details_count(self):
        return len(self.details)

    @property
    def grammar_comment(self):
        comment = f'// Grammar: ID={self.grammar_id}; read/write bits={self.bits_to_read}; '
        detail_list = []
        detail: ElementGrammarDetail = None  # type hint
        for detail in self.details:
            detail_list.append(f'{detail.flag} ({detail.particle.name})'
                               if detail.particle is not None else f'{detail.flag}')

        comment += ', '.join(detail_list)

        return comment
