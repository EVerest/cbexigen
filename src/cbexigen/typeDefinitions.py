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

    add_debug_code_enabled = 0
    debug_code_current_message_id = 1
    debug_code_messages = {}


@dataclass
class FragmentData:
    name = ''
    namespace = ''
    type = ''


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
