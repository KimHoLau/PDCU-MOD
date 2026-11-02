"""Built-in K-7 four-season data calibrated from the KF style table (v2.10).

The K-7 (2009) writes the same AOC EXIF MakerNote as the K20D, but in a
different shape: 11 parameters per record (24 bytes), 22 mode records and 17
colour matrices.  The 34,002-byte block is packed (largest internal gap 1 B),
so the 12-parameter / 26-byte rebuild and the four extra matrices cannot fit
inside it; the tool rebuilds the whole block at the end of the file exactly as
for the K20D (absolute offsets are rebased, the EXIF 0x927C entry is
repointed, raw / preview / thumbnail do not move).

Its 0x021B base matrix and its DNG ColorMatrix2 disagree by 0.31, like the
K10D (0.27): the ColorMatrix metadata is not the same calibration as the maker
note table.  PDCU reads only 0x021B, and the K-7's mode-0 relative style is
identical to KF's (1.1e-16), so Y = inv(M(KF)[0]) * M(K-7)[0] is still the
body's exact input calibration and M(K-7 season) = M(KF season) * Y keeps the
relative season style R = M * inv(M_base) at <= 0.51 Q13 LSB.

The K-7's own style table is the old generation one (median |R| difference to
KF is 7.6e-2, like the K20D / 645D / K10D), so this is a dedicated bundle
rather than a "same style table" calibrated cross-model transplant.
BASE_MATRIX below is the K-7 mode-0 matrix, so a K-7 target needs no run-time
recalibration (Y = I).  CM2 is kept only for the base-vs-CM2 sanity check when
this bundle donates to another body; it triggers the tool's warning.

Measured in PDCU 5.10.2.2: the original 11-parameter table does not list the
four seasons; the rebuilt 12-parameter table lists them between SATOBI and
Pop Style, and a marker test (pure R / G / B / identity matrices) proves PDCU
reads matrices #17-#20 from this file.
"""

__copyright__ = "Copyright © 2026 KimHoLau X deepseek harness"

from season_common import (BLOCK_SIZE, K30_SERIES_RECORDS, N_PARAMS,
                           REC_SIZE, TABLE_PARAMS)

MODEL = 'PENTAX K-7'
UNIQUE_MODEL = 'PENTAX K-7'
BLOCK_COUNT = 4
PRIV_ENDIAN = '>'

# Mode-0 colour matrix of the K-7 (9 x Q13 ints).  The bundled season matrices
# are already expressed in the K-7 colour space, so a K-7 target needs no
# run-time recalibration; another body would get Y from this base.
BASE_MATRIX = (11744, -2624, -928, -832, 10304, -1280, 352, -3136, 10976)

# ColorMatrix2 of this K-7 sample (DNG 0xC622).  It disagrees with the 0x021B
# base by 0.31 (old-converter metadata, like the K10D); PDCU does not read it.
# Kept for the base-vs-CM2 sanity check when this bundle donates to another
# body.
CM2 = (0.877792, -0.269806, -0.061401,
       -0.418549, 1.111801, 0.274719,
       -0.086838, 0.138474, 0.877991)

# KF season records in the K-7 byte order, with param 128 (the 0x021B matrix
# index) renumbered to this bundle's 0..3.
RECORDS = dict(K30_SERIES_RECORDS)

# M(KF season) * Y, quantised to Q13 in the K-7's big-endian byte order.
MATRICES = {
    0: bytes.fromhex('3186fc6af210f7b4340bf441f91e04d2220f'),
    1: bytes.fromhex('3523f053fa8afcd830baf26e043dee992d2a'),
    2: bytes.fromhex('32dceb6901bb04cf19f6013b007701a41de6'),
    3: bytes.fromhex('206d0204fd90ff2a20fcffdb024a022f1b86'),
}
