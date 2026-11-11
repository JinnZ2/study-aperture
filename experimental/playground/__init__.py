"""The experimental determination playground.

An instrument for examining the relationship between:

    physical system -> experimental determination -> mathematical
    representation -> observed result -> revised determination

The software is organized around experimental questions, not equation
families. Equations enter as replaceable instruments validated by harnesses,
never trusted by construction.

Milestones 1-4 implement diagnostic infrastructure, the system track,
sensitivity-qualified absence and UNKNOWN expiry, and context-dependent
applicability mapping. Tests use constructed cases; neither the package nor
its checks establish empirical adequacy. Diagnostic-gated equation substitution
adds arithmetic adapters, while physical equation families remain deferred.
"""

__version__ = "0.5.0-experimental"
