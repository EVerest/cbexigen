# SPDX-License-Identifier: Apache-2.0
"""Generate the schema-independent common runtime for tests."""
import os

from config import *

output_dir = os.path.join(os.environ['CBEXIGEN_TEST_OUT'], 'c')
log_dir = os.path.join(os.environ['CBEXIGEN_TEST_OUT'], 'log')
c_files_to_generate = {
    name: entry for name, entry in c_files_to_generate.items()
    if entry['folder'] == 'common'
}
