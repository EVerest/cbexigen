# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2026 chargebyte GmbH
# Copyright (c) 2022 - 2026 Contributors to EVerest

"""Shared code of the round trip tests for one generated codec.

A test class derived from RoundTripTest names its codec and vector file.
setUpClass generates the codec into a scratch directory with
config_roundtrip.py and compiles it together with exi_roundtrip_driver.c.
The driver decodes one reference stream produced by Exificient, encodes it
again and prints the bytes, which the tests compare with the reference.

The class skips, rather than fails, when the codec's schemas are absent or
when no C compiler is available.
"""
import os
import shutil
import subprocess  # nosec B404 - the tests run the generator, a C compiler and the built driver
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
SRC = REPO / 'src'
SCHEMAS = SRC / 'input' / 'schemas'
DRIVER = TESTS / 'exi_roundtrip_driver.c'
CONFIG = TESTS / 'config_roundtrip.py'


def read_vectors(path):
    """Return the (name, hex stream) pairs of a tab separated vector file."""
    vectors = []
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        name, expected = line.split('\t')
        vectors.append((name, expected))
    return vectors


def generate(codec, out_dir):
    """Generate the codec files whose names start with codec into out_dir and return the code root."""
    # tools_config imports the config by module name, so it has to sit next to
    # the other modules on sys.path[0], which is src/ when main.py runs.
    staged = SRC / CONFIG.name
    shutil.copyfile(CONFIG, staged)
    try:
        env = dict(os.environ, CBEXIGEN_TEST_OUT=str(out_dir), CBEXIGEN_TEST_CODEC=codec)
        result = subprocess.run(  # nosec B603 - fixed argument list, no shell
            [sys.executable, str(SRC / 'main.py'), '--config_file', CONFIG.name],
            cwd=str(REPO), env=env, capture_output=True, text=True)
        if result.returncode != 0:
            raise AssertionError(
                f'generator failed ({result.returncode})\n'
                f'{result.stdout[-4000:]}\n{result.stderr[-4000:]}')
    finally:
        staged.unlink(missing_ok=True)
    return Path(out_dir) / 'c'


def compile_driver(code_root, out_dir, codec_dir, codec_sources, define):
    """Compile the driver, selecting the codec with define, with the runtime and codec sources."""
    compiler = os.environ.get('CC') or shutil.which('cc') or shutil.which('gcc')
    if compiler is None:
        raise unittest.SkipTest('no C compiler found')
    binary = Path(out_dir) / 'exi_roundtrip_driver'
    sources = sorted((code_root / 'common').glob('*.c')) + \
        sorted((code_root / codec_dir).glob(codec_sources))
    command = [compiler, '-std=c11', '-O1', f'-D{define}', '-o', str(binary), str(DRIVER)] + \
        [str(s) for s in sources] + \
        ['-I', str(code_root / 'common'), '-I', str(code_root / codec_dir)]
    result = subprocess.run(command, capture_output=True, text=True)  # nosec B603 - fixed argument list, no shell
    if result.returncode != 0:
        raise AssertionError(f'driver build failed\n{result.stderr[-4000:]}')
    return binary


class RoundTripTest(unittest.TestCase):
    """Builds the round trip driver for one codec once per test class."""

    standard = ''          # name of the standard, for messages
    schema = None          # a schema file of the codec; the tests skip without it
    schema_hint = ''       # how to get the schemas, added to the skip message
    codec = ''             # start of the codec's names in c_files_to_generate
    codec_dir = ''         # directory of the generated codec below the code root
    codec_sources = '*.c'  # the codec's sources in codec_dir
    driver_define = ''     # macro that selects the codec in the driver
    vectors_file = None
    binary = None
    work_dir = None

    @classmethod
    def setUpClass(cls):
        if not cls.schema.exists():
            raise unittest.SkipTest(
                f'{cls.standard} schemas not present at {cls.schema}{cls.schema_hint}')
        cls.work_dir = tempfile.mkdtemp(prefix='cbexigen-roundtrip-test-')
        code_root = generate(cls.codec, cls.work_dir)
        cls.binary = compile_driver(code_root, cls.work_dir, cls.codec_dir,
                                    cls.codec_sources, cls.driver_define)

    @classmethod
    def tearDownClass(cls):
        if cls.work_dir:
            shutil.rmtree(cls.work_dir, ignore_errors=True)

    def read_vectors(self):
        return read_vectors(self.vectors_file)

    def run_driver(self, stream):
        return subprocess.run([str(self.binary), stream],  # nosec B603 - fixed argument list, no shell
                              capture_output=True, text=True)

    def assert_round_trip(self, vectors):
        failures = []
        for name, expected in vectors:
            result = self.run_driver(expected)
            lines = result.stdout.split()
            if lines[:2] != ['decode=0', 'encode=0'] or len(lines) != 3 or lines[2] != expected:
                failures.append(
                    f'  {name}\n'
                    f'    expected decode=0 encode=0 {expected}\n'
                    f'    actual   {" ".join(lines) or "<no output>"}'
                    f' (exit {result.returncode}) {result.stderr.strip()}')
        if failures:
            self.fail(
                f'{len(failures)} of {len(vectors)} {self.standard} vectors do not '
                f'round trip to the Exificient reference:\n' + '\n'.join(failures))
