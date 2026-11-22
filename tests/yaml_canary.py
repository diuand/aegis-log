"""Harmless target for the B-04 test: records that YAML constructed a call."""

TRIPPED: list[tuple] = []


def trip(*args):
    TRIPPED.append(args)
    return "tripped"
