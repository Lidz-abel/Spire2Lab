# RL environment: E0 readiness

Checked 2026-11-15. E0 server readiness passed; E1 training design and E2 game-policy
training have not started. Windows installation/tunnel and original single-act
acceptance are separate, still pending requirements.

## Workspace and isolation

The current checkout is `/user/chenzk/sts2/sts2-lab-phase2`, branch
`phase2/search-hierarchy`. `git worktree repair` repaired its two-way links to the
shared metadata in `/user/chenzk/sts2/sts2-lab/.git`. The main checkout remains at
`f9faf0a`; its tracked source diff is empty and its before/after installed-package
lists match. The old reproduction worktree registration remains at a stale path;
it was not pruned or used for this check.

The new project-local `.venv-rl/` is ignored by Git. `.venv` now links to `.venv-rl`,
so existing commands use the isolated phase-two environment. No training dependency
was installed into the first-stage venv or system Python. `.tools/vendor-archives`,
`dotnet`, `powershell` and `browsers` are relative links to the existing sibling
checkout's tools; their contents were not rebuilt or edited. Native code, game
references and the prepared Windows Mod remain at their previous fingerprints.

Do not run the legacy `scripts/bootstrap.py` against this ready RL environment:
it synchronizes the base-only lock and may remove training packages. Use the
separate [RL lock](../requirements-rl.lock). Dependency updates must be explicit.

## Dependencies and installation provenance

The tested stack is Python 3.12.3, NumPy 2.5.4, Gymnasium 1.4.0 and PyTorch 2.14.0
with CUDA runtime 13.0. `pip check` passed. The RL version lock includes every
installed distribution via the unchanged base lock plus explicit additions.

Official version/platform combinations were checked against the
[PyTorch installation table](https://pytorch.org/get-started/previous-versions/).
The host's configured HTTPS proxy failed TLS connections to both package sources;
direct connections could not resolve DNS. The first offline attempt also lacked
registry metadata for cached `uv`. Recovery used unchanged local pip wheels and
the uv cache, installed with `--link-mode copy`. One missing wheel, setuptools
78.1.0, was recovered from another existing same-host environment after verifying
514 hashed files against its installed wheel RECORD. Source environments were
not changed. Local wheel hashes and the recovery scripts are retained privately.

This is a same-host dependency recovery, not a fresh independent installation.
Wheel/RECORD consistency does not establish a publisher signature. A future
networked installation can use the version lock and rerun the checks; independent
reproduction remains a separate deliverable.

```bash
# From the checkout, on a new machine with working package access:
python3.12 -m venv .venv-rl
.venv-rl/bin/python -m pip install -r requirements-rl.lock
.venv-rl/bin/python -m pip check
```

This installs Python dependencies only. The pinned source archives and native
build must also be restored/verified; do not substitute unverified game binaries.

## GPU choice and bounded checks

The host reports four RTX 4090-labelled devices with approximately 48 GiB each,
128 logical CPUs and 377 GiB RAM. These are observed host totals, not an exclusive
allocation or a claim about the retail card specification. GPU 0 reports errors
and is excluded. Only physical GPU 1 was tested with a small numerical workload;
GPUs 2–3 were visible in telemetry, not compute-validated. No reset, driver update
or multi-GPU job was performed. Long-running resource quotas remain to be agreed.

Choose a currently verified GPU UUID before running the optional CUDA check:

```bash
nvidia-smi --query-gpu=index,uuid,name,memory.used,utilization.gpu --format=csv
# Set CUDA_VISIBLE_DEVICES to ONE healthy device UUID from the above output.
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  .venv-rl/bin/python -B scripts/check_rl_environment.py --cuda \
  --output artifacts/rl-mvp/environment/NEW_CHECK_ID/readiness.json
```

The CUDA checker requires an explicit single-device selection. Omitting `--cuda`
performs only the CPU/native check. Use a new output directory to retain prior
evidence. Site caches can be scoped with `CUDA_CACHE_PATH` and
`TORCHINDUCTOR_CACHE_DIR` under ignored `.tools/rl-runtime-cache/`.

## Evidence and scope

Private evidence: `artifacts/rl-mvp/environment/e0-20261115/`.

- `readiness-attempt1.json`: source checks for 1,383 simulator files and 34 Mod
  source files; native SHA-256 `6321ca69c3ac6024d069f00b683d698523d8b22819609ee0044f078492856131`.
- CPU and selected-GPU forward/backward/Adam checks passed with finite gradients
  and changed weights; NumPy/PyTorch interchange passed. These use synthetic
  numeric inputs and are not game-agent learning results.
- Three heuristic starter battles at development seed 1 completed: Nibbit 11
  actions / 74 HP, Slimes 19 / 80 HP, Sludge Spinner 9 / 77 HP. Each was repeated
  once with matching public encoded trajectories. This is six simulator runs,
  three distinct cases, not six new original-game validations.
- `regression.xml`: 65 related tests passed, covering environment lifecycle,
  training transitions, vocabulary, source integrity, planning and sampling.
  Sampling tests include single/two-worker trajectory consistency and cleanup
  after success, worker errors and startup timeouts.
- `installed-packages.txt`, `pip-inspect.json`, `cached-wheels.json` and
  `setuptools-restore.json` record installation identity and provenance.
- `backups/` retains prior Git metadata and symlink values. Network, offline
  dependency-resolution and wheel-tag recovery failures are retained in logs.

No dashboard or background trainer was started, and no game commands were sent.
This report does not change the outstanding original-game single-act acceptance.
