# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2026 chargebyte GmbH
# Copyright (c) 2022 - 2026 Contributors to EVerest

"""
End to end check of ISO 15118-20 arrays filled to their maxOccurs.

Generates the ISO 15118-20 CommonMessages codec, compiles it together with a
small driver, decodes reference streams produced by Exificient, encodes them
again and compares the bytes with the reference (see exi_roundtrip.py).

Each stream holds one repeated particle at exactly its maxOccurs. There the
grammar leaves the particle's loop without coding another event, so a decoder
that reads one more event, or an encoder that writes one, fails here.

Needs the ISO 15118-20 schemas under src/input/schemas; fetch them once with
    python src/main.py --auto-download-public-xsd 1
The test skips, rather than fails, when they are absent or when no C compiler
is available.
"""
import unittest

import exi_roundtrip


class Iso20ArrayBreakoutTest(exi_roundtrip.RoundTripTest):
    standard = 'ISO 15118-20'
    schema = exi_roundtrip.SCHEMAS / 'ISO_15118-20' / 'FDIS' / 'V2G_CI_CommonMessages.xsd'
    schema_hint = '; run "python src/main.py --auto-download-public-xsd 1" once'
    codec = 'iso20_CommonMessages'
    codec_dir = 'iso-20'
    codec_sources = 'iso20_CommonMessages_*.c'
    driver_define = 'ROUNDTRIP_ISO20'
    vectors_file = exi_roundtrip.TESTS / 'vectors' / 'array_breakout_iso20.txt'

    def test_arrays_at_max_occurs_round_trip(self):
        vectors = self.read_vectors()
        self.assertEqual(len(vectors), 3, 'expected 3 pinned vectors')
        self.assert_round_trip(vectors)


if __name__ == '__main__':
    unittest.main()
