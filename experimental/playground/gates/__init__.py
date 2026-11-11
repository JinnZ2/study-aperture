"""Gates: checkpoints that answer one experimental question and emit typed findings.

A gate outcome (PASS / FAIL / INDETERMINATE / BLOCKED) is a statement about
the gate's own question, never a verdict about a model. Axis-level meaning
lives in the FailureRecord every gate returns.
"""
