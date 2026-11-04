"""Built-in K-30 four-season data calibrated from the KF style table.

The K-30 has no 0x021A/0x021B, like the K-01 and K-50.  Its bundled
matrices use the same construction as those two bodies: read the body's
own DNG ColorMatrix2, form T = diag(1/(CM2*W)) * CM2 (D65), solve
Y = T(KF) * inv(T(K-30)), and write M(K-30 season) = M(KF season) * Y.
The K-30 ColorMatrix2 comes from sample/K30.DNG (firmware 1.06).

CM2 keeps that calibration input and CALIBRATED_FROM names the style table
these matrices were derived from, so dng_season_params.baked_calibration()
can prove at run time that the bundle still equals KF-style * Y for the file
being patched.
"""

__copyright__ = "Copyright © 2026 KimHoLau X deepseek harness"

from season_common import (BLOCK_SIZE, K30_SERIES_RECORDS, N_PARAMS,
                           REC_SIZE, TABLE_PARAMS)

# DNG ColorMatrix2 (0xC622) of the K-30 sample these seasons were calibrated
# on.  Only used by the offline-calibration check, never written to a file.
CM2 = (0.8908843994140625, -0.26922607421875, -0.1193084716796875,
       -0.3995361328125, 1.2301177978515625, 0.1880645751953125,
       -0.0991058349609375, 0.1737213134765625, 0.660430908203125)

# Style table the four season matrices were derived from.
CALIBRATED_FROM = 'kf'

MODEL = 'PENTAX K-30'
UNIQUE_MODEL = 'PENTAX K-30'
BLOCK_COUNT = 4
PRIV_ENDIAN = '>'

# Base colour matrix implied by the bundled season matrices (M = MKF * Y).
# At Q13 it quantises to exactly the K-3 base matrix, so these four seasons
# stay on the K-3 calibration line to the last LSB.
BASE_MATRIX = (12512, -4352, 32, -1728, 12832, -2912, 288, -3392, 11296)

RECORDS = dict(K30_SERIES_RECORDS)

MATRICES = {
    0: bytes.fromhex('346ff675f51cf32b40eaebebf74d084a2069'),
    1: bytes.fromhex('38fde783ff80f8e23c3eeae1047eec322f50'),
    2: bytes.fromhex('36d0e1f4073d02b51ff0fd5bff6103791d26'),
    3: bytes.fromhex('21bbff83fec2fc3f291cfaa5015003e01ad0'),
}
