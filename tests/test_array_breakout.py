# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2026 chargebyte GmbH
# Copyright (c) 2022 - 2026 Contributors to EVerest

"""End to end check of ISO 15118-2 arrays filled to their maxOccurs.

Generates the ISO 15118-2 codec, compiles it together with a small driver,
decodes reference streams produced by Exificient, encodes them again and
compares the bytes with the reference.

Each stream holds one repeated particle at exactly its maxOccurs. There the
grammar leaves the particle's loop without coding another event, so a decoder
that reads one more event, or an encoder that writes one, fails here.

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
VECTORS = Path(__file__).resolve().parent / 'vectors' / 'array_breakout_iso2.txt'
DRIVER = Path(__file__).resolve().parent / 'iso2_roundtrip_driver.c'
CONFIG = Path(__file__).resolve().parent / 'config_iso2_only.py'


def read_vectors():
    vectors = []
    for line in VECTORS.read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        name, expected = line.split('\t')
        vectors.append((name, expected))
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
    binary = Path(out_dir) / 'iso2_roundtrip_driver'
    sources = sorted((code_root / 'common').glob('*.c')) + \
        sorted((code_root / 'iso-2').glob('*.c'))
    command = [compiler, '-std=c11', '-O1', '-o', str(binary), str(DRIVER)] + \
        [str(s) for s in sources] + \
        ['-I', str(code_root / 'common'), '-I', str(code_root / 'iso-2')]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(f'driver build failed\n{result.stderr[-4000:]}')
    return binary


class ArrayBreakoutTest(unittest.TestCase):
    binary = None
    work_dir = None

    @classmethod
    def setUpClass(cls):
        if not SCHEMA.exists():
            raise unittest.SkipTest(
                f'ISO 15118-2 schemas not present at {SCHEMA}; run '
                '"python src/main.py --auto-download-public-xsd 1" once')
        cls.work_dir = tempfile.mkdtemp(prefix='cbexigen-breakout-test-')
        code_root = generate(cls.work_dir)
        cls.binary = compile_driver(code_root, cls.work_dir)

    @classmethod
    def tearDownClass(cls):
        if cls.work_dir:
            shutil.rmtree(cls.work_dir, ignore_errors=True)

    def assert_round_trip(self, vectors):
        failures = []
        for name, expected in vectors:
            result = subprocess.run([str(self.binary), expected],
                                    capture_output=True, text=True)
            lines = result.stdout.split()
            if lines[:2] != ['decode=0', 'encode=0'] or len(lines) != 3 or lines[2] != expected:
                failures.append(
                    f'  {name}\n'
                    f'    expected decode=0 encode=0 {expected}\n'
                    f'    actual   {" ".join(lines) or "<no output>"}'
                    f' (exit {result.returncode}) {result.stderr.strip()}')
        if failures:
            self.fail(
                f'{len(failures)} of {len(vectors)} array break-out vectors do not '
                f'round trip to the Exificient reference:\n' + '\n'.join(failures))

    def test_arrays_at_max_occurs_round_trip(self):
        vectors = read_vectors()
        self.assertEqual(len(vectors), 7, 'expected 7 pinned vectors')
        self.assert_round_trip(vectors)


if __name__ == '__main__':
    unittest.main()
