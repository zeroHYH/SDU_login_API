from collections.abc import Sequence
from functools import lru_cache

SDU_PC1_MAP = (
    0, 1, 2, 6, 38, 37, 36, 7,
    8, 9, 10, 14, 46, 45, 44, 15,
    16, 17, 18, 22, 54, 53, 52, 23,
    24, 25, 26, 30, 62, 61, 60, 31,
    32, 33, 34, 35, 5, 4, 3, 39,
    40, 41, 42, 43, 13, 12, 11, 47,
    48, 49, 50, 51, 21, 20, 19, 55,
    56, 57, 58, 59, 29, 28, 27, 63,
)  # fmt: off

IP = (
    58, 50, 42, 34, 26, 18, 10, 2,
    60, 52, 44, 36, 28, 20, 12, 4,
    62, 54, 46, 38, 30, 22, 14, 6,
    64, 56, 48, 40, 32, 24, 16, 8,
    57, 49, 41, 33, 25, 17, 9, 1,
    59, 51, 43, 35, 27, 19, 11, 3,
    61, 53, 45, 37, 29, 21, 13, 5,
    63, 55, 47, 39, 31, 23, 15, 7,
)  # fmt: off

FP = (
    40, 8, 48, 16, 56, 24, 64, 32,
    39, 7, 47, 15, 55, 23, 63, 31,
    38, 6, 46, 14, 54, 22, 62, 30,
    37, 5, 45, 13, 53, 21, 61, 29,
    36, 4, 44, 12, 52, 20, 60, 28,
    35, 3, 43, 11, 51, 19, 59, 27,
    34, 2, 42, 10, 50, 18, 58, 26,
    33, 1, 41, 9, 49, 17, 57, 25,
)  # fmt: off

P = (
    16, 7, 20, 21,
    29, 12, 28, 17,
    1, 15, 23, 26,
    5, 18, 31, 10,
    2, 8, 24, 14,
    32, 27, 3, 9,
    19, 13, 30, 6,
    22, 11, 4, 25,
)  # fmt: off

PC1 = (
    57, 49, 41, 33, 25, 17, 9,
    1, 58, 50, 42, 34, 26, 18,
    10, 2, 59, 51, 43, 35, 27,
    19, 11, 3, 60, 52, 44, 36,
    63, 55, 47, 39, 31, 23, 15,
    7, 62, 54, 46, 38, 30, 22,
    14, 6, 61, 53, 45, 37, 29,
    21, 13, 5, 28, 20, 12, 4,
)  # fmt: off


PC2 = (
    14, 17, 11, 24, 1, 5,
    3, 28, 15, 6, 21, 10,
    23, 19, 12, 4, 26, 8,
    16, 7, 27, 20, 13, 2,
    41, 52, 31, 37, 47, 55,
    30, 40, 51, 45, 33, 48,
    44, 49, 39, 56, 34, 53,
    46, 42, 50, 36, 29, 32,
)  # fmt: off

SHIFTS = (1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1)

SBOX = (
    (
        (14, 4, 13, 1, 2, 15, 11, 8, 3, 10, 6, 12, 5, 9, 0, 7),
        (0, 15, 7, 4, 14, 2, 13, 1, 10, 6, 12, 11, 9, 5, 3, 8),
        (4, 1, 14, 8, 13, 6, 2, 11, 15, 12, 9, 7, 3, 10, 5, 0),
        (15, 12, 8, 2, 4, 9, 1, 7, 5, 11, 3, 14, 10, 0, 6, 13),
    ),
    (
        (15, 1, 8, 14, 6, 11, 3, 4, 9, 7, 2, 13, 12, 0, 5, 10),
        (3, 13, 4, 7, 15, 2, 8, 14, 12, 0, 1, 10, 6, 9, 11, 5),
        (0, 14, 7, 11, 10, 4, 13, 1, 5, 8, 12, 6, 9, 3, 2, 15),
        (13, 8, 10, 1, 3, 15, 4, 2, 11, 6, 7, 12, 0, 5, 14, 9),
    ),
    (
        (10, 0, 9, 14, 6, 3, 15, 5, 1, 13, 12, 7, 11, 4, 2, 8),
        (13, 7, 0, 9, 3, 4, 6, 10, 2, 8, 5, 14, 12, 11, 15, 1),
        (13, 6, 4, 9, 8, 15, 3, 0, 11, 1, 2, 12, 5, 10, 14, 7),
        (1, 10, 13, 0, 6, 9, 8, 7, 4, 15, 14, 3, 11, 5, 2, 12),
    ),
    (
        (7, 13, 14, 3, 0, 6, 9, 10, 1, 2, 8, 5, 11, 12, 4, 15),
        (13, 8, 11, 5, 6, 15, 0, 3, 4, 7, 2, 12, 1, 10, 14, 9),
        (10, 6, 9, 0, 12, 11, 7, 13, 15, 1, 3, 14, 5, 2, 8, 4),
        (3, 15, 0, 6, 10, 1, 13, 8, 9, 4, 5, 11, 12, 7, 2, 14),
    ),
    (
        (2, 12, 4, 1, 7, 10, 11, 6, 8, 5, 3, 15, 13, 0, 14, 9),
        (14, 11, 2, 12, 4, 7, 13, 1, 5, 0, 15, 10, 3, 9, 8, 6),
        (4, 2, 1, 11, 10, 13, 7, 8, 15, 9, 12, 5, 6, 3, 0, 14),
        (11, 8, 12, 7, 1, 14, 2, 13, 6, 15, 0, 9, 10, 4, 5, 3),
    ),
    (
        (12, 1, 10, 15, 9, 2, 6, 8, 0, 13, 3, 4, 14, 7, 5, 11),
        (10, 15, 4, 2, 7, 12, 9, 5, 6, 1, 13, 14, 0, 11, 3, 8),
        (9, 14, 15, 5, 2, 8, 12, 3, 7, 0, 4, 10, 1, 13, 11, 6),
        (4, 3, 2, 12, 9, 5, 15, 10, 11, 14, 1, 7, 6, 0, 8, 13),
    ),
    (
        (4, 11, 2, 14, 15, 0, 8, 13, 3, 12, 9, 7, 5, 10, 6, 1),
        (13, 0, 11, 7, 4, 9, 1, 10, 14, 3, 5, 12, 2, 15, 8, 6),
        (1, 4, 11, 13, 12, 3, 7, 14, 10, 15, 6, 8, 0, 5, 9, 2),
        (6, 11, 13, 8, 1, 4, 10, 7, 9, 5, 0, 15, 14, 2, 3, 12),
    ),
    (
        (13, 2, 8, 4, 6, 15, 11, 1, 10, 9, 3, 14, 5, 0, 12, 7),
        (1, 15, 13, 8, 10, 3, 7, 4, 12, 5, 6, 11, 0, 14, 9, 2),
        (7, 11, 4, 1, 9, 12, 14, 2, 0, 6, 10, 13, 15, 3, 5, 8),
        (2, 1, 14, 7, 4, 10, 8, 13, 15, 12, 9, 0, 3, 5, 6, 11),
    ),
)  # fmt: off


def _permute(x: int, in_bits: int, table: Sequence[int]) -> int:
    y = 0
    n = len(table)
    for i, pos in enumerate(table):
        bit = (x >> (in_bits - pos)) & 1
        y |= bit << (n - 1 - i)
    return y


def _build_spbox() -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(
            _permute(
                SBOX[box_idx][((chunk & 0x20) >> 4) | (chunk & 0x01)][
                    (chunk >> 1) & 0x0F
                ]
                << (28 - 4 * box_idx),
                32,
                P,
            )
            for chunk in range(64)
        )
        for box_idx in range(8)
    )


def _build_perm64_lut(table: Sequence[int]) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(_permute(v << (56 - 8 * byte_idx), 64, table) for v in range(256))
        for byte_idx in range(8)
    )


def _permute64_via_lut(x: int, lut: Sequence[Sequence[int]]) -> int:
    return (
        lut[0][(x >> 56) & 0xFF]
        | lut[1][(x >> 48) & 0xFF]
        | lut[2][(x >> 40) & 0xFF]
        | lut[3][(x >> 32) & 0xFF]
        | lut[4][(x >> 24) & 0xFF]
        | lut[5][(x >> 16) & 0xFF]
        | lut[6][(x >> 8) & 0xFF]
        | lut[7][x & 0xFF]
    )


def _rol28(v: int, n: int) -> int:
    v &= 0x0FFFFFFF
    return ((v << n) & 0x0FFFFFFF) | (v >> (28 - n))


def _subkeys_from_key64(key64: int) -> tuple[int, ...]:
    k56 = _permute(key64, 64, PC1)
    c = (k56 >> 28) & 0x0FFFFFFF
    d = k56 & 0x0FFFFFFF
    out = []
    for s in SHIFTS:
        c = _rol28(c, s)
        d = _rol28(d, s)
        cd = (c << 28) | d
        out.append(_permute(cd, 56, PC2))
    return tuple(out)


SPBOX = _build_spbox()
IP_LUT = _build_perm64_lut(IP)
FP_LUT = _build_perm64_lut(FP)


def _build_round_tables(
    subkeys: Sequence[int],
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    vals = range(64)

    def one_round(k48: int) -> tuple[tuple[int, ...], ...]:
        k0 = (k48 >> 42) & 0x3F
        k1 = (k48 >> 36) & 0x3F
        k2 = (k48 >> 30) & 0x3F
        k3 = (k48 >> 24) & 0x3F
        k4 = (k48 >> 18) & 0x3F
        k5 = (k48 >> 12) & 0x3F
        k6 = (k48 >> 6) & 0x3F
        k7 = k48 & 0x3F
        return (
            tuple(SPBOX[0][v ^ k0] for v in vals),
            tuple(SPBOX[1][v ^ k1] for v in vals),
            tuple(SPBOX[2][v ^ k2] for v in vals),
            tuple(SPBOX[3][v ^ k3] for v in vals),
            tuple(SPBOX[4][v ^ k4] for v in vals),
            tuple(SPBOX[5][v ^ k5] for v in vals),
            tuple(SPBOX[6][v ^ k6] for v in vals),
            tuple(SPBOX[7][v ^ k7] for v in vals),
        )

    return tuple(one_round(k48) for k48 in subkeys)


def _des_encrypt_block(
    block64: int, round_tables: Sequence[Sequence[Sequence[int]]]
) -> int:
    x = _permute64_via_lut(block64, IP_LUT)
    l = (x >> 32) & 0xFFFFFFFF
    r = x & 0xFFFFFFFF
    for rt in round_tables:
        t0, t1, t2, t3, t4, t5, t6, t7 = rt
        c0 = ((r & 0x00000001) << 5) | ((r >> 27) & 0x1F)
        c1 = (r >> 23) & 0x3F
        c2 = (r >> 19) & 0x3F
        c3 = (r >> 15) & 0x3F
        c4 = (r >> 11) & 0x3F
        c5 = (r >> 7) & 0x3F
        c6 = (r >> 3) & 0x3F
        c7 = ((r & 0x0000001F) << 1) | ((r >> 31) & 0x01)
        f = t0[c0] ^ t1[c1] ^ t2[c2] ^ t3[c3] ^ t4[c4] ^ t5[c5] ^ t6[c6] ^ t7[c7]
        l, r = r, l ^ f
    pre = (r << 32) | l
    return _permute64_via_lut(pre, FP_LUT)


def fix_mutated_key(k: bytes) -> bytes:
    x = int.from_bytes(k, "big")
    y = 0
    for dst, src in enumerate(SDU_PC1_MAP):
        y |= ((x >> (63 - src)) & 1) << (63 - dst)
    return y.to_bytes(8, "big")


@lru_cache(maxsize=256)
def _key_part_subkeys(k4: str) -> tuple[tuple[tuple[int, ...], ...], ...]:
    fixed = fix_mutated_key(k4.encode("utf-16-be"))
    k64 = int.from_bytes(fixed, "big")
    return _build_round_tables(_subkeys_from_key64(k64))


@lru_cache(maxsize=128)
def _expand_round_keys(
    keys: tuple[str, ...],
) -> tuple[tuple[tuple[tuple[int, ...], ...], ...], ...]:
    return tuple(
        _key_part_subkeys((key[i : i + 4] + "\0\0\0\0")[:4])
        for key in keys
        for i in range(0, len(key), 4)
    )


def strEnc(data: str, *keys: str) -> str:
    if not data:
        return ""
    out = []
    for i in range(0, len(data), 4):
        d4 = (data[i : i + 4] + "\0\0\0\0")[:4]
        block = int.from_bytes(d4.encode("utf-16-be"), "big")
        for sk in _expand_round_keys(tuple(keys)):
            block = _des_encrypt_block(block, sk)
        out.append(f"{block:016X}")
    return "".join(out)
