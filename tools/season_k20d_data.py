"""Built-in K20D four-season data calibrated from the KF style table (v2.8).

The K20D (2008) writes 0x021A/0x021B, but in the old generation layout:
8 parameter slots, 18-byte records, 20 mode records and 15 colour matrices.
PDCU 5.10.2.2 only offers the four seasons when the table uses the
12-parameter / 26-byte layout, so this bundle is written that way: the K20D's
own records are re-encoded with the parameter 7..10 slots filled by 0xFFFF,
and the four season records are the KF ones (big-endian, indices 0..3).

Its 0x021B base matrix and its DNG ColorMatrix2 (0xC622) agree to 2.0e-5, so
Y = inv(M(KF)[0]) * M(K20D)[0] is the body's input calibration and
M(K20D season) = M(KF season) * Y is the exact transplant: the relative
season style R = M * inv(M_base) is unchanged (<=0.46 Q13 LSB).

The K20D's own style table is the old generation one (median |R| difference
to KF is 7.7e-2, like the 645D), so this is a dedicated bundle instead of a
"same style table" calibrated cross-model transplant.  BASE_MATRIX below is
the K20D mode-0 matrix, so a K20D target needs no run-time recalibration.

Record parameter 7..10 do not exist in the camera's own table; the tool
writes the "unset" value 0xFFFF for them.  The K20D file's AOC MakerNote is
completely packed (largest gap 1 B), so the tool rebuilds the whole block at
the end of the file; see the docs for the measured layout.
"""

__copyright__ = "Copyright © 2026 KimHoLau X deepseek harness"

from season_common import (BLOCK_SIZE, K30_SERIES_RECORDS, N_PARAMS,
                           REC_SIZE, TABLE_PARAMS)

MODEL = 'PENTAX K20D'
UNIQUE_MODEL = 'PENTAX K20D'
BLOCK_COUNT = 4
PRIV_ENDIAN = '>'

# Mode-0 colour matrix of the K20D (9 x Q13 ints).  Because the bundled
# season matrices are already expressed in the K20D colour space, a K20D
# target needs no run-time recalibration; another body would get Y from
# this base.
BASE_MATRIX = (12448, -3584, -672, -1440, 11168, -1536, 192, -4320, 12320)

# K20D ColorMatrix2 (DNG 0xC622, 3x3 floats).  Only used for the
# base-vs-CM2 sanity check; it agrees with BASE_MATRIX to 2.0e-05.
CM2 = (1.138107, -0.346939, -0.148712,
       -0.476700, 1.345383, 0.098969,
       -0.145813, 0.312790, 0.671280)

# KF season records in the K20D byte order, with param 128 (the 0x021B
# matrix index) renumbered to this bundle's 0..3.
RECORDS = dict(K30_SERIES_RECORDS)

# M(KF season) * Y, quantised to Q13 in the K20D's big-endian byte order.
MATRICES = {
    0: bytes.fromhex('3461f9bbf1e4f4a0392af236f76702b625e2'),
    1: bytes.fromhex('3898ebd5fb93fa403567f05903f9e93832d0'),
    2: bytes.fromhex('3645e6220399036f1b3f0152ff66ff222177'),
    3: bytes.fromhex('21d0fffafe36fd2b2346ff8f015affca1edc'),
}
