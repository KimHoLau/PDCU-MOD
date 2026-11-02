"""Built-in K10D four-season data calibrated from the KF style table (v2.9).

The K10D (2006) has no Custom Image menu: its private IFD carries a tiny
0x021A table with only two "image tone" records (Bright / Natural), 5 parameter
slots and 12-byte records, plus two 18-byte matrices.  PDCU 5.10.2.2 needs the
12-parameter / 26-byte layout before it will list HARUBENI / KATEN / KYUSHU /
FUYUNO, so a K10D target goes through the same table rebuild as the 645D and
K20D; the K10D is simply one generation older (5 slots instead of 8 / 11).

Its 0x021B mode-0 matrix is the body's own input transform: the four bundled
matrices are M(KF season) * Y with Y = inv(M(KF)[0]) * M(K10D)[0], quantised to
Q13.  Relative season style R = M * inv(M_base) therefore matches KF to
<= 0.47 Q13 LSB.  BASE_MATRIX below is that mode-0 matrix, so a K10D target
needs no run-time recalibration (Y = I).

The K10D's own style table is the old generation one (only two mode records
exist, and the Natural record differs from KF's by 8.6e-2), so this is a
dedicated bundle rather than a "same style table" cross-model transplant.

Two things differ from the K20D bundle:

* the private block is DNGPrivateData (0xC634) with offsets relative to the
  block start, not an AOC MakerNote with absolute offsets;
* the block is not packed - a 19,048-byte zero-filled run sits after the
  embedded JPEG preview, so the rebuilt tables fit inside the block and the
  file does not grow at all.

CM2 is the ColorMatrix2 this sample carries.  It does NOT agree with the
0x021B base (dY = 0.27), because the file came from an old/third-party PEF to
DNG converter; PDCU ignores ColorMatrix1/2 and multiplies 0x021B, so the
mismatch is metadata-only.  The value is kept so a non-K10D target of this
bundle still gets the tool's cross-check warning.

Record parameter slots 4..10 do not exist in the camera's own table; the tool
fills 4..9 with the neutral 0 and 10 with 0xFFFF.  Measured in PDCU, filling
4..6 with 0 or with 1/0xFFFF/0xFFFF renders pixel-identically.
"""

__copyright__ = "Copyright © 2026 KimHoLau X deepseek harness"

from season_common import (BLOCK_SIZE, K30_SERIES_RECORDS, N_PARAMS,
                           REC_SIZE, TABLE_PARAMS)

MODEL = 'PENTAX K10D'
UNIQUE_MODEL = 'PENTAX K10D'
BLOCK_COUNT = 4
PRIV_ENDIAN = '>'

# Mode-0 colour matrix of the K10D (9 x Q13 ints, rows sum to 1.0).  The
# bundled season matrices are already expressed in the K10D colour space, so a
# K10D target needs no run-time recalibration; another body would get Y from
# this base.
BASE_MATRIX = (12576, -3872, -512, -896, 11328, -2240, -96, -2080, 10368)

# ColorMatrix2 of this K10D sample (DNG 0xC622).  It disagrees with the 0x021B
# base by 0.27 (old-converter metadata); PDCU does not read it.  Kept for the
# base-vs-CM2 sanity check when this bundle donates to another body.
CM2 = (1.098602, -0.257263, -0.038010,
       -0.568558, 1.259155, 0.250153,
       -0.067535, 0.060776, 0.977936)

# KF season records in the K10D byte order, with param 128 (the 0x021B matrix
# index) renumbered to this bundle's 0..3.
RECORDS = dict(K30_SERIES_RECORDS)

# M(KF season) * Y, quantised to Q13 in the K10D's big-endian byte order.
MATRICES = {
    0: bytes.fromhex('356ff6abf3e6f75938d2efd5f71c0a441ea0'),
    1: bytes.fromhex('38fcea18fcecfcee3489ee89029cf2402b25'),
    2: bytes.fromhex('3644e5bd03ff04e71ca1fe78ff2505ab1b30'),
    3: bytes.fromhex('22a8ff9afdbefee724a5fc74013205d618f8'),
}
