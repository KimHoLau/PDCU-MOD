"""Built-in PENTAX *ist DL four-season data calibrated from the KF table (v2.12).

The *ist DL (2005, 6 MP CCD) is the oldest body this tool supports.  Its AOC
EXIF MakerNote (0x927C, offsets absolute to the file) carries a tiny 0x021A
table with seven "image tone" records, 5 parameter slots (1,2,3,128,129) and
12-byte records, plus seven 18-byte matrices.  PDCU 5.10.2.2 needs the
12-parameter / 26-byte layout before it lists HARUBENI / KATEN / KYUSHU /
FUYUNO, so an *ist DL target goes through the same rebuild as the K10D; the
body is simply older (5 slots, 12,408-byte packed block).

Its 0x021B mode-0 matrix is the body's own input transform: the four bundled
matrices are M(KF season) * Y with Y = inv(M(KF)[0]) * M(*ist DL)[0],
quantised to Q13.  max|Y-I| is 0.1625 - larger than the K10D (0.121) or the
K20D (0.097) - so the calibration is mandatory; relative season style
R = M * inv(M_base) matches KF to <= 0.49 Q13 LSB.  BASE_MATRIX below is that
mode-0 matrix, so an *ist DL target needs no run-time recalibration (Y = I).

The record and matrix layout is the same as the K10D / K-30 family: the
season records are the shared K30_SERIES_RECORDS (big-endian, param 128
renumbered to 0..3 here); the tool remaps them to the target's #7-#10.

What is different from the K10D bundle:

* the private block is an AOC MakerNote (0x927C) with absolute offsets, not
  DNGPrivateData (0xC634) with relative ones;
* the 12,408-byte block is packed (no gap at all), so the rebuilt tables do
  not fit inside it.  The tool copies the whole block to the end of the file
  and rewrites the one 0x927C offset (file +12,925 B, five changed bytes in
  the original area), exactly like the K20D / K-7.

CM2 is the ColorMatrix2 this sample carries.  It does NOT agree with the
0x021B base (dY = 0.154), because PDCU wrote the file and its ColorMatrix tags
come from a different calibration; PDCU reads 0x021B only, so the mismatch is
metadata-only.  The value is kept for the base-vs-CM2 sanity check.

PDCU 5.10.2.2 renders the four entries with these matrices: replacing
#7-#10 with pure red turns all four previews red while As Shot stays
pixel-identical, in the screen view and in a full-size "Save as" JPEG.
The body's own modes (Natural / Portrait / Landscape) ignore #1-#6 - only #0
and the new #7-#10 take part in the file matrices.
"""

__copyright__ = "Copyright © 2026 KimHoLau X deepseek harness"

from season_common import (BLOCK_SIZE, K30_SERIES_RECORDS, N_PARAMS,
                           REC_SIZE, TABLE_PARAMS)

MODEL = 'PENTAX *ist DL'
UNIQUE_MODEL = 'PENTAX *ist DL'
BLOCK_COUNT = 4
PRIV_ENDIAN = '>'

# Mode-0 colour matrix of the *ist DL (9 x Q13 ints, rows sum to 1.0).  The
# bundled season matrices are already expressed in the *ist DL colour space,
# so an *ist DL target needs no run-time recalibration; another body would get
# Y from this base.
BASE_MATRIX = (12512, -4640, 320, -1152, 11264, -1920, -384, -1600, 10176)

# ColorMatrix2 of this *ist DL sample (DNG 0xC622).  It disagrees with the
# 0x021B base by 0.154 (PDCU-written metadata); PDCU does not read it.
CM2 = (1.248199, -0.422760, -0.115280,
       -0.493912, 1.239655, 0.223831,
       -0.075073, 0.083786, 1.091751)

# KF season records in the *ist DL byte order, with param 128 (the 0x021B
# matrix index) renumbered to this bundle's 0..3.
RECORDS = dict(K30_SERIES_RECORDS)

# M(KF season) * Y, quantised to Q13 in the *ist DL's big-endian byte order.
MATRICES = {
    0: bytes.fromhex('3548f2f2f7c6f64c3886f12ef5e50c2d1def'),
    1: bytes.fromhex('38dae696008ffbf733daf02e0185f4132a68'),
    2: bytes.fromhex('3612e2b8073604001c3affc6fe0f06f21afe'),
    3: bytes.fromhex('2232fd6f0060fdeb247ffd95002506e418f6'),
}
