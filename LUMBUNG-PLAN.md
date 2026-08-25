# Lumbung Product and Technical Plan

## 1. Product definition

Lumbung is an AI procurement copilot that sits above a retailer's POS and inventory records. It is not intended to replace the full store-management system. The POS remains the source of truth for transactions, stock, receiving, and product records. Lumbung adds the decision and execution layer for replenishment.

The product promise is specific:

> Help an owner decide what to buy, how much to buy, from which supplier, at what expected price, and when it should arrive, while keeping the owner in control of every order.

The initial customer is a growing independent grocery retailer with digital sales records, current inventory, several suppliers, and limited working capital. A practical pilot requires at least three to six months of usable transaction history. This is a screening requirement, not a claim about the wider retail market.

## 2. End-to-end operating model

```text
POS sales and stock
  -> demand forecast and stockout risk
  -> budget-constrained purchase proposal
  -> owner review and approval
  -> purchase-order draft
  -> supplier message through an approved connector
  -> supplier price and delivery confirmation
  -> receiving and stock update in the POS
  -> actual lead-time and fulfillment feedback
```

The approval screen should show editable quantity, supplier, quoted or estimated unit price, total cost, requested arrival date, confidence, and the numeric reason for each recommendation. The system may prepare and send an order only after explicit owner approval.

## 3. Scope by stage

| Capability | Preliminary MVP in this repository | Final-stage product target | Post-competition product |
|---|---|---|---|
| Data intake | One validated CSV upload | CSV plus one POS import adapter | Scheduled multi-POS synchronization |
| Forecasting | LightGBM P50 and P90 demand | Retrained on authorized pilot data | Per-store monitoring and recalibration |
| Purchase decision | MOQ and budget optimizer | Editable proposal grouped by supplier | Multi-supplier price, reliability, and cash-flow optimization |
| Approval | Editable browser simulation with explicit owner confirmation | Persisted approval with audit trail | Role-based approval thresholds |
| Purchase order | Downloadable local draft after approval | Persisted, supplier-grouped PO | Versioned PO and receiving reconciliation |
| Supplier contact | Message preview and simulated local status | Telegram sandbox or copy-to-chat workflow | Approved Telegram and WhatsApp Business connectors |
| Supplier response | Not included | Manual confirmation capture | Structured reply parsing and exception queue |
| Inventory system | Existing POS remains external | Read from one POS and export receiving updates | Two-way adapters with conflict handling |

The preliminary prototype keeps the core AI interaction to one CSV upload and one synchronous result. Review and approval run in browser memory after inference. The prototype labels supplier records and sending status as simulations. It includes no authentication, database, background job, POS adapter, or messaging connector. The final product should prove the closed replenishment loop through integration, persisted approval, supplier communication, and receiving.

## 4. Current core inference

The current pipeline accepts:

```text
date, sku_id, category, sales_qty, stock_on_hand, on_order,
unit_cost, unit_margin, lead_time_days, moq, available_budget
```

It then:

1. validates the schema and business rules;
2. builds lagged, rolling, intermittency, calendar, and commercial features without future leakage;
3. predicts P50 and P90 demand over lead time plus a seven-day review period;
4. calculates target stock after stock on hand and on-order units;
5. rounds requirements to MOQ bundles;
6. chooses a deterministic set of bundles that cannot exceed the input budget;
7. returns reasons, model version, data cutoff, and input checksum.

The optimizer, not a language model, controls quantity and budget feasibility.

## 5. Evidence boundary

The checked-in model uses deterministic synthetic data: 3,520 rows, 16 SKU series, and 220 days. Hyperparameters were selected with two expanding temporal validation folds. The untouched temporal holdout contains 432 examples.

| Metric | Model | Moving-average baseline |
|---|---:|---:|
| Mean P50/P90 pinball loss | 1.786392 | 1.828699 |
| P50 WAPE | 0.200564 | 0.205738 |
| P90 empirical coverage | 0.891204 | Not applicable |

This supports a narrow claim: the supplied model passed its predefined software acceptance gate on synthetic data. It does not prove impact, field accuracy, adoption, savings, or suitability for an Indonesian retailer. Those claims require authorized POS data and a prospective pilot.

## 6. Target architecture

Keep the system modular so each integration can change independently:

```text
POS adapter ----> normalized retail events ----> feature and forecast service
                                                   |
supplier data --> supplier registry --------------> purchase optimizer
                                                   |
                                                   v
owner UI <---- proposal and approval API <---- order workflow
                                                   |
                                                   v
                                      connector outbox and audit log
                                                   |
                                      Telegram or WhatsApp Business
```

Recommended boundaries:

- **POS adapters** map sales, inventory, products, suppliers, purchase orders, and receiving into a stable internal schema.
- **Forecast service** produces demand distributions and uncertainty metadata.
- **Purchase optimizer** applies stock, MOQ, budget, price, lead-time, and supplier constraints.
- **Order workflow** owns approvals, idempotency, status transitions, and audit events.
- **Connector outbox** handles retries and channel failures without duplicating orders.
- **Owner UI** exposes evidence, editable fields, and explicit approval.

A database and background worker become necessary when the system adds saved proposals, integrations, message retries, or receiving. They are intentionally absent from the synchronous preliminary MVP.

## 7. Order workflow and safeguards

Use an explicit state machine:

```text
NEEDS_REVIEW
  -> APPROVED
  -> PO_DRAFTED
  -> SENT
  -> SUPPLIER_CONFIRMED
  -> ETA_CONFIRMED
  -> RECEIVED

Any active state may move to CANCELLED through an authorized action.
```

Required controls:

- No transition to `SENT` without recorded human approval.
- Approval stores the user, timestamp, model version, input checksum, and final edited values.
- Sending is idempotent so retries cannot create duplicate orders.
- A changed price, unavailable quantity, substituted item, or changed arrival date returns to an exception review.
- Supplier replies never update stock directly. Receiving must be confirmed against delivered goods.
- Credentials remain outside Git and are scoped per connector and store.
- Every automated action has a manual fallback, including copying a prepared message.

An LLM is optional for drafting natural supplier messages or extracting proposed price and ETA from replies. It must not forecast demand, set the budget, approve an order, silently accept substitutions, or execute a payment. Parsed replies remain untrusted until validated and confirmed.

## 8. Delivery roadmap

### Stage A: stabilize the preliminary handover

- Complete one clean `docker compose up --build` run on a healthy Docker host.
- Repeat the sample upload through the containerized frontend proxy.
- Confirm both health checks, recommendation values, CSV download, and API documentation.
- Record the final tested commit and Docker versions.

### Stage B: validate real data readiness

- Interview owners and document how purchase decisions are currently made.
- Audit three to six months of authorized POS data for missing dates, stockouts, returns, cancellations, price changes, and stock adjustments.
- Establish moving-average and current-store-policy baselines before retraining.
- Measure forecast calibration, stockout-risk ranking, recommendation acceptance, edits, and planning time.

### Stage C: close the approval loop

- Add store, supplier, product, proposal, approval, order, and audit tables.
- Build the editable approval popup and supplier-grouped proposal.
- Generate a versioned purchase-order draft.
- Implement a transactional outbox and idempotency key.

### Stage D: prove one integration path

- Build one POS import adapter with documented field mapping.
- Add a Telegram sandbox or manual share workflow first.
- Capture supplier price, available quantity, and ETA as structured confirmation.
- Reconcile receiving and feed actual supplier performance back into the registry.

### Stage E: production hardening

- Add authentication, role-based authorization, encryption, backups, monitoring, rate limiting, data retention, and incident procedures.
- Validate the approved WhatsApp Business or Telegram integration terms before operational use.
- Add drift, calibration, connector-failure, duplicate-order, and audit-completeness monitoring.
- Run a prospective pilot before making business-impact claims.

## 9. Acceptance gates

The next stage should not be considered complete until its gate passes.

| Gate | Minimum evidence |
|---|---|
| Portable preliminary MVP | Clean Compose build, healthy services, browser upload, deterministic sample output |
| Data-ready pilot | Authorized data audit, leakage-safe baseline, inventory-quality report |
| Useful recommendation | Temporal evaluation plus owner review of recommendation errors |
| Safe order execution | Approval audit, idempotency test, retry test, exception handling |
| Operational integration | POS reconciliation and supplier confirmation demonstrated end to end |
| Impact claim | Prospective baseline and pilot measurement with documented limitations |

## 10. Product principles

- Keep the POS as the operational source of truth.
- Automate preparation and communication, not accountability.
- Make every recommendation editable and traceable.
- Separate forecasts, deterministic constraints, workflow state, and message wording.
- Prefer one reliable integration over several superficial connectors.
- Label synthetic, retrospective, and pilot evidence separately.
- Never present an unmeasured target as an achieved result.
