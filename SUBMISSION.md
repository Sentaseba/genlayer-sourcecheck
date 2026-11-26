# Portal contribution submission — prepared text (placeholders filled after deploy)

**Title:** SourceCheck — an on-chain claim-verification oracle

**Project / repo:** https://github.com/Sentaseba/genlayer-sourcecheck

**Contract (Studionet / GenLayer Studio):** 0x5810642d5914FA8f56EE6a27d0D8dA01Ec034C6E
**Explorer:** https://explorer-studio.genlayer.com/address/0x5810642d5914FA8f56EE6a27d0D8dA01Ec034C6E
**Deployment tx:** 0xac9f600f43ec9cb06d98e4c3866a5cfa2abb6a4c0b2c595b361a377ad59e09b7

**Description:**
SourceCheck is an Intelligent Contract that fact-checks a claim against a
cited web source and stores the verdict on-chain. A user submits a claim and
a source URL; the contract fetches the page as text and prompts an LLM to
classify the claim as SUPPORTED, CONTRADICTED, or UNMENTIONED, with a
one-sentence reason grounded in the source. Validators re-run the evaluation
and accept only when their own verdict category matches the leader's and the
payload is well-formed — the Equivalence Principle applied to verdicts, not
wording. Finalized records (claim, source, submitter, verdict, reason) are
stored in a TreeMap and readable by anyone via get_check.

**What was built:**
- Full Intelligent Contract in Python (GenVM, py-genlayer) using native web
  access and LLM calls — no external oracles.
- Deliberate consensus design: category-level equivalence, strict payload
  validation, leader rotation on disagreement.
- Deployed and exercised end-to-end on Studionet: a real check against
  example.org reached consensus with verdict SUPPORTED
  (submit tx 0x07c60ab33584db41f7f349a9365d574762f6773c1fb64fa2e589709e9728cdf9;
  get_total_checks 0 → 1; get_check(0) returns the stored record).
- Documented repo: contract source, interface table, demo results, design
  notes and limitations, MIT license.
