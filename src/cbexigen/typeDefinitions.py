# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 chargebyte GmbH
# Copyright (c) 2022 - 2023 Contributors to EVerest

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class AnalyzerData:
    schema_identifier: str = ''
    root_elements: list = field(default_factory=list)
    generate_elements: list = field(default_factory=list)
    generate_elements_types: dict = field(default_factory=dict)

    known_elements: dict = field(default_factory=dict)
    known_particles: dict = field(default_factory=dict)
    known_enums: dict = field(default_factory=dict)
    known_prototypes: dict = field(default_factory=dict)
    known_fragments: dict = field(default_factory=dict)

    max_occurs_changed: dict = field(default_factory=dict)
    namespace_elements: dict = field(default_factory=dict)
    schema_builtin_types: dict = field(default_factory=dict)

    add_debug_code_enabled: int = 0
    debug_code_current_message_id: int = 1
    debug_code_messages: dict = field(default_factory=dict)


@dataclass
class FragmentData:
    name: str = ''
    namespace: str = ''
    type: str = ''
    is_complex: bool = False


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
