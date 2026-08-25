# AIC Preliminary Submission Checklist

Status date: 25 August 2026. This file separates verified repository work from external submission tasks. A checked box means evidence exists in this repository or was executed locally.

## Product and code

- [x] Original Lumbung MVP is scoped to Smart Commerce inventory replenishment.
- [x] One user input produces one synchronous AI recommendation output.
- [x] Fine-tuned quantile model and static inference parameters are versioned.
- [x] Temporal validation, baseline comparison, and limitations are documented.
- [x] Frontend, backend, and model concerns are modular.
- [x] `docker compose up --build` is the documented local entry point.
- [x] Invalid schema, missing values, MOQ, budget, deterministic inference, health, upload contract, and file type have automated tests.
- [x] Setup, schema, architecture, API docs, model card, and limitations are documented.
- [x] Git commits use Conventional Commits.
- [x] No educational institution identity appears in the product interface.

## Validation evidence

- [x] Backend tests pass locally.
- [x] Frontend production build passes locally.
- [x] Python lint passes locally.
- [x] Release verifier confirms model/data hash, acceptance gate, deterministic sample output, budget, MOQ, required files, and Conventional Commits.
- [ ] Clean Docker Compose build and browser-to-backend smoke test pass on the final commit.
- [ ] Proof-of-work recording repeats the clean Docker run without cut.

## External deliverables requiring team action

- [ ] Repository visibility changed to **public** only when the team authorizes the final push.
- [ ] Final local commits pushed to the approved GitHub repository before 25 August 2026, 23:55 WIB.
- [ ] Public repository link entered on the COMPFEST site.
- [ ] Proof-of-work video, maximum 7 minutes, unlisted YouTube, double screen with terminal and application, visible timestamp, no cuts, correct title.
- [ ] Promotional video, maximum 5 minutes, minimum 720p, public YouTube, correct title.
- [ ] Proposal PDF, maximum 20 counted pages excluding permitted front/back matter, includes name, background, objective, dataset/model/integration methodology, and conclusion.
- [ ] All video and proposal claims reconciled against `artifacts/model_metadata.json`; synthetic metrics are not presented as field results.
- [ ] No educational institution background shown in repository materials, videos, proposal, or demo.
- [ ] Submission completed on the COMPFEST site and confirmation captured.
- [ ] Team remains available on Discord on 9 and 10 September 2026 at 20:00 WIB.

## Proof-of-work recording sequence

1. Show the current timestamp and repository commit.
2. Run `docker compose down --remove-orphans` if an earlier demo is active.
3. Run `docker compose up --build` with terminal and application visible together.
4. Wait for both containers to become healthy.
5. Open `http://localhost:3000`.
6. Download the sample, upload it unchanged, and generate recommendations.
7. Show budget feasibility, MOQ quantities, numeric reasons, audit checksum, and CSV download.
8. Show `http://localhost:8000/docs` and `docker compose ps`.
9. If reducing waiting time, use fast-forward only; do not cut the recording.
