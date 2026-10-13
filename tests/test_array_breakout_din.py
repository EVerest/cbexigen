# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2026 chargebyte GmbH
# Copyright (c) 2022 - 2026 Contributors to EVerest

"""End to end check of DIN 70121 arrays at their occurrence limits.

Generates the DIN 70121 codec, compiles it together with a small driver,
decodes reference streams produced by Exificient, encodes them again and
compares the bytes with the reference (see exi_roundtrip.py).

The DIN 70121 schema declares these particles unbounded, and the generator
limits their array size (OCCURRENCE_LIMITS_CORRECTED). That size is only a
storage limit: the grammar stays a loop whose END event is coded with 2 bits,
also after the last occurrence that fits into the array.

Needs the DIN 70121 schemas under src/input/schemas/DIN_70121. They cannot be
downloaded by the generator, so the test skips, rather than fails, when they
are absent or when no C compiler is available.
"""
import unittest

import exi_roundtrip


class DinArrayBreakoutTest(exi_roundtrip.RoundTripTest):
    standard = 'DIN 70121'
    schema = exi_roundtrip.SCHEMAS / 'DIN_70121' / 'V2G_CI_MsgDef.xsd'
    codec = 'din'
    codec_dir = 'din'
    driver_define = 'ROUNDTRIP_DIN'
    vectors_file = exi_roundtrip.TESTS / 'vectors' / 'array_breakout_din.txt'

    def test_arrays_at_their_limit_round_trip(self):
        vectors = self.read_vectors()
        self.assertEqual(len(vectors), 1, 'expected 1 pinned vector')
        self.assert_round_trip(vectors)


if __name__ == '__main__':
    unittest.main()
