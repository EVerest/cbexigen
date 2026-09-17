# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2026 chargebyte GmbH
# Copyright (c) 2022 - 2026 Contributors to EVerest

"""End to end check of the ISO 15118-2 eMAID element fragment encoding.

Generates the ISO 15118-2 codec, compiles it together with a small driver and
compares the encoded eMAID fragment against vectors produced by Exificient.

eMAID is the only element in the ISO 15118-2 schema set whose qname is bound
to more than one type, so per EXI 1.0 section 8.5.3 it is the only element that
has to be coded with the schema-informed element fragment grammar rather than
with its own type grammar.

Needs the ISO 15118-2 schemas under src/input/schemas; fetch them once with
    python src/main.py --auto-download-public-xsd 1
The test skips, rather than fails, when they are absent or when no C compiler
is available.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / 'src'
SCHEMA = SRC / 'input' / 'schemas' / 'ISO_15118-2' / 'FDIS' / 'V2G_CI_MsgDef.xsd'
VECTORS = Path(__file__).resolve().parent / 'vectors' / 'emaid_iso2.txt'
DRIVER = Path(__file__).resolve().parent / 'emaid_fragment_driver.c'
CONFIG = Path(__file__).resolve().parent / 'config_iso2_only.py'


def read_vectors():
    vectors = []
    for line in VECTORS.read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        identifier, value, expected = line.split('\t')
        vectors.append((identifier, value, expected))
    return vectors


def generate(out_dir):
    """Run the generator into out_dir and return the generated code root."""
    # tools_config imports the config by module name, so it has to sit next to
    # the other modules on sys.path[0], which is src/ when main.py runs.
    staged = SRC / CONFIG.name
    shutil.copyfile(CONFIG, staged)
    try:
        env = dict(os.environ, CBEXIGEN_TEST_OUT=str(out_dir))
        result = subprocess.run(
            [sys.executable, str(SRC / 'main.py'), '--config_file', CONFIG.name],
            cwd=str(REPO), env=env, capture_output=True, text=True)
        if result.returncode != 0:
            raise AssertionError(
                f'generator failed ({result.returncode})\n'
                f'{result.stdout[-4000:]}\n{result.stderr[-4000:]}')
    finally:
        staged.unlink(missing_ok=True)
    return Path(out_dir) / 'c'


def compile_driver(code_root, out_dir):
    compiler = os.environ.get('CC') or shutil.which('cc') or shutil.which('gcc')
    if compiler is None:
        raise unittest.SkipTest('no C compiler found')
    binary = Path(out_dir) / 'emaid_fragment_driver'
    sources = sorted((code_root / 'common').glob('*.c')) + \
        sorted((code_root / 'iso-2').glob('*.c'))
    command = [compiler, '-std=c11', '-O1', '-o', str(binary), str(DRIVER)] + \
        [str(s) for s in sources] + \
        ['-I', str(code_root / 'common'), '-I', str(code_root / 'iso-2')]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(f'driver build failed\n{result.stderr[-4000:]}')
    return binary


class ElementFragmentGrammarTest(unittest.TestCase):
    binary = None
    work_dir = None

    @classmethod
    def setUpClass(cls):
        if not SCHEMA.exists():
            raise unittest.SkipTest(
                f'ISO 15118-2 schemas not present at {SCHEMA}; run '
                '"python src/main.py --auto-download-public-xsd 1" once')
        cls.work_dir = tempfile.mkdtemp(prefix='cbexigen-fragment-test-')
        code_root = generate(cls.work_dir)
        cls.binary = compile_driver(code_root, cls.work_dir)

    @classmethod
    def tearDownClass(cls):
        if cls.work_dir:
            shutil.rmtree(cls.work_dir, ignore_errors=True)

    def test_emaid_fragment_matches_reference(self):
        failures = []
        vectors = read_vectors()
        self.assertEqual(len(vectors), 12, 'expected 12 pinned vectors')
        for identifier, value, expected in vectors:
            result = subprocess.run([str(self.binary), identifier, value],
                                    capture_output=True, text=True)
            actual = result.stdout.strip()
            if result.returncode != 0:
                actual = f'<driver exit {result.returncode}: {result.stderr.strip()}>'
            if actual != expected:
                failures.append(
                    f'  Id={identifier!r} value={value!r}\n'
                    f'    expected {expected}\n'
                    f'    actual   {actual}')
        if failures:
            self.fail(
                f'{len(failures)} of {len(vectors)} eMAID fragment vectors differ '
                f'from the Exificient reference:\n' + '\n'.join(failures))


if __name__ == '__main__':
    unittest.main()
