"""Lifecycle: UNKNOWN expiry, reevaluation, and state transitions.

Two state tracks run through the laboratory and never merge:

- System track: anchor -> perturbation -> return -> misclosure.
- Determination track: issued -> conditions recorded -> expiry -> reevaluation.

Misclosure is to the system what UNKNOWN expiry is to the determination.
A transition in one track is not a transition in the other.
"""
