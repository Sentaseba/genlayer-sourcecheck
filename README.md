# SourceCheck — On-Chain Claim Verification Oracle

An [Intelligent Contract](https://docs.genlayer.com/developers/intelligent-contracts/introduction)
for [GenLayer](https://www.genlayer.com/) that fact-checks a claim against a
web source and stores the verdict on-chain.

Anyone can submit a factual claim together with the URL of a source that is
supposed to settle it. The contract fetches the source page, asks an LLM
whether the page **supports** the claim, **contradicts** it, or does not
mention it at all, and records the verdict — reached by validator consensus —
in contract storage, where anyone can read it back.

## Why GenLayer?

A normal smart contract cannot read a web page or judge natural language.
SourceCheck needs both, plus a neutral way to agree on a subjective result.
GenLayer's Optimistic Democracy and Equivalence Principle provide exactly
that: validators independently re-run the evaluation and vote on whether the
leader's verdict is acceptable.

## How it works

1. `submit_check(claim, source_url)` is called.
2. In a non-deterministic block, the contract:
   - fetches the source page as text (`gl.nondet.web.render(..., mode="text")`,
     truncated to 6,000 characters),
   - prompts an LLM (`gl.nondet.exec_prompt(..., response_format="json")`) to
     classify the claim as `SUPPORTED`, `CONTRADICTED`, or `UNMENTIONED`,
     with a one-sentence reason grounded in the source text.
3. Validators re-run the same evaluation. They accept the leader's result
   only if:
   - the payload is well-formed (valid verdict + non-empty reason), **and**
   - their own verdict category matches the leader's exactly.
4. On consensus, the full record (claim, source URL, submitter, verdict,
   reason) is stored under a sequential id.

Free-text reasons are never compared across validators — only the verdict
category must match. That is the Equivalence Principle applied deliberately:
LLM wording differs between runs, verdicts on a clear source should not.

## Contract interface

| Method | Type | Description |
| --- | --- | --- |
| `submit_check(claim: str, source_url: str) -> u256` | write | Runs a verification and stores the record. Returns the check id. |
| `get_check(check_id: u256) -> str` | view | Returns the stored record as a JSON string. |
| `get_total_checks() -> u256` | view | Returns how many checks have been finalized. |

Stored record (the actual first record stored by the deployed contract):

```json
{"id": 0, "claim": "This domain is for use in documentation examples", "source_url": "https://example.org", "submitter": "0xC49F47292a0e8FeD4c83e34f2162434fEd678456", "verdict": "SUPPORTED", "reason": "The source states, \"This domain is for use in documentation examples without needing permission.\""}
```

## Demo (GenLayer Studio / Studionet)

- Contract: [`contracts/sourcecheck_v3.py`](contracts/sourcecheck_v3.py)
  (pinned runner `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`,
  the runner documented in the official GenVM SDK v0.3.x docs)
- Deployed address: `0x5810642d5914FA8f56EE6a27d0D8dA01Ec034C6E`
- Explorer: https://explorer-studio.genlayer.com/address/0x5810642d5914FA8f56EE6a27d0D8dA01Ec034C6E
- Deployment transaction: `0xac9f600f43ec9cb06d98e4c3866a5cfa2abb6a4c0b2c595b361a377ad59e09b7`
  (consensus ACCEPTED)
- Deployed from (CLI account): `0xc49f47292a0e8fed4c83e34f2162434fed678456`
- Verification sequence, all read back from the deployed contract:
  - `get_total_checks()` → `0`
  - `submit_check("This domain is for use in documentation examples", "https://example.org")`
    → tx `0x07c60ab33584db41f7f349a9365d574762f6773c1fb64fa2e589709e9728cdf9` (consensus ACCEPTED)
  - `get_total_checks()` → `1`
  - `get_check(0)` → the stored record shown above (verdict `SUPPORTED`)

## Run it yourself

1. Open [GenLayer Studio](https://studio.genlayer.com/).
2. Create a new contract file and paste the contents of
   `contracts/sourcecheck_v3.py`.
3. Fund the Studio account with the built-in faucet button if needed, then
   deploy (the constructor takes no arguments).
4. Call `submit_check` with a claim and a source URL, wait for consensus,
   then read the verdict with `get_check(0)`.

## Design notes & limitations

- **Source-bound judging.** The LLM is instructed to judge *only* from the
  fetched page text and to answer `UNMENTIONED` when the evidence is weak —
  the contract verifies claims against a cited source, it is not a general
  truth oracle.
- **Page volatility.** If a page changes between the leader's and a
  validator's fetch, verdicts can diverge and the transaction rotates to a
  new leader instead of finalizing — by design.
- **Truncation.** Only the first 6,000 characters of a page are judged, so
  claims about content deep inside very long pages may read as
  `UNMENTIONED`.
- **No value handling.** The contract is free to call, holds no funds, and
  has no admin or upgrade mechanism.

## License

MIT
