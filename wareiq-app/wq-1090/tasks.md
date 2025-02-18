- [ ] App store revamp changes
  - [ ] Database migrations removing the unnecessary columns
  - [x] Notifications Engine
    - [x] Template naming needs to be standardized
    - [x] Fixing the notification configuration
    - [x] Updating the templates according to the relevant scenario
      - [x] Show amount with GST in the email
    - [x] Skip deduction for default messages
  - [ ] Code cleanup
  - [x] Endpoint updates `apps/` to `apps/master`
  - [ ] Move the config used by `shipping_badges` app to a dedicated file
- [ ] Shipping app changes
  - [ ] Database migrations
    - [ ] Application Costs Sub Ledger table
    - [ ] Rate cards table
    - [ ] Reconciliation history in the shipments table
    - [ ] Shipment reference for rate card
  - [ ] Code cleanup

# Database Migrations

This rework of the app store aims to simplify the current setup of the app store so that, in the next iteration a sub ledger can be used to provide
a more solid billing system for a wareiq app. The following changes are being made to the tables that are concerned with the app store.

## 1. Master Applications

Master Application is a table that holds the necessary information regarding a wareiq application that is offered in the app store. In this current structure there are
some columns which are not meaningful and in the current structure such a column are the Pricing detail columns. If the pricing details are stored inside the json field
for each subscription it is redundant and useless to have `unit_price` and `unit` columns in the table.

Here is the current structure of the application:

```python
    class MasterApplication(db.Model):

        __tablename__ = "master_application"

        id = db.Column(db.Integer, primary_key=True, autoincrement=True)


        # Content that describes the app for the end user
        app_name = db.Column(db.String, nullable=True)
        thumbnail_url = db.Column(db.String, nullable=True)
        icon_url = db.Column(db.String, nullable=True)
        description = db.Column(db.String, nullable=True)


        # Content that describes the app in the system
        app_key = db.Column(db.String)
        app_type = db.Column(db.String)
        master_configuration = db.Column(JSON)

        # Subscription details
        subscription_1 = db.Column(JSON)
        subscription_2 = db.Column(JSON)
        subscription_3 = db.Column(JSON)
        subscription_4 = db.Column(JSON)

        # Pricing details
        unit_price = db.Column(db.FLOAT, nullable=True)
        unit = db.Column(db.String)

        date_created = db.Column(db.DateTime, default=datetime.now)
        date_updated = db.Column(db.DateTime, onupdate=datetime.now)
```

The new structure of the table will be:

```python
    class MasterApplication(db.Model):

        __tablename__ = "master_application"

        id = db.Column(db.Integer, primary_key=True, autoincrement=True)

        # Content that describes the app for the end user
        app_name = db.Column(db.String, nullable=True)
        thumbnail_url = db.Column(db.String, nullable=True)
        icon_url = db.Column(db.String, nullable=True)
        description = db.Column(db.String, nullable=True)

        # Content that describes the app in the system
        app_key = db.Column(db.String)
        app_type = db.Column(db.String)
        master_configuration = db.Column(JSON)

        # Subscription details
        subscription_1 = db.Column(JSON)
        subscription_2 = db.Column(JSON)
        subscription_3 = db.Column(JSON)
        subscription_4 = db.Column(JSON)

        date_created = db.Column(db.DateTime, default=datetime.now)
        date_updated = db.Column(db.DateTime, onupdate=datetime.now)
```

NOTE:

- `master_configuration` will be used to store the default configuration for the application if any.
- `subscription_1`, `subscription_2`, `subscription_3`, `subscription_4` will be used to store the subscription details for the application in the
  form of a json object. The json object will have the following structure:

  ```json
  {
    "name": "Base",
    "desc": "Covers 2,000 sms communications",
    "price": 700,
    "unit_price": 0.35,
    "total_units": 2000,
    "recurring_days": 30
  }
  ```

## 2. User Applications

User Applications table holds the information regarding an application that is activated for a client.

```python
    class UserApplication(db.Model):

        __tablename__ = "user_application"

        # Application indentifiers
        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        client_prefix = db.Column(db.String, nullable=False)
        app_id = db.Column(db.Integer, db.ForeignKey("master_application.id"))
        active = db.Column(db.BOOLEAN, nullable=True, default=True)

        subscription_key = db.Column(db.Integer, nullable=True)
        is_recurring_payment = db.Column(db.BOOLEAN, nullable=True, default=False)

        units_remaining = db.Column(db.Integer, nullable=True)
        activated_units = db.Column(db.Integer, nullable=True)
        recurring_period = db.Column(db.INTEGER, nullable=True)
        recurring_price = db.Column(db.FLOAT, nullable=True)

        trial_taken = db.Column(db.BOOLEAN, nullable=True)
        is_trial = db.Column(db.BOOLEAN, nullable=True)

        configuration = db.Column(JSON)

        expiry_date = db.Column(db.DateTime, nullable=True)
        activated_on = db.Column(db.DateTime, default=datetime.now)

        __table_args__ = (db.UniqueConstraint("app_id", "client_prefix", name="fld_idx_ord_unique"),)
```

There are some structural problems and redundancy in the table. The columns `activated_units`, `recurring_period`, `recurring_price` are redundant as they will be available
in the subscription details of the master application. The structural problems are with how the date columns are named. Here is the new structure addressing the issues:

```python
    class UserApplication(db.Model):

        __tablename__ = "user_application"

        # Application indentifiers
        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        client_prefix = db.Column(db.String, nullable=False)
        app_id = db.Column(db.Integer, db.ForeignKey("master_application.id"))
        active = db.Column(db.BOOLEAN, nullable=True, default=True)

        subscription_key = db.Column(db.Integer, nullable=True)
        is_recurring_payment = db.Column(db.BOOLEAN, nullable=True, default=False)

        units_remaining = db.Column(db.Integer, nullable=True)
        trial_taken = db.Column(db.BOOLEAN, nullable=True)
        is_trial = db.Column(db.BOOLEAN, nullable=True)

        configuration = db.Column(JSON)

        date_expiry = db.Column(db.DateTime, nullable=True)
        date_created = db.Column(db.DateTime, default=datetime.now)
        date_updated = db.Column(db.DateTime, onupdate=datetime.now)


        __table_args__ = (db.UniqueConstraint("app_id", "client_prefix", name="fld_idx_ord_unique"),)
```

## 3. User Application History

In the current app store system, the `user_application_history` table serves the purpose of having a record of the purchase history for the client. This is the same behaviour that
the `transactions_ledger` table shows when it comes to the billing system. This means, when the `application_costs_sub_ledger` is being developed this table can be completely removed
and be replaced with a `transactions_ledger` entry, corresponding to that particular sub ledger entry.

Anyway, the current structure of the table is as follows:

```python
class UserApplicationHistory(db.Model):

    __tablename__ = "user_application_history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_prefix = db.Column(db.String, nullable=False)

    app_id = db.Column(db.Integer, db.ForeignKey("master_application.id"))
    units_remaining = db.Column(db.INTEGER, nullable=True)

    created_date = db.Column(db.DateTime, default=datetime.now)
    deducted_amount = db.Column(db.FLOAT, nullable=True)
    activation_date = db.Column(db.DateTime, nullable=False)
    expiry_date = db.Column(db.DateTime, nullable=True)

    subscription_key = db.Column(db.Integer)
    recurring_period = db.Column(db.INTEGER, nullable=True)
    recurring_price = db.Column(db.FLOAT, nullable=True)

    username = db.Column(db.String, nullable=True)
    status = db.Column(db.String, nullable=True)
    reason = db.Column(db.String, nullable=True)
```

Here also some data is redundant and the date columns are not named properly. The new structure of the table will be:

```python
class UserApplicationHistory(db.Model):

    __tablename__ = "user_application_history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_prefix = db.Column(db.String, nullable=False)

    app_id = db.Column(db.Integer, db.ForeignKey("master_application.id"))
    units_remaining = db.Column(db.INTEGER, nullable=True)

    deducted_amount = db.Column(db.FLOAT, nullable=True)

    subscription_key = db.Column(db.Integer)
    username = db.Column(db.String, nullable=True)
    status = db.Column(db.String, nullable=True)
    reason = db.Column(db.String, nullable=True)

    date_activation = db.Column(db.DateTime, nullable=False)
    date_expiry = db.Column(db.DateTime, nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.now)
    date_updated = db.Column(db.DateTime, onupdate=datetime.now)
```

# Notifications Engine

## 1. Fixing app store related templates

The app store related templates are not named properly and are not standardized. Let's see all
the required templates and fix them one by one.

So a wareiq application has the following actions that can be triggered:

1. `activate` (API)
2. `deactivate` (API, Task)
3. `renew` (API, Task)
4. `upgrade` (API)
5. `downgrade` (API,Task)

Each of these actions will have a corresponding template that will be sent to the client. The templates are:

1. Activation

When a client activates an application for the first time, if its a trial or a paid subscription, the client will receive a notification that the application has been activated.

So this template has 2 scenarios:

- Trial activation `client_app_trial_activation_success`
- Paid activation `client_app_activation_success`

The relevant information for this email will include the following according to the scenario:

- Trial activation
  - App name
  - App description
  - App thumbnail
  - App icon
  - Activation date
  - Expiry date
  - Remaining units
- Paid activation
  - App name
  - App description
  - App thumbnail
  - App icon
  - Activation date
  - Expiry date
  - Remaining units
  - Amount paid
  - GST amount
  - Total amount

2. Deactivation

When a client deactivates an application, the client will receive a notification that the application has been deactivated.

This operation can be done by the client or by the system. So the template has 2 scenarios:

- Client deactivation `client_app_deactivation_success` (When the client turns of the recurring payment)
- System deactivation `client_app_wiq_deactivation_success` (When the system deactivates the application)

In the email template the messaging should signify how the deactivation was done. If the deactivation was done by the client, the email should say that the client has deactivated the application. If the deactivation was done by the system, the email should say that the application has been deactivated by the system.

3. Renewal

Renewal of the application is done at expiry by the background job. When the application is renewed, the client will receive a notification that the application has been renewed.

- System renewal `client_app_wiq_renewal_success` (When the system renews the application)

4. Upgrade

When a client purchases an application upgrade, for both `credit_based` and `duration_based` applications, the client will recieve one single
notification that the application has been upgraded.

- Upgrade successful `client_app_upgrade_success`

5. Downgrade

When a client purchases a downgrade for an application, the client will receive a notification that the purchase for the downgrade has been successful. For `duration_based` applications, the client will receive a notification that the application has been scheduled for a downgrade. Since there is a difference in the downgrade process for `duration_based` applications, the template has 2 scenarios:

- Downgrade initiated `client_app_downgrade_initiated`
- Downgrade successful `client_app_downgrade_success`

# Default notifications
