"""Validation: known-answer and null harnesses, planted defects, diagnostics.

The harnesses validate instruments, not models. A harness pass certifies an
instrument within its tested case set only; the records it returns say so
explicitly. The planted-defect suite is the laboratory testing its own
determinations: every planted defect must be caught and classified into the
correct failure class, or the build fails.
"""
