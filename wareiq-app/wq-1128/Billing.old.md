# Billing Documentation

WareIQ offers two primary services to its (normal wiq clients and wiq marketplace clients) clients: **Shipping** and **Fulfillment**. Each service incurs specific charges based on usage and agreements with WareIQ’s partners (such as courier providers, warehouses, etc.). These charges are reconciled monthly, and the finance team generates a bill for each client.

WareIQ clients can be billed in one of two ways: **Prepaid** or **Postpaid**, each with a distinct billing process. The client’s **current balance** is tracked to monitor spending on WareIQ services.

> The account type (prepaid or postpaid) and closing balance of each client’s wallet are stored in the `client_mapping` table under `account_type` and `current_balance`.

---

## Billing Methods

### Prepaid Clients

Prepaid clients maintain a positive balance in their `current_balance` to access WareIQ services. The billing process for prepaid clients includes:

1. **Wallet Recharge**: Clients can recharge their wallet using online (e.g., Razorpay) or offline (e.g., bank transfer) payment methods. The recharged amount is added to `current_balance`.
2. **Shipping Charge Deduction**: Charges are deducted upon shipment creation (handled by `shipping_engine`) and updated with each status sync (via `status_engine` or `webhook`). If `current_balance` is insufficient, shipment creation fails, and the courier assignment is removed.
3. **Application Charge Deduction**: Application costs are deducted from the wallet for the applications subscribed to by the client at the time of subscription or renewal.
4. **Refund/Reconciliation**: If a refund or reconciliation is needed, the finance team can adjust `current_balance` using either the `billing/v1/refund` API or the `/celery/uploads/internal/v1/reconciliation` API.

### Postpaid Clients

Postpaid clients are billed monthly based on service usage, and their wallet operates differently:

1. **Shipping Charge Deduction**: Charges are deducted at shipment creation. If `current_balance` becomes negative, shipment creation still proceeds.
2. **Hidden Wallet Balance**: Postpaid clients do not see a visible wallet balance, nor do they have recharge options. Their balance is maintained internally by the finance team.
3. **Application Charge Deduction**: Application costs are deducted from the wallet for the applications subscribed to by the client at the time of subscription or renewal and settled at the end of the month.
4. **Refund/Reconciliation**: The finance team can update `current_balance` for any required refunds or reconciliations using the same APIs as for prepaid clients.

---

## Ledger Overview

A **ledger** records all transactions within the wallet, stored in the `transactions_ledger` table. It logs all financial activities, such as:

1. **Recharges**: Funds added to the client’s wallet.
2. **Deductions**: Charges deducted for services.
3. **Refunds/Reconciliations**: Adjustments made by the finance team, either for refunds or other reconciliations.

### Transaction Types

Transactions, which represent individual financial activities impacting the wallet, are categorized and saved in the `transaction_category` table. This table organizes each possible transaction type for consistency in reporting and auditing.

### Recording Transactions

Each transaction updates the ledger in real time and includes the following details:

- **Transaction Category**: Identifies if the transaction is a recharge, deduction, or refund/reconciliation.
- **Credit/Debit**: The transaction’s monetary value.
- **Date**: The date and time of the transaction.
- **References**: Foreign keys to relevant tables (e.g., `orders`, `shipments`) for easy lookup of shipping or service-related deductions.

This approach ensures all financial activities are traceable and auditable.

---

## Sub-Ledgers

To enhance the accuracy of financial tracking and aid in double-entry bookkeeping, WareIQ employs **sub-ledgers** for different services. These sub-ledgers provide a detailed view of transactions for each service, helping to resolve discrepancies efficiently.

### Shipping Costs Sub-Ledger (SCSL)

This sub-ledger records all charges associated with shipping. At shipment creation:

1. The relevant amount is deducted from the client’s wallet.
2. An entry is created in the `shipping_costs_sub_ledger` table, specifying:
   - **Forward Charge**
     - When a forward or a return order is shipped, forward charge is added.
   - **RTO Charge**
     - When a forward order goes into RTO flow, RTO charge is added.
   - **COD Charge**
     - COD charge is charged when a forward order is shipped.
     - COD is charge is refunded in case a forward order moves to RTO flow.
   - **Management Fee**
     - For WIQ-marketplace orders, order management fee is charged while creating the order in WIQ.
     - For non-(WIQ-marketplace) orders, shipping management fee is charged while shipping the order.
3. Reconciliation process involves correcting the weight considered by WIQ while charging the clients for shipping. When couriers share the correct weight charged at the month end, this data is uploaded to add the charge adjustments for the four categories mentioned above.
   > [!NOTE]
   > For shipments that are over-charged nominally, refunds are not processed.
   > For shipments that are over-charged unusually, finace team provides the list of such shipments that need to be refunded.
4. There is 2 types of refunds, a full refund and partial refund.
   - **Full Refund**: When a shipment is in the `NOT SHIPPED`, `CLOSED` or `CANCELED` , the full amount is refunded.
     > [!NOTE]
     > Full refund is processed only when the shipment is not shipped or canceled or closed.
     > Full refund means if the order is reconciled the entire net deduction is what is refunded.
   - **Partial Refund**: When a shipment is shipped but then the charges are adjusted either by the courier or by the finance team, a partial refund is processed.

Each charge is also logged in the `transactions_ledger`. For any refunds or reconciliations, the sub-ledger is updated, and new entries are added to the `transactions_ledger` to reflect these adjustments.

### Wallet Recharges Sub-Ledger [wip]

The **Wallet Recharges Sub-Ledger** will detail each wallet recharge transaction. This sub-ledger is planned but has not yet been implemented.

### Application Costs Sub-Ledger [wip]

The **Application Costs Sub-Ledger** will track costs associated with application services. Like the Wallet Recharges Sub-Ledger, this is planned for future implementation.

## Context

For every WareIQ client they will have a `current_balance` that will be maintained by the billing system. WareIQ clients are categorized into 2 types based on their billing setup:

1. Prepaid clients - these clients maintain a positive balance in their `current_balance` to access WareIQ services.
2. Postpaid Clients - these clients are billed monthly based on service usage.

A client's `current_balance` can be updated by 2 entities:

1. A WareIQ service.
2. The finance team signified by `someone@wareiq.com`.

These updates are recorded in 2 tables in the database.

- A sub ledger is a collection of changes that happened to the `current_balance` of a prepaid or postpaid wallet.

  A sub ledger's main objective is to be the source of truth for the adjustment that happened on the `current_balance`, and to explain the difference the sub-ledger should hold all necessary information.

  **NOTE**:

  - How-to-implement-a-sub-ledger.md will define the checks and requirements for implementing it.
  - All sub ledgers implemented in the billing system should have a document available in the `Billing>Sub-ledgers` folder.

- A transactions ledger records every individual change done to the `current_balance` of a prepaid or postpaid wallet.
