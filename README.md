# Vortex OrderGuard

**Check deliveries. Explain discrepancies. Keep owners in control.**

Vortex OrderGuard is a functional MVP for the SDC Hackathon 2026 Domain 2 — Orbyte Smart SME Challenge. It helps micro and small businesses compare purchase orders, receiving records and supplier invoices, surface explainable exceptions, and keep consequential actions behind human approval.

> **Current MVP status:** Core comparison, Trust Gate, human clarification, owner approval/rejection, simulated outbox, activity log, dashboard analytics, demo scenarios and optional DeepSeek extraction are implemented on the `vortex-orderguard-mvp` branch. Replit deployment and competition submission evidence must still be completed by the team.

## Why OrderGuard

Small businesses often reconcile supplier messages, purchase orders, deliveries and invoices manually. A shortage, wrong unit or price change can be missed when records live in different places. OrderGuard turns that repeated checking into one reviewable workflow without allowing AI to make the final business decision.

## Core Journey

1. **Trigger** — staff submits supplier evidence and connected purchasing records.
2. **Connected data** — purchase order, receiving record and invoice are compared together.
3. **Decision logic** — deterministic rules identify quantity, invoice-quantity, price and unit exceptions.
4. **Trust Gate** — a transparent rules-based score shows whether the case is clear, reviewable or blocked.
5. **Human control** — ambiguous units must be clarified by a person; consequential supplier clarification requires owner approval.
6. **Visible outcome** — approved clarification enters a simulated outbox and every step is recorded in the audit trail.

## Innovation: OrderGuard Trust Gate

The Trust Gate is a reusable safety layer between automation and action.

- `CLEAR` — records match; no supplier action is needed.
- `REVIEW` — records are comparable but discrepancies require owner review.
- `BLOCKED` — data is ambiguous or incompatible, so approval is disabled until a person clarifies it.

The Trust Gate score is a deterministic heuristic, **not an AI confidence probability**. This makes the reasoning easy to explain to judges and keeps the owner in control.

## Judge Demo Scenarios

The dashboard includes three one-click synthetic scenarios:

| Scenario | What it demonstrates |
| --- | --- |
| Discrepancy | 10 kg chicken ordered at RM12/kg, 8 kg received, invoice at RM13/kg |
| Ambiguous unit | PO/invoice use kg while receiving says “bags”; Trust Gate blocks approval |
| Clean match | Connected records match and the system avoids unnecessary follow-up |

For the ambiguous-unit case, confirm the receiving quantity/unit to demonstrate **blocked → human clarification → recalculation → owner review**.

## Implemented MVP Features

- Evidence-linked quantity and price discrepancy detection
- Invoice quantity checks
- Human clarification for incompatible/missing units
- Explainable Trust Gate with `CLEAR`, `REVIEW` and `BLOCKED` states
- Owner-only approval/rejection for consequential actions
- Duplicate-approval protection using a unique outbox case constraint
- Simulated supplier outbox (no real messages/payments)
- Activity/audit history
- Dashboard case metrics and exception pulse
- Three one-click judge demo scenarios
- Optional DeepSeek supplier-message extraction
- Manual fallback when AI is unavailable
- Human confirmation of AI-extracted fields before rule evaluation
- SQLite demonstration storage
- Responsive Flask/Bootstrap UI

## AI Design

AI is used only where it adds value: converting informal supplier text into structured suggestions such as item, quantity, unit and price. It does **not** calculate discrepancies, approve actions, infer unit conversions or send supplier messages.

The application currently supports DeepSeek through `DEEPSEEK_API_KEY`. If no key is configured, users continue with the manual structured fields.

## Architecture

```text
Supplier message / records
          |
          v
Flask web UI ---- optional DeepSeek extraction
          |
          v
Human-confirmed structured fields
          |
          v
Deterministic discrepancy engine
          |
          v
OrderGuard Trust Gate
      /        \
 BLOCKED      REVIEW
    |            |
Human clarify  Owner approve/reject
    |            |
    +--> Recalculate
                 |
                 v
       Simulated outbox + audit log
                 |
              SQLite
```

## Run Locally / Replit

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python src/main.py
```

Then open the URL provided by Replit, or locally open `http://127.0.0.1:5000`.

### Replit Secrets

Do not commit real keys. Configure these through Replit Secrets when used:

```text
DEEPSEEK_API_KEY=...
FLASK_SECRET_KEY=...
```

Optional:

```text
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_API_URL=https://api.deepseek.com/chat/completions
```

## Tests

Run:

```bash
python -m unittest discover -s tests -v
```

Coverage includes matching records, quantity/price discrepancies, ambiguous units, Trust Gate blocking, human clarification, owner-only approval, rejection, and duplicate-action protection.

## Safety and Competition Boundaries

- Synthetic demo business data only
- No real payment processing
- No statutory filing
- No legal or financial advice
- No live WhatsApp/Orbyte integration claimed
- Roles and Orbyte interfaces are simulated for the MVP
- No API keys or credentials should be committed
- RunPod is only required if the team uses GPU training, fine-tuning or GPU inference

## Orbyte Fit

OrderGuard is designed as a reusable purchasing-exception module within a shared business hub. In a production Orbyte integration, upstream services could provide purchase orders, supplier records and role information, while OrderGuard would return discrepancy cases, approval decisions and audit events. The MVP uses team-created interface assumptions and does not claim access to live Orbyte APIs.

## Validation Still Required

The team still needs to complete real SME problem validation and measure a defensible baseline/KPI for the official preliminary proposal. Do not present estimated time savings as measured results.

Suggested measurements:

- Manual check time vs prototype check time
- Known discrepancy detection rate
- False-alert count on matching records
- First-time-user task completion
- Approval-control and duplicate-action tests

## Submission Status

Still required before the preliminary deadline:

- Complete official `SDC2026_Vortex_Preliminary.pdf`
- Complete `SDC2026_Vortex_TechDeclaration.pdf`
- Deploy through the team's Replit account and retain proof of use
- Add the official Replit/live prototype link
- Prepare pitch deck
- Record 5–7 minute YouTube pitch with prototype demo
- Verify team details, workshop completion, eligibility and declarations
- Verify all public links in an incognito window

See `docs/VORTEX_SUBMISSION_GUIDE.md` for the detailed requirement mapping.

## Technical & AI Disclosure

The project has used ChatGPT for substantial ideation, documentation and development assistance and this must be disclosed accurately in the Technical & Tools Declaration. The team remains responsible for reviewing, understanding, testing and adapting all generated material. The competition requires the team's own problem framing, solution decisions and explainability; the team should validate the SME problem and document its own decisions before submission.

This repository is based on the official SDC Hackathon Submission Template and retains its Apache License 2.0.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
