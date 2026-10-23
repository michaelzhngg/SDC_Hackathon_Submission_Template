# Vortex OrderGuard — Pitch Deck Content

Use this as the content source for the preliminary pitch deck. Keep any measured-impact numbers honest: replace placeholders only after the team has actually timed or tested the prototype.

## Slide 1 — Vortex OrderGuard

**Catch supplier discrepancies before they become expensive mistakes.**

Domain 2 — Orbyte Smart SME Challenge: Less Busywork, Better Business

One-line pitch:

> Vortex OrderGuard turns scattered supplier messages, purchase orders, receiving records and invoices into one explainable exception workflow, while keeping SME owners in control of every consequential action.

Suggested visual: OrderGuard dashboard with the Money at Risk and Trust Gate cards visible.

## Slide 2 — The SME Problem

Malaysian micro and small businesses may still check purchasing records manually across WhatsApp-style messages, spreadsheets, paper receiving notes and supplier invoices.

A staff member may need to answer questions such as:

- Did the delivered quantity match the purchase order?
- Did the invoice use the agreed unit price?
- Are the units actually comparable?
- Has this supplier-item combination had the same issue before?
- Who is allowed to approve the follow-up?

The problem is not only data entry. The recurring burden is **manual cross-checking, repeated follow-up and inconsistent exception handling**.

Do not claim interview or market-validation results until the team has actually collected them.

## Slide 3 — Our Solution

OrderGuard focuses on one complete SME workflow:

**Trigger → Connected records → Decision logic → Supplier pattern memory → Trust Gate → Human approval → Logged outcome**

The prototype currently supports:

- Purchase order, receiving and invoice comparison
- Quantity and unit-price discrepancy detection
- AI-assisted extraction from informal supplier messages
- Human confirmation of AI suggestions
- Trust Gate for ambiguous or unsafe-to-act data
- Owner-only approval/rejection
- Duplicate-action protection
- Simulated supplier outbox
- Activity/audit trail
- Repeat-issue detection for the same supplier and item
- Money at Risk visibility
- Supplier Exception Radar

## Slide 4 — What Makes It Different

### 1. AI where it adds value
AI helps transform informal supplier text into structured suggestions. It does not decide payments, calculate discrepancies or approve actions.

### 2. Deterministic financial checks
Quantity, unit and price comparisons use transparent program rules that can be explained from the source records.

### 3. Trust Gate
When inputs are not safely comparable, such as `2 bags` versus `10 kg`, OrderGuard blocks approval instead of guessing a conversion.

### 4. Supplier Pattern Memory
OrderGuard remembers recurring exception types for the same supplier and item, helping the owner notice repeated operational issues without automatically blacklisting the supplier.

### 5. Money at Risk
Open discrepancies are translated into a visible RM comparison amount so the owner can prioritize review. This is a review indicator, not a payment instruction or final amount owed.

## Slide 5 — Live Demo Story

### Demo 1: Discrepancy
FreshFarm Foods:

- PO: Chicken, 10 kg at RM12/kg
- Received: 8 kg
- Invoice: 10 kg at RM13/kg

OrderGuard flags quantity and price discrepancies and shows a RM34 comparison difference.

### Demo 2: Repeat Issue
Run the same supplier + item pattern again.

OrderGuard shows **Repeat issue detected** and displays prior exception context in the Supplier Exception Radar.

### Demo 3: Ambiguous Unit
RiceHub Supply:

- PO: 10 kg
- Receiving record: 2 bags

Trust Gate blocks the workflow. A human confirms the receiving record before recalculation and any approval.

### Demo 4: Clean Match
Golden Egg Trading:

- 30 trays ordered
- 30 trays received
- 30 trays invoiced at the agreed price

OrderGuard takes no unnecessary consequential action.

## Slide 6 — Architecture

```text
Supplier message / staff input
            |
            v
Optional AI extraction (DeepSeek)
            |
            v
Human-confirmed structured fields
            |
            v
PO + Receiving + Invoice
            |
            v
Deterministic discrepancy engine
            |
            +--> Trust Gate
            |
            +--> Supplier Pattern Memory
            |
            +--> Money at Risk / Exception Radar
            |
            v
Owner approve / reject
            |
            v
Simulated outbox + audit log
```

Prototype stack:

- Python
- Flask
- SQLite
- Bootstrap
- DeepSeek API for optional structured extraction
- Replit target for compulsory competition development/deployment evidence
- GitHub for version history and tests

No live Orbyte API is required for the prototype; integration is represented through reusable purchasing and role interfaces.

## Slide 7 — Human Control, Safety and Reliability

OrderGuard is intentionally not a fully autonomous financial agent.

- Staff may submit records.
- Consequential supplier clarification requires owner approval.
- Ambiguous units block approval.
- AI output must be human-confirmed.
- Repeated approval does not create duplicate outbox actions.
- Rejection creates no supplier action.
- Activity history records the workflow.
- The prototype sends no real payment and no real supplier message.
- Synthetic demo data is used.

Automated tests cover core discrepancy, Trust Gate, approval, duplicate-action and supplier-intelligence behavior.

## Slide 8 — Orbyte Fit and Reusability

OrderGuard can fit into Orbyte as a reusable purchasing-exception module.

Potential input interfaces:

- Purchase orders
- Supplier records
- Receiving records
- Invoice data
- User/role information

Potential output interfaces:

- Exception case
- Approval/rejection decision
- Clarification request
- Audit/activity event

The same core engine could be configured for restaurants, retailers, small wholesalers and other SMEs without rebuilding the entire approval workflow.

## Slide 9 — Business Impact and SDG

Primary SDG: **SDG 8 — Decent Work and Economic Growth**

Relevant direction:

- Improve SME operational productivity through digital workflow automation.
- Help micro and small enterprises reduce repetitive manual checking.

### KPI to measure before submission

Recommended primary KPI:

**Average time required to check one supplier order/receiving/invoice case.**

Team action:

1. Time the same synthetic cases manually.
2. Time them using OrderGuard.
3. Report the actual baseline and percentage difference.

Do not place an invented percentage on this slide. Insert the measured value only after testing.

Secondary measurements can include discrepancy-detection accuracy, unnecessary alerts, owner-control tests and time required for a new tester to learn the workflow.

## Slide 10 — Why Vortex OrderGuard

Closing message:

> Small businesses do not need another chatbot that tells them what might be wrong. They need a reliable workflow that connects the evidence, explains the exception, remembers repeated issues and still lets the owner make the final decision.

**Vortex OrderGuard: Check. Explain. Remember. Approve.**

End the pitch by returning to the live dashboard and showing the Supplier Exception Radar, Trust Gate and activity log together.
