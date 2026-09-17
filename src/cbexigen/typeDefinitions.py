# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 chargebyte GmbH
# Copyright (c) 2022 - 2023 Contributors to EVerest

from dataclasses import dataclass
from typing import Dict


@dataclass
class AnalyzerData:
    schema_identifier = ''
    root_elements = []
    generate_elements = []
    generate_elements_types = {}

    known_elements = {}
    known_particles = {}
    known_enums = {}
    known_prototypes = {}
    known_fragments = {}

    max_occurs_changed = {}
    namespace_elements = {}
    schema_builtin_types = {}
    element_fragment_grammar = None

    add_debug_code_enabled = 0
    debug_code_current_message_id = 1
    debug_code_messages = {}


@dataclass
class FragmentData:
    name = ''
    namespace = ''
    type = ''


@dataclass
class ElementFragmentAttribute:
    """One AT production of an element fragment grammar."""
    name = ''
    qname = ''
    event_code = 0
    define = ''


@dataclass
class ElementFragmentType:
    """An element that must be coded with the element fragment grammar.

    EXI 1.0, 8.5.3: an element whose qname is declared more than once, and
    whose declarations do not all share one type name and {nillable} value,
    cannot be resolved to a single type grammar inside a fragment. Its content
    is coded with the relaxed element fragment grammar instead.
    """
    name = ''
    namespace = ''
    type = ''
    declared_types = []
    attributes = []
    has_characters = False
    content_define = ''


@dataclass
class ElementFragmentGrammar:
    """EXI 1.0, 8.5.3 Schema-informed Element Fragment Grammar.

    n is the number of unique attribute qnames in the schema, m the number of
    unique element qnames, both sorted first by local-name then by uri.

    ElementFragment_0:  AT(A_0..A_n-1) 0..n-1, AT(*) n,
                        SE(F_0..F_m-1) n+1..n+m, SE(*) n+m+1,
                        EE n+m+2, CH n+m+3
    ElementFragment_1:  SE(F_0..F_m-1) 0..m-1, SE(*) m, EE m+1, CH m+2
    """
    attribute_qnames = []
    element_count = 0
    types = {}

    @property
    def attribute_count(self):
        return len(self.attribute_qnames)

    @property
    def first_characters_code(self):
        return self.attribute_count + self.element_count + 3

    @property
    def first_end_element_code(self):
        return self.attribute_count + self.element_count + 2

    @property
    def content_characters_code(self):
        return self.element_count + 2

    @property
    def content_end_element_code(self):
        return self.element_count + 1


# Note: a corrected limit of 1 is default for all unbounded types, unless
#       listed differently here
OCCURRENCE_LIMITS_CORRECTED: Dict[str, int] = {
    "X509IssuerSerial": 1,
    "X509SKI": 1,
    "X509SubjectName": 1,
    "X509Certificate": 1,
    "X509CRL": 1,
    "XPath": 1,
    "SPKISexp": 1,
    "RootCertificateID": 5,
    "Transform": 1,
    "SignatureProperty": 1,
    "Reference": 4,
    "PMaxScheduleEntry": 5,
    "KeyName": 1,
    "KeyValue": 1,
    "RetrievalMethod": 1,
    "X509Data": 1,
    "PGPData": 1,
    "SPKIData": 1,
    "MgmtData": 1,
    "SalesTariffEntry": 5,
    "Object": 1,
    "ParameterSet": 5,
    "PaymentOption": 2,  # DIN schema uses unbounded, but restricts it to 2 [V2G-DC-634]
    "ProfileEntry": 24,  # DIN schema uses unbounded, but restricts it to 24 [V2G-DC-307]
    "SelectedService": 16,  # DIN schema uses unbounded, but restricts it to 1 [V2G-DC-635], ISO-2 uses 16
    "SAScheduleTuple": 5,  # DIN schema uses unbounded, but restricts it to 5
}
