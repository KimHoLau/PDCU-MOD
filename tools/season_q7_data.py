"""Built-in Q7 four-season data calibrated from the KF style table.

The Q7 (1/1.7" sensor) has no 0x021A/0x021B and stores its private
block little-endian.  Its ColorMatrix2 differs a lot from the SLR
bodies, so the KF season style is calibrated through
Y = T(KF) * inv(T(Q7)), T = diag(1/(CM2*W)) * CM2.  This is the same
construction used for the K-01; it is an inference, not official
Pentax season data for the Q7.

CM2 keeps that calibration input and CALIBRATED_FROM names the style table
these matrices were derived from, so dng_season_params.baked_calibration()
can prove at run time that the bundle still equals KF-style * Y for the file
being patched.
"""

__copyright__ = "Copyright © 2026 KimHoLau X deepseek harness"

from season_common import (BLOCK_SIZE, N_PARAMS, Q7_MX1_RECORDS, REC_SIZE,
                           TABLE_PARAMS)

# DNG ColorMatrix2 (0xC622) of the Q7 sample these seasons were calibrated
# on.  Only used by the offline-calibration check, never written to a file.
CM2 = (1.299453735352, -0.559326171875, -0.110717773438,
       -0.187881469727, 1.013946533203, 0.202682495117,
       -0.006423950195, 0.123291015625, 0.491882324219)

# Style table the four season matrices were derived from.
CALIBRATED_FROM = 'kf'

MODEL = 'PENTAX Q7'
UNIQUE_MODEL = 'PENTAX Q7'
BLOCK_COUNT = 4
PRIV_ENDIAN = '<'

# Base colour matrix implied by the bundled season matrices (M = MKF * Y).
# It lets another body recalibrate these seasons if this module is used
# as a donor.
BASE_MATRIX = (11268, -856, -2220, -2319, 14321, -3810, -79, -4295, 12565)

RECORDS = dict(Q7_MX1_RECORDS)

MATRICES = {
    0: bytes.fromhex('242fe506f7e9f9f05147b6e719f64205a524'),
    1: bytes.fromhex('b433c2f68af55ff6e243c0e5f602aae86134'),
    2: bytes.fromhex('d0314eefe2fe1f00c6251bfab1fd8902c61f'),
    3: bytes.fromhex('9b1db10ab4f7edf94c2ec6f779ffbe03c91c'),
}
