# WareIQ

## Wed, 12 Feb 2025

- [x] Explain to Aayush the confusion in understanding the transaction ledger entries against cleaned up order.
- [ ] Test the reconciliation flow for updating rate cards for orders.
- [ ] Test the `fix_billing_issues` script for the rest of the orders in the system that needs to be cleaned up
- [ ] App store revamp changes
    - [ ] Database migrations removing the unnecessary columns
    - [ ] Notifications Engine
        - [ ] Template naming needs to be standardized
        - [ ] Fixing the notification configuration
        - [ ] Updating the templates according to the relevant scenario
            - [ ] Show amount with gst in the email
        - [ ] Default notifiactions should not fail if the deduction is not successful
            - [ ] Check with Aayush if the deduction should happen at all for default notifications
    - [ ] Code cleanup
    - [ ] Endpoint updates `apps/` to `apps/master`
    - [ ] Move the config used by `shipping_badges` app to dedicated file.
- [ ] Shipping app changes.
    - [ ] Database migrations
        - [ ] Application Costs Sub Ledger table
        - [ ] Rate cards table
        - [ ] Reconciliation history in the shipments table
        - [ ] Shipment reference for rate card
    - [ ] Code cleanup





