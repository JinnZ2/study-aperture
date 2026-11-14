Status: reasoning on the extract in `EXTRACT.md`. Every number below is either quoted there (OBSERVED), computed from quoted numbers (DERIVED, arithmetic shown), or a proposed next step (PROPOSED). Nothing here is a verdict on the paper's validity or on any tool. Not established: any statement about literature outside the 102-article corpus, about tools in other versions, or about results under other prompts.

# Checks: arXiv 2611.05459v1

Co-authored. CC0. Quotes are in `EXTRACT.md` (cited below as `E<item>`); this file holds reasoning only.

## C1 Constraint check: what each tool needs, and how much of measured skill is access

**OBSERVED**
- All six tools ran on paid plans: ChatGPT Plus, Google AI Pro and Claude Pro, each the provider's entry-level paid plan, with reasoning effort at maximum (E1, Table 1). Prices are UNKNOWN; the paper gives none.
- Coding agents need the user's own machine, a terminal, a file system, and a browser that carries the user's sessions. Online assistants use the provider's own search tooling. NotebookLM answers only from uploaded documents (E1).
- Find task, barriers named in the paper (E5):
  - Web of Science needs a subscription.
  - Google Scholar showed a CAPTCHA to one agent and stopped the other after 15 results.
  - AMS blocked one agent outright.
  - Wiley serves pre-2005 *Weather* article bodies as scanned images.
- Paired login test (E5): Codex went from 42 to 82 articles; Claude Code went from 15 to 79.
- The paper says the login also got the agents past websites that had blocked them, so subscription and bot-admission effects cannot be separated (E5).
- Interpret, synthesize and propose tasks: the 102 PDFs were supplied, so access was removed from those tasks by design (E4, §2.2).
- Authors' repository at commit `f2f565b`, file `Data/access_barriers/access_status.csv`: 31 PDFs have retrieval route `automatic` and 71 have `manual_import`. The repository README calls this "an observed retrieval route, not a publisher licensing classification".

**DERIVED**
- Share of the 102 articles found:
  - Codex: 42/102 = 41.2% before login, 82/102 = 80.4% after.
  - Claude Code: 15/102 = 14.7% before, 79/102 = 77.5% after.
- Share of each agent's post-login total that appeared only after login:
  - Codex: 40/82 = 48.8%.
  - Claude Code: 64/79 = 81.0%.
- Gap between the two agents: 42 − 15 = 27 articles before login, 82 − 79 = 3 after. So (27 − 3)/27 = 89% of the gap disappeared once access was equalised.
- The 89% figure covers access in the broad sense: subscription plus bot admission, which the paper says it cannot separate. Each agent ran once per condition, and the paper says run-to-run variation was not measured (E7). The 89% is therefore a single-run figure.
- In the closed-corpus tasks, 71/102 = 69.6% of the PDFs reached the tools by manual import. Scores there measure reading and synthesis after a human did most of the access work. They do not show how the tools would perform on that literature unaided.
- Reading: in the find task, most of the measured difference between agents and between conditions follows access. The paper's own heading for §3.4 says the same: "Access, not capability, limited what the tools found".

**PROPOSED**
- Report find-task results as a tool × access-condition table, with per-publisher denominators, rather than as one score per tool.
- Record the cost and subscription state of every run as fields, so a reader can compute an access ceiling per tool.
- Rerun the paired test with the bot-admission and subscription effects separated: login without bot admission, and the reverse.

## C2 Practitioner check: who graded, and whether field users are represented

**OBSERVED**
- Two graders, both coauthors (E3):
  - Reviewer A is the lead author of the benchmark review.
  - Reviewer B is a severe-convection researcher not involved in that review.
- The affiliations listed are university earth/atmospheric-science departments (E3).
- Blinding: tool labels were replaced with Synthesis 1–3, the key was withheld, and citation formatting was standardised (E3).
- Agreement: exact on 24% of 150 ratings, within one point on 67%. Reviewer A scored 0.94 points higher on average, and the two ranked the tools differently. No chance-corrected inter-rater statistic is reported (E3).
- The "usefulness" criterion is defined for "a researcher conducting a review" (E2).
- No grader is described as an operational forecaster, warning-service staff member, or other user of Spanish-plume findings outside research. Grader credentials beyond affiliation are UNKNOWN (E3).

**DERIVED**
- Both scoring positions sit inside research use of the literature. The paper does not say whether the findings would read the same from a position that applies them, such as a forecast desk. That is UNKNOWN, not answered no.
- With exact agreement at 24%, which grader scored matters about as much as which tool wrote the synthesis. Reviewer B's insight scores (2.3–2.5) are flat across tools. Reviewer A's (3.2–4.2) separate them (E2, Table 5 in §5.3).
- "Low insight" rests on two positions, one of them the benchmark's own lead author. The paper states the proximity bias itself (E3).

**PROPOSED**
- Add at least one grader from a position that uses the findings in practice, scored on the same five criteria.
- Have that grader also score "usefulness" against their own task rather than against "a researcher conducting a review".
- Report a chance-corrected agreement statistic per criterion.

## C3 Cyclical baseline: does the 1995–2019 gap remove the multi-decade baseline?

**OBSERVED**
- Corpus span is 1968–2023 (E4).
- Counts by period, quoted (E4): 4 articles before 1995, 71 from 1995–2019, 27 from 2020 onward.
- Without login, the tools found 34/71 = 48% of 1995–2019 articles and 21/27 = 78% of 2020+ articles (E4).
- After login, Codex found a similar share in every period, but Claude Code still found only 39% of pre-2000 articles (§3.4; E5 context).
- Two of the four essential articles are from the thin pre-1995 period: Carlson and Ludlam (1968) and Morris (1986) (§2.1).
- One synthesis described the plume as a warm, moist layer. Several corpus articles describe it that way, but it is inconsistent with the 1968 original definition (E-frame).

**DERIVED**
- The premise "1995–2019 thin" holds for *tool recall* without login. It does not hold for the corpus, where 1995–2019 is the bulk: 71/102 = 69.6%.
- The corpus is thin before 1995: 4 articles over 1968–1994, about 0.15 per year. That compares with 71/25 = 2.84 per year for 1995–2019 and 27/4 = 6.75 per year for 2020–2023.
- The multi-decade baseline in this benchmark is therefore carried by a few anchor articles, not by a period of literature.
- Search task: losing older articles can remove the definitional anchor. The tools found 3 of the 4 essential articles. The one missed was Gray and Marshall (1998), in *Weather* (§3.4).
- Access and age are confounded: Wiley's pre-2005 *Weather* bodies are image-only, and only 2 of 11 pre-2005 *Weather* articles were found (§3.3). So "older" and "unreachable" coincide in this corpus.
- Synthesis task: the baseline was supplied by construction, since all 102 PDFs were given. It was still overridden at least once. The later, more frequent usage ("warm, moist") displaced the 1968 definition. Supplying the baseline did not ensure it was weighted.
- Publication rate rises about 45-fold from the first period to the last (0.15 → 6.75 per year). Any recency weighting in a tool therefore cannot be told apart from literature growth in this benchmark.
- "Cyclical" in the phenomenon sense (multi-decade variation in Spanish-plume events) is not measured. The benchmark is citation-defined, not event-defined. UNKNOWN.

**PROPOSED**
- Score recall separately for definitional-anchor articles, not only by period.
- Rerun synthesis with the corpus split before and after 1995, to see whether the original definition survives as a minority.
- Report per-period recall with the age × access confound as its own row.

## C4 Load withheld / denominator: what is outside the 102 by construction, and does it inflate "consensus"?

**OBSERVED**
- The inclusion rule is peer-reviewed articles containing the exact phrase "Spanish plume", found through four named search routes (E4).
- The language criterion, treatment of non-peer-reviewed sources, and search date are UNKNOWN (E4).
- 84 of the 102 articles mention the plume only in passing (E4). The tools classed 40%–79% of those passing mentions as substantial (§4.3).
- Rule 4 of the synthesis prompt forbids describing consensus "unless the supplied sources demonstrate it". All three tools overstated agreement on Theme 8 (E6).

**DERIVED**
- Outside the denominator by construction:
  - unpublished or non-peer-reviewed material (forecast discussions, operational bulletins, internal reports);
  - any work describing the pattern without the exact English phrase, including other-language terms, whose existence is UNKNOWN here;
  - practitioner knowledge that was never written down.
- The paper's "exaggerated consensus" is measured against the corpus. That makes it a statement about agreement among users of one term in peer-reviewed venues.
- Agreement in the wider field is UNKNOWN in both directions. The excluded material could agree or disagree, and the corpus cannot say which. The selection bounds consensus claims; it does not by itself show them inflated.
- One inflation route is internal to the corpus and visible in the paper's own numbers:
  - 84/102 = 82.4% of articles are passing mentions, which typically restate a standard description.
  - Tools counted 40%–79% of those as substantial.
  - So repeated restatements can be counted as independent agreement.
  - The "warm, moist layer" case (C3) is one instance: a description repeated across several articles and inconsistent with the original definition.
- An agreement count that does not weight passing mentions down inflates apparent consensus inside the denominator. The prompt asked for that weighting (rule 3); whether each tool applied it is not scored separately.

**PROPOSED**
- Every consensus statement should carry its denominator (which articles, classed how) and its selection rule.
- Count agreement on substantial articles only, as its own figure.
- Repeat the search with the phrase criterion relaxed (other-language terms, non-peer-reviewed sources) to measure what the rule excludes. Until then, treat that excluded material as UNKNOWN, not as absent.

## Frame note: what "insight" scores, and would cross-frame reasoning read as "unsupported"?

**OBSERVED**
- "Insight" is one of five criteria "developed jointly", rated 1–5 on agreement. No definition, anchor text or rubric appears in the paper or in the authors' repository at `f2f565b` (E2): UNKNOWN.
- The prompt forbade outside knowledge and web access, and required a corpus source and page for every claim (E-frame).
- Themes 8–9 ask for agreement, disagreement and unsupported assumptions within the corpus (§5.2).
- One of three statement labels, "cross-article synthesis inference", allowed reasoning across articles. It was not defined (E2).
- The authors state that every grounding rule penalised unsupported statements and none rewarded justified interpretation (E2).
- Reviewer A faulted all three syntheses for not recognising that Spain lies on the trajectory path from Africa (E-frame).

**DERIVED**
- What the prompt permits: synthesis inside the field's frame, plus critique of studies within the corpus (themes 8–9, the rule weighting analytical studies). Cross-frame reasoning, meaning a frame or fact from outside the corpus, was excluded by instruction.
- A cross-frame statement would carry no `[SPxxx, PDF p. N]` citation, and under rule 5 the tool should write "Not established". If a tool made one anyway, it would plausibly read as unsupported. How the reviewers would score it on veracity or insight is UNKNOWN, since no rubric text is available.
- Tension, unresolved:
  - What the reviewers looked for as insight included at least one point (the Africa trajectory) whose presence in the corpus is UNKNOWN.
  - If it is not in the corpus, the expected insight needed outside knowledge the prompt forbade.
  - The paper says low insight may "reflect the prompt as much as the tools" (E7).
- Classification: the scored "insight" sits inside the field's frame. Whether cross-frame reasoning would be credited or penalised is UNKNOWN.

**PROPOSED**
- Publish the rubric text with anchors for each criterion.
- Add a prompt arm that permits labelled outside-corpus reasoning, so that cross-frame statements and unsupported ones are scored apart.
