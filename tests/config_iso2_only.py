# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2026 chargebyte GmbH
# Copyright (c) 2022 - 2026 Contributors to EVerest

"""Generator config for the element fragment grammar test.

Same as the default config, restricted to ISO 15118-2 and its common runtime.
DIN 70121 is dropped because its schemas cannot be downloaded, and ISO 15118-20
is dropped because it has no ambiguous element and only costs run time here.
Output and log directories come from CBEXIGEN_TEST_OUT so the test can generate
into a scratch directory instead of the source tree. CBEXIGEN_TEST_DROP_FRAGMENTS,
a comma separated list, removes those names from iso2_fragments.
"""
import os

from config import *  # noqa: F401,F403

_out = os.environ['CBEXIGEN_TEST_OUT']
output_dir = os.path.join(_out, 'c')
log_dir = os.path.join(_out, 'log')

c_files_to_generate = {
    key: value
    for key, value in c_files_to_generate.items()  # noqa: F405
    if not key.startswith('din') and not key.startswith('iso20')
}

_drop = [name for name in os.environ.get('CBEXIGEN_TEST_DROP_FRAGMENTS', '').split(',') if name]
iso2_fragments = [name for name in iso2_fragments if name not in _drop]  # noqa: F405
