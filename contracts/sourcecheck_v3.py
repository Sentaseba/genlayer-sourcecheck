# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

# Always put the above line first in the contract file
# In actual genlayer network `:latest` is not allowed and hash must be specified

# `from genlayer import *` brings `gl` itself, the type aliases (u256, ...)
# and the storage types (TreeMap, ...) into scope — the official import style
from genlayer import *

import json

VERDICTS = ("SUPPORTED", "CONTRADICTED", "UNMENTIONED")
MAX_PAGE_CHARS = 6000


class SourceCheck(gl.Contract):
    total_checks: u256
    checks: TreeMap[u256, str]

    def __init__(self):
        self.total_checks = u256(0)

    def _evaluate(self, claim: str, source_url: str) -> dict:
        page_text = gl.nondet.web.render(source_url, mode="text")
        if page_text is None:
            raise gl.vm.UserError("Could not fetch the source page")
        page_text = str(page_text)[:MAX_PAGE_CHARS]
        if len(page_text.strip()) == 0:
            raise gl.vm.UserError("Source page returned no readable text")

        prompt = f"""
You are a strict fact-checking judge. You are given a CLAIM and the text of a
SOURCE web page. Decide what the source says about the claim.

Rules:
- Answer "SUPPORTED" only if the source page clearly states or implies the
  claim is true.
- Answer "CONTRADICTED" only if the source page clearly states or implies
  the claim is false.
- Answer "UNMENTIONED" if the source page does not address the claim, or the
  evidence is too weak or ambiguous to decide.
- Judge ONLY from the source text below. Do not use outside knowledge.
- The reason must be one short sentence quoting or paraphrasing the relevant
  part of the source.

Return a JSON object with exactly these keys:
- "verdict": one of "SUPPORTED", "CONTRADICTED", "UNMENTIONED"
- "reason": one short sentence

CLAIM:
{claim}

SOURCE TEXT:
{page_text}
"""
        result = gl.nondet.exec_prompt(prompt, response_format="json")
        if not isinstance(result, dict):
            raise gl.vm.UserError("LLM returned a non-object response")

        verdict = str(result.get("verdict", "")).strip().upper()
        reason = str(result.get("reason", "")).strip()
        if verdict not in VERDICTS:
            raise gl.vm.UserError(f"LLM returned an invalid verdict: {verdict}")
        if len(reason) == 0:
            raise gl.vm.UserError("LLM returned an empty reason")

        return {"verdict": verdict, "reason": reason}

    @gl.public.write
    def submit_check(self, claim: str, source_url: str) -> u256:
        claim = claim.strip()
        source_url = source_url.strip()
        if len(claim) == 0:
            raise gl.vm.UserError("Claim must not be empty")
        if not (source_url.startswith("https://") or source_url.startswith("http://")):
            raise gl.vm.UserError("Source URL must start with http:// or https://")

        def leader_fn() -> dict:
            return self._evaluate(claim, source_url)

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            data = leader_result.calldata
            if not isinstance(data, dict):
                return False
            if data.get("verdict") not in VERDICTS:
                return False
            if not isinstance(data.get("reason"), str) or len(data["reason"].strip()) == 0:
                return False
            try:
                my_result = self._evaluate(claim, source_url)
            except Exception:
                return False
            return my_result["verdict"] == data["verdict"]

        outcome = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        check_id = self.total_checks
        record = {
            "id": int(check_id),
            "claim": claim,
            "source_url": source_url,
            "submitter": str(gl.message.sender_address),
            "verdict": outcome["verdict"],
            "reason": outcome["reason"],
        }
        self.checks[check_id] = json.dumps(record)
        self.total_checks = check_id + u256(1)
        return check_id

    @gl.public.view
    def get_check(self, check_id: u256) -> str:
        if check_id >= self.total_checks:
            raise gl.vm.UserError("Unknown check id")
        return self.checks[check_id]

    @gl.public.view
    def get_total_checks(self) -> u256:
        return self.total_checks
