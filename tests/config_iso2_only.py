# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2026 chargebyte GmbH
# Copyright (c) 2022 - 2026 Contributors to EVerest

"""Generator config for the element fragment grammar test.

Same as the default config, restricted to ISO 15118-2 and its common runtime.
DIN 70121 is dropped because its schemas cannot be downloaded, and ISO 15118-20
is dropped because it has no ambiguous element and only costs run time here.
Output and log directories come from CBEXIGEN_TEST_OUT so the test can generate
into a scratch directory instead of the source tree.
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
