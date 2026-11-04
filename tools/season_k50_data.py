"""Built-in K-50 four-season data calibrated from the KF style table.

The K-50 has no 0x021A/0x021B, like the K-30.  Its DNG ColorMatrix2
gives the same calibration as the K-3 (Y differs by 3.65e-5 from the
K-3 0x021B base, 3.24e-5 from the K-3 ColorMatrix2), so the season
matrices land within one Q13 LSB of the K-30 bundle.
Y = T(KF) * inv(T(K-50)), with T = diag(1/(CM2*W)) * CM2.

CM2 keeps the calibration input (the ColorMatrix2 of sample/K50.dng) and
CALIBRATED_FROM names the style table these matrices were derived from, so
dng_season_params.baked_calibration() can prove at run time that the bundle
still equals KF-style * Y for the file being patched."""

__copyright__ = "Copyright © 2026 KimHoLau X deepseek harness"

from season_common import (BLOCK_SIZE, K30_SERIES_RECORDS, N_PARAMS,
                           REC_SIZE, TABLE_PARAMS)

# DNG ColorMatrix2 (0xC622) of the K-50 sample these seasons were calibrated
# on.  Only used by the offline-calibration check, never written to a file.
CM2 = (0.8627777099609375, -0.2607269287109375, -0.1155548095703125,
       -0.3995361328125, 1.2301177978515625, 0.1880645751953125,
       -0.098968505859375, 0.1734771728515625, 0.6595458984375)

# Style table the four season matrices were derived from.
CALIBRATED_FROM = 'kf'

MODEL = 'PENTAX K-50'
UNIQUE_MODEL = 'PENTAX K-50'
BLOCK_COUNT = 4
PRIV_ENDIAN = '>'

# Base colour matrix implied by the bundled season matrices (M = MKF * Y).
# It lets another body recalibrate these seasons if this module is used
# as a donor.
BASE_MATRIX = (12512, -4352, 32, -1728, 12832, -2912, 288, -3392, 11296)

RECORDS = dict(K30_SERIES_RECORDS)

MATRICES = {
    0: bytes.fromhex('346ff675f51cf32b40eaebebf74d084a2068'),
    1: bytes.fromhex('38fde783ff80f8e23c3eeae1047eec332f50'),
    2: bytes.fromhex('36cfe1f4073d02b51ff0fd5bff6103791d26'),
    3: bytes.fromhex('21bbff83fec2fc3f291cfaa5015003e01ad0'),
}
