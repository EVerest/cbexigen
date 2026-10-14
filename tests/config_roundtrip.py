# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2026 chargebyte GmbH
# Copyright (c) 2022 - 2026 Contributors to EVerest

"""Generator config for the round trip tests built on exi_roundtrip.py.

Same as the default config, restricted to the common runtime and the codec
files whose names start with CBEXIGEN_TEST_CODEC, so a test only needs the
schemas of its own codec. Output and log directories come from
CBEXIGEN_TEST_OUT so the test can generate into a scratch directory instead
of the source tree.
"""
import os

import config as _base
from config import *  # noqa: F401,F403

_out = os.environ['CBEXIGEN_TEST_OUT']
output_dir = os.path.join(_out, 'c')
log_dir = os.path.join(_out, 'log')

c_files_to_generate = {
    key: value
    for key, value in _base.c_files_to_generate.items()
    if key.startswith(('exi_', os.environ['CBEXIGEN_TEST_CODEC']))
}
