"""Hash-bound evidence links (the labref pattern).

bind() attaches a report to a claim by content digest and changes nothing
about the claim's state or support. Linking is not promoting: an integrity
PASS on the report side never becomes claim support by itself.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


def digest_payload(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class EvidenceLink:
    claim_id: str
    report_digest: str
    produced_by: str
    note: str = ""


@dataclass(frozen=True)
class EvidenceChain:
    links: tuple[EvidenceLink, ...] = ()

    def bind(
        self, claim_id: str, payload: str | bytes, produced_by: str, note: str = ""
    ) -> "EvidenceChain":
        link = EvidenceLink(
            claim_id=claim_id,
            report_digest=digest_payload(payload),
            produced_by=produced_by,
            note=note,
        )
        return EvidenceChain(self.links + (link,))

    def links_for(self, claim_id: str) -> tuple[EvidenceLink, ...]:
        return tuple(l for l in self.links if l.claim_id == claim_id)

    def verify_digest(self, payload: str | bytes) -> bool:
        """True when the payload still matches some bound digest.

        False means the payload changed, not that it is wrong.
        """
        digest = digest_payload(payload)
        return any(l.report_digest == digest for l in self.links)
