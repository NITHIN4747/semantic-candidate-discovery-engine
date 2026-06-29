## Description

Briefly describe what this PR changes and why.

## Related Issue / Task

Closes #

---

## Checklist

### Sandbox Compliance (mandatory before merge)

- [ ] No `numpy` or `scipy` imports added (`grep -rE "^import numpy|^from numpy" --include="*.py" .` returns clean)
- [ ] No external API calls at rank time (OpenAI, Anthropic, HuggingFace Inference Endpoints)
- [ ] Peak memory stays under 16 GB — streaming JSONL reader in place, no full dataset loads
- [ ] Pipeline completes within 300 seconds on CPU-only hardware

### Code Quality

- [ ] `flake8` passes with no fatal errors
- [ ] `python validate_submission.py submission.csv` outputs `Submission is valid.`
- [ ] Commit message is descriptive and written from the author's perspective

### Infrastructure (if infra scripts were changed)

- [ ] No hardcoded VPC IDs, subnet IDs, or security group IDs — all read from env/params
- [ ] IAM roles follow least-privilege — no `AdministratorAccess` or wildcard `*` actions
- [ ] `IMDSv2` hop limit set to 2 on any new EC2 provisioning

---

## Testing Evidence

Paste the output of `python validate_submission.py submission.csv` here:

```
Submission is valid.
```

Paste the pipeline runtime here (from the final line of `make bench` output):

```
[t]   Total runtime: ___s
```
