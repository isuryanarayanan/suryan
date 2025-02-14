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



  Merge conflict data

```bash
From github.com:RohithBhandaru/wareiq-app
 * branch                master     -> FETCH_HEAD
Auto-merging services/apis/management/project/api/clients/client_settings.py
Auto-merging services/apis/management/project/api/clients/queries.py
Auto-merging services/celery/disparate_tasks/tasks/__init__.py
Auto-merging services/celery/disparate_tasks/tasks/tasks/queries.py
Auto-merging services/celery/disparate_tasks/tasks/tasks/zoho_invoices.py
CONFLICT (content): Merge conflict in services/celery/disparate_tasks/tasks/tasks/zoho_invoices.py
Auto-merging services/core/project/__init__.py
CONFLICT (content): Merge conflict in services/core/project/__init__.py
CONFLICT (modify/delete): services/core/project/api/applications/index.py deleted in HEAD and modified in 5a2c22f5f41ed253c74ec1d922a76b48cdb77f99.  Version 5a2c22f5f41ed253c74ec1d922a76b48cdb77f99 of services/core/project/api/applications/index.py left in tree.
CONFLICT (modify/delete): services/core/project/api/applications/templates.py deleted in HEAD and modified in 5a2c22f5f41ed253c74ec1d922a76b48cdb77f99.  Version 5a2c22f5f41ed253c74ec1d922a76b48cdb77f99 of services/core/project/api/applications/templates.py left in tree.
Auto-merging services/core/project/api/core.py
Auto-merging services/core/project/api/orders/index.py
CONFLICT (content): Merge conflict in services/core/project/api/orders/index.py
Automatic merge failed; fix conflicts and then commit the result.
```
