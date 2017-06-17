"""Utility package."""


def frame_to_str(data):
    """Convert raw data to formatted string."""
    return ":".join("{:02x}".format(c) for c in data)


def calc_crc(data):
    """Calculate frame CRC."""
    crc = 0x2d
    for b in data:
        crc += b
    return crc & 0xff
