# SPDX-License-Identifier: Apache-2.0
"""Generate, compile and exercise the common integer runtime."""
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / 'src'
CONFIG = Path(__file__).with_name('config_common_only.py')
DRIVER = Path(__file__).with_name('basetypes_integer_driver.c')
VALUES = (0, 1, -1, 127, 128, 200, -200, -(2**31), 2**31 - 1,
          -(2**63), 2**63 - 1)
SENTINEL = 123456789


class BasetypesIntegerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shlex.split(os.environ.get('CC') or shutil.which('cc') or
                               shutil.which('gcc') or shutil.which('clang') or '')
        if not compiler or shutil.which(compiler[0]) is None:
            raise unittest.SkipTest('no C compiler found')
        work = tempfile.TemporaryDirectory(prefix='cbexigen-integer-test-')
        cls.addClassCleanup(work.cleanup)
        out = Path(work.name)
        staged = SRC / CONFIG.name
        shutil.copyfile(CONFIG, staged)
        try:
            result = subprocess.run(
                [sys.executable, str(SRC / 'main.py'), '--config_file', CONFIG.name],
                cwd=REPO, env=dict(os.environ, CBEXIGEN_TEST_OUT=str(out)),
                capture_output=True, text=True)
            if result.returncode:
                raise AssertionError(f'generator failed\n{result.stdout}\n{result.stderr}')
        finally:
            staged.unlink()
        flags = ['-std=c11', '-Wall', '-Wextra', '-Werror']
        sanitizer = ['-fsanitize=undefined', '-fno-sanitize-recover=undefined']
        probe = subprocess.run(
            compiler + flags + sanitizer + ['-x', 'c', '-', '-o', str(out / 'probe')],
            input='int main(void) { return 0; }\n', capture_output=True, text=True)
        if probe.returncode == 0:
            flags += sanitizer
        common = out / 'c' / 'common'
        cls.binary = out / 'basetypes_integer_driver'
        result = subprocess.run(
            compiler + flags + ['-I', str(common), str(DRIVER)] +
            [str(p) for p in sorted(common.glob('*.c'))] +
            ['-o', str(cls.binary)], capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(f'driver build failed\n{result.stdout}\n{result.stderr}')

    def run_driver(self, *args):
        result = subprocess.run([str(self.binary), *map(str, args)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        self.assertEqual(len(result.stdout.splitlines()), 1)
        return dict(part.split('=', 1) for part in result.stdout.split())

    def test_uint8_range(self):
        encoded = self.run_driver('encode_uint8', 255)
        self.assertEqual(encoded, {'rc': '0', 'wire': 'ff01'})
        self.assertEqual(self.run_driver('uint8', encoded['wire']),
                         {'rc': '0', 'value': '255'})
        self.assertEqual(self.run_driver('uint8', '8002'),
                         {'rc': '-113', 'value': '123'})

    def test_uint16_range(self):
        encoded = self.run_driver('encode_uint16', 65535)
        self.assertEqual(encoded, {'rc': '0', 'wire': 'ffff03'})
        self.assertEqual(self.run_driver('uint16', encoded['wire']),
                         {'rc': '0', 'value': '65535'})
        self.assertEqual(self.run_driver('uint16', '808004'),
                         {'rc': '-113', 'value': '12345'})

    def test_uint32_range(self):
        encoded = self.run_driver('encode_uint32', 2**32 - 1)
        self.assertEqual(encoded, {'rc': '0', 'wire': 'ffffffff0f'})
        self.assertEqual(self.run_driver('uint32', encoded['wire']),
                         {'rc': '0', 'value': str(2**32 - 1)})
        self.assertEqual(self.run_driver('uint32', '8080808010'),
                         {'rc': '-113', 'value': str(SENTINEL)})

    def test_uint64_range(self):
        encoded = self.run_driver('encode_uint64', 2**64 - 1)
        self.assertEqual(encoded, {'rc': '0', 'wire': 'ff' * 9 + '01'})
        self.assertEqual(self.run_driver('uint64', encoded['wire']),
                         {'rc': '0', 'value': str(2**64 - 1)})
        self.assertEqual(self.run_driver('uint64', '80' * 9 + '02'),
                         {'rc': '-113', 'value': str(SENTINEL)})

    def test_unsigned_decoder_returns_api_bytes(self):
        self.assertEqual(self.run_driver('unsigned_bytes', '8001'),
                         {'rc': '0', 'count': '1', 'bytes': '80'})
        self.assertEqual(self.run_driver('unsigned_bytes', '00'),
                         {'rc': '0', 'count': '0', 'bytes': ''})

    def test_unsigned_decoder_normalizes_redundant_groups(self):
        for wire, data in (('8000', ''), ('808000', ''), ('818000', '01')):
            with self.subTest(wire=wire):
                self.assertEqual(self.run_driver('unsigned_bytes', wire),
                                 {'rc': '0', 'count': str(len(data) // 2), 'bytes': data})

    def test_unsigned_helpers_read_api_bytes(self):
        for bits in (32, 64):
            extra = (5,) if bits == 32 else ()
            for prefix in ('', '000000'):
                with self.subTest(bits=bits, prefix=prefix):
                    self.assertEqual(
                        self.run_driver(f'from_unsigned{bits}', prefix + 'ff' * (bits // 8), *extra),
                        {'rc': '0', 'value': str(2**bits - 1)})
                    self.assertEqual(self.run_driver(f'from_unsigned{bits}', prefix, *extra),
                                     {'rc': '0', 'value': '0'})
            self.assertEqual(
                self.run_driver(f'from_unsigned{bits}', '01' + '00' * 8, *extra),
                {'rc': '-113', 'value': str(SENTINEL)})
        for data, limit, error in (('0100000000', 5, -113),
                                   ('0100000000', 4, -31),
                                   ('0800000000', 5, -31),
                                   ('0800000000', 6, -113),
                                   ('01' + '00' * 8, 0, -113),
                                   ('80', 1, -31), ('', 0, -31)):
            with self.subTest(data=data, limit=limit):
                self.assertEqual(self.run_driver('from_unsigned32', data, limit),
                                 {'rc': str(error), 'value': str(SENTINEL)})

    def test_unsigned32_max_octets_counts_exi_octets(self):
        self.assertEqual(self.run_driver('to_unsigned32', 128, 1)['rc'], '-31')
        self.assertEqual(self.run_driver('to_unsigned32', 0, 0)['rc'], '-31')

    def test_unsigned_helpers_match_uint_codecs(self):
        for bits in (64, 32):
            extra = (5,) if bits == 32 else ()
            for value in (0, 1, 127, 128, 2**32 - 1, 2**32, 2**64 - 1):
                if value >= 2**bits:
                    continue
                reference = self.run_driver('encode_uint64', value)
                self.assertEqual(reference['rc'], '0')
                with self.subTest(bits=bits, value=value, direction='to'):
                    self.assertEqual(
                        self.run_driver(f'to_unsigned{bits}', value, *extra), reference)
                with self.subTest(bits=bits, value=value, direction='from'):
                    self.assertEqual(
                        self.run_driver(f'decode_unsigned{bits}', reference['wire'], *extra),
                        {'rc': '0', 'value': str(value)})

    def test_signed_helpers_match_integer_codecs(self):
        for bits in (64, 32):
            extra = (5,) if bits == 32 else ()
            for value in VALUES:
                if not -(2**(bits - 1)) <= value < 2**(bits - 1):
                    continue
                reference = self.run_driver(f'integer{bits}', value)
                self.assertEqual(reference['rc'], '0')
                with self.subTest(bits=bits, value=value, direction='to'):
                    self.assertEqual(
                        self.run_driver(f'to_signed{bits}', value, *extra), reference)
                with self.subTest(bits=bits, value=value, direction='from'):
                    expected = {'rc': '0', 'value': str(value)}
                    self.assertEqual(
                        self.run_driver(f'decode_integer{bits}', reference['wire']), expected)
                    self.assertEqual(
                        self.run_driver(f'from_signed{bits}', reference['wire'], *extra),
                        expected)

    def test_signed_wire_parts(self):
        for value, sign, magnitude in ((128, 0, 128), (-1, 1, 0),
                                       (-200, 1, 199),
                                       (-(2**63), 1, 2**63 - 1)):
            with self.subTest(value=value):
                encoded = self.run_driver('to_signed64', value)
                self.assertEqual(encoded['rc'], '0')
                self.assertEqual(self.run_driver('parts', encoded['wire']),
                                 {'sign': str(sign), 'magnitude': str(magnitude)})

    def test_signed32_max_octets_counts_exi_octets(self):
        self.assertEqual(self.run_driver('to_signed32', 128, 1)['rc'], '-31')

    def test_signed32_rejects_out_of_range_magnitude(self):
        for value in (2**31, -(2**31) - 1):
            with self.subTest(value=value):
                encoded = self.run_driver('integer64', value)
                self.assertEqual(encoded['rc'], '0')
                self.assertEqual(self.run_driver('from_signed32', encoded['wire'], 5),
                                 {'rc': '-113', 'value': str(SENTINEL)})
                self.assertEqual(self.run_driver('from_signed32', encoded['wire'], 4),
                                 {'rc': '-31', 'value': str(SENTINEL)})

    def test_signed32_max_octets_error_preserves_destination(self):
        wire = self.run_driver('integer32', 128)['wire']
        self.assertEqual(self.run_driver('from_signed32', wire, 1),
                         {'rc': '-31', 'value': str(SENTINEL)})

    def test_signed64_rejects_out_of_range_magnitude(self):
        for sign in (0, 1):
            with self.subTest(sign=sign):
                encoded = self.run_driver('signed_bytes', sign, '8000000000000000')
                self.assertEqual(encoded['rc'], '0')
                self.assertEqual(self.run_driver('from_signed64', encoded['wire']),
                                 {'rc': '-113', 'value': str(SENTINEL)})

    def test_signed64_rejects_nine_byte_magnitude(self):
        for sign in (0, 1):
            with self.subTest(sign=sign):
                encoded = self.run_driver('signed_bytes', sign, '010000000000000000')
                self.assertEqual(encoded['rc'], '0')
                self.assertEqual(self.run_driver('from_signed64', encoded['wire']),
                                 {'rc': '-113', 'value': str(SENTINEL)})


if __name__ == '__main__':
    unittest.main()
