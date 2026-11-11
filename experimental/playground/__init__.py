"""The experimental determination playground.

An instrument for examining the relationship between:

    physical system -> experimental determination -> mathematical
    representation -> observed result -> revised determination

The software is organized around experimental questions, not equation
families. Equations enter as replaceable instruments validated by harnesses,
never trusted by construction.

Milestone 1 (this package): the diagnostic infrastructure. Typed failure
records, the L0 accounting-closure gate, known-answer and null harnesses,
planted-defect self-tests, and the provenance skeleton. The equation library
is deliberately absent: the laboratory tests its own determinations before
it owns any equations.
"""

__version__ = "0.1.0-milestone1"
