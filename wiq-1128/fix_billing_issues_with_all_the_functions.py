import logging
from datetime import datetime, timedelta
from ..config_db import DbConnection
from logs.config import config as logger_config
from logs.logger_templates import info_log, error_log

logging.config.dictConfig(logger_config)
logger = logging.getLogger(__name__)

select_other_sub_ledgers_query = """
    SELECT
        scsl.id,
        scsl.client_prefix,
        scsl.order_id,
        scsl.shipment_id,
        scsl.zone,
        scsl.weight_charged,
        scsl.transaction_date,
        scsl.forward_charge,
        scsl.forward_charge_gst,
        scsl.cod_charge,
        scsl.cod_charge_gst,
        scsl.rto_charge,
        scsl.rto_charge_gst,
        scsl.management_fee,
        scsl.management_fee_gst,
        scsl.total_charge,
        scsl.total_charged_gst,
        scsl.credit_adjustment,
        scsl.credit_adjustment_gst,
        scsl.debit_adjustment,
        scsl.debit_adjustment_gst,
        scsl.credit,
        scsl.debit,
        scsl.date_created,
        scsl.date_updated,
        scsl.updated_by
    FROM
        shipping_costs_sub_ledger scsl
    WHERE
        scsl.order_id = %s
        AND scsl.id != %s
"""

bulk_insert_transaction_ledger_query = """
INSERT INTO transactions_ledger
    (
        category_id,
        client_prefix,
        order_id,
        shipment_id,
        shipping_costs_sub_ledger_id,
        credit,
        debit,
        date_created,
        date_updated,
        transaction_date,
        updated_by,
        is_settled,
        closing_balance
    )
SELECT
    tc.id,
    t.client_prefix,
    t.order_id,
    t.shipment_id,
    t.shipping_costs_sub_ledger_id,
    t.credit,
    t.debit,
    now() AT TIME ZONE 'Asia/Kolkata',
    now() AT TIME ZONE 'Asia/Kolkata',
    t.transaction_date,
    t.updated_by,
    t.is_settled,
    t.closing_balance
FROM (
    VALUES {0}
) AS t(
    category, 
    client_prefix, 
    order_id, 
    shipment_id, 
    shipping_costs_sub_ledger_id, 
    credit, 
    debit, 
    transaction_date, 
    updated_by, 
    closing_balance, 
    is_settled
)
LEFT JOIN transaction_category tc ON tc.category = t.category
"""

select_existing_transaction_ledger_query = """
    SELECT
        tc.category,
        tl.credit,
        tl.debit,
        tl.transaction_date,
        tl.date_created,
        tl.id,
        tc.id
    FROM
        transactions_ledger tl
        LEFT JOIN transaction_category tc ON tc.id = tl.category_id
    WHERE
        tl.shipping_costs_sub_ledger_id = %s
"""

cleanup_update_shipping_costs_sub_ledger_query = """
UPDATE
    shipping_costs_sub_ledger
SET
    total_charge = ROUND(CAST(({0}) AS numeric), 2),
    total_charged_gst = ROUND(CAST(({1}) AS numeric), 2),
    credit = ROUND(CAST(({2}) AS numeric), 2),
    debit = ROUND(CAST(({3}) AS numeric), 2),
    date_updated = now() AT TIME ZONE 'Asia/Kolkata',
    updated_by = 'surya.narayanan@wareiq.com'
WHERE
    id = {4}
"""

update_client_balance = """
    UPDATE client_mapping SET
        current_balance=coalesce(current_balance, 0)- (%s)
    WHERE
        client_prefix=%s
    RETURNING current_balance;
"""

select_orders_to_calculate_query = """
WITH
    tl_summary AS (
        SELECT
            tl.order_id,
            tl.shipping_costs_sub_ledger_id AS sub_ledger_id,
            SUM(tl.debit - tl.credit) AS total_charge,
            MAX(tl.date_created) AS latest_date_created
        FROM transactions_ledger tl
        WHERE
            tl.client_prefix = '__CLIENT_PREFIX__'
            __ORDER_FILTER__
            AND tl.shipping_costs_sub_ledger_id IS NOT NULL
            AND tl.date_created > '2024-11-01'
        GROUP BY
            tl.order_id,
            tl.shipping_costs_sub_ledger_id
    ),
    scsl_summary AS (
        SELECT
            scsl.id AS sub_ledger_id,
            scsl.order_id,
            SUM(
                scsl.forward_charge_gst + scsl.cod_charge_gst + scsl.rto_charge_gst + scsl.management_fee_gst - COALESCE(scsl.credit_adjustment_gst, 0) + COALESCE(scsl.debit_adjustment_gst, 0)
            ) AS individual_charge_gst,
            SUM(scsl.total_charged_gst) as total_charge_gst,
            sum(scsl.debit - scsl.credit) AS net_charge_gst
        FROM shipping_costs_sub_ledger scsl
        WHERE
            scsl.client_prefix = '__CLIENT_PREFIX__'
            __ORDER_FILTER__
            AND scsl.date_created > '2024-11-01'
        GROUP BY
            scsl.order_id,
            scsl.id
    )
SELECT
    ord.id,
    ord.client_prefix,
    ord.order_date,
    ord.status,
    ord.status_type,
    ord.parent_order_id,
    ord.channel_order_id,
    shp.id,
    shp.awb,
    shp.courier_id,
    shp.volumetric_weight,
    shp.weight,
    shp.order_id,
    shp.dimensions,
    shp.zone,
    scsl.id,
    scsl.weight_charged,
    scsl.zone,
    scsl.credit_adjustment,
    scsl.debit_adjustment,
    pp.pincode as pickup_pincode,
    sa.pincode as delivery_pincode,
    os.status_time,
    op.payment_mode,
    op.amount,
    op.collectable_amount,
    mkt_conf.id,
    mkt_conf.client_prefix AS mkt_plc_client_prefix,
    cm.management_fee,
    cm.management_fee_static,
    cm.account_type,
    mcm.management_fee,
    mcm.management_fee_static,
    mcm.account_type,
    ns.client_business_notification_email,
    mkt_ns.client_business_notification_email,
    scsl_summary.individual_charge_gst,
    scsl_summary.total_charge_gst,
    scsl_summary.net_charge_gst,
    scsl.forward_charge_gst,
    scsl.cod_charge_gst,
    scsl.rto_charge_gst,
    scsl.management_fee_gst,
    scsl.client_prefix
FROM
    tl_summary
    LEFT JOIN scsl_summary ON tl_summary.order_id = scsl_summary.order_id AND tl_summary.sub_ledger_id = scsl_summary.sub_ledger_id
    LEFT JOIN shipping_costs_sub_ledger scsl ON scsl.id = tl_summary.sub_ledger_id
    LEFT JOIN orders ord ON ord.id = scsl.order_id
    LEFT JOIN shipments shp ON shp.id = scsl.shipment_id
    LEFT JOIN orders_payments op ON op.order_id = scsl.order_id
    LEFT JOIN marketplace_config mkt_conf ON mkt_conf.master_channel_id = ord.master_channel_id
    LEFT JOIN client_mapping cm ON cm.client_prefix = scsl.client_prefix
    LEFT JOIN client_mapping mcm ON mcm.client_prefix = mkt_conf.client_prefix
    LEFT JOIN pickup_points pp ON pp.id = shp.pickup_id
    LEFT JOIN shipping_address sa ON sa.id = ord.delivery_address_id
    LEFT JOIN (
        SELECT
            *
        FROM
            order_status
        WHERE
            status IN ('Delivered', 'RTO', 'DTO')
    ) os ON os.shipment_id = shp.id
    LEFT JOIN master_couriers mc ON mc.id = shp.courier_id
    LEFT JOIN notifications_settings ns ON ns.client_prefix = cm.client_prefix
    LEFT JOIN notifications_settings mkt_ns ON mkt_ns.client_prefix = mcm.client_prefix
WHERE
    shp.order_id IS NOT NULL AND ((
        tl_summary.total_charge - scsl_summary.individual_charge_gst > 0.1
        OR tl_summary.total_charge - scsl_summary.individual_charge_gst< -0.1
    ) OR (
        tl_summary.total_charge - scsl_summary.total_charge_gst > 0.1
        OR tl_summary.total_charge - scsl_summary.total_charge_gst < -0.1
    ) OR (
        tl_summary.total_charge - scsl_summary.net_charge_gst > 0.1
        OR tl_summary.total_charge - scsl_summary.net_charge_gst < -0.1
    ))
    """


def fix_billing_issues_util(task_name, client_prefix=None, order_ids=[]):
    """
    This function will solve the following billing issues.

    1. Extra deductions
    2. Extra refunds
    3. Sub ledger updates

    The charges in the ledger is not matching with the sub ledger for shipping charges for the following known cases:
    1. Ledger total charge > sub ledger total charge
        1.1. Order management fee duplication
        1.2. RTO charge duplication
        1.3. Additional shipping charge
    2. Ledger total charge < sub ledger total charge
        2.1. Missing RTO charge deduction entry in the ledger
        2.2. Missing COD charge refund entry in the ledger

    """

    conn_obj = DbConnection().get_db_connection_instance()
    conn, cur = next(conn_obj)
    _, cur_2 = DbConnection().get_pincode_db_connection_instance()
    time_since_nov_2 = datetime(2024, 11, 2)
    time_since_nov_2 = time_since_nov_2.strftime("%Y-%m-%d")
    time_now = datetime.utcnow() + timedelta(hours=5.5)
    order_ids_str = "(" + ",".join(str(order_id) for order_id in order_ids) + ")"

    # Get clients to run the job for
    query_to_get_clients = "select client_prefix, count(*) as entry_count from shipping_costs_sub_ledger where date_created > '2024-11-02' __CLIENT_FILTER__ __ORDER_FILTER__  group by client_prefix order by entry_count desc"
    # This query will return all the order id's which have charge mismatch between transactions ledger and shipping costs sub ledger.
    query_to_get_orders = select_orders_to_calculate_query.replace("__STATUS_TIME__", time_since_nov_2)

    if client_prefix:
        query_to_get_clients = query_to_get_clients.replace(
            "__CLIENT_FILTER__", "AND client_prefix = '%s'" % client_prefix
        )
    else:
        query_to_get_clients = query_to_get_clients.replace("__CLIENT_FILTER__", "")

    if order_ids:
        query_to_get_clients = query_to_get_clients.replace("__ORDER_FILTER__", "AND order_id IN %s" % order_ids_str)
        query_to_get_orders = query_to_get_orders.replace("__ORDER_FILTER__", "AND order_id IN %s" % order_ids_str)
    else:
        query_to_get_clients = query_to_get_clients.replace("__ORDER_FILTER__", "")
        query_to_get_orders = query_to_get_orders.replace("__ORDER_FILTER__", "")

    cur.execute(query_to_get_clients)
    active_clients = cur.fetchall()

    for client in active_clients:
        cur.execute(query_to_get_orders.replace("__CLIENT_PREFIX__", client[0]))
        all_orders = cur.fetchall()

        count = 0
        mismatch_count = 0

        # Calculate the charges for the order
        for order in all_orders:
            try:
                count += 1
                update = False
                applied_transactions = []
                unapplied_transactions = []
                debit = 0
                credit = 0
                final_debit = 0
                final_credit = 0

                # Total charge
                final_total_charge_gst = 0
                ledger_total_charge_gst = 0
                sub_ledger_individual_charge_gst = 0
                sub_ledger_total_charge_gst = 0
                sub_ledger_net_charge_gst = 0
                ledger_net_gap_gst = 0
                sub_ledger_net_gap_gst = 0

                # Forward charge
                sub_ledger_forward_charge_gst = 0
                ledger_forward_charge_gst = 0
                forward_charge_diff = 0

                # Cod charge
                sub_ledger_cod_charge_gst = 0
                ledger_cod_charge_gst = 0
                cod_charge_diff = 0

                # Rto charge
                sub_ledger_rto_charge_gst = 0
                ledger_rto_charge_gst = 0
                rto_charge_diff = 0

                # Management fee
                other_sub_ledger_management_fee_gst = 0
                sub_ledger_management_fee_gst = 0
                ledger_management_fee_gst = 0
                management_fee_diff = 0

                cur.execute(
                    select_existing_transaction_ledger_query,
                    (order[15],),
                )
                existing_transactions = cur.fetchall()

                cur.execute(
                    select_other_sub_ledgers_query,
                    (
                        order[0],
                        order[15],
                    ),
                )
                other_sub_ledgers = cur.fetchall()

                # Total charge
                ledger_total_charge_gst = round(
                    sum(
                        (existing_transaction[2] or 0) - (existing_transaction[1] or 0)  # debit - credit
                        for existing_transaction in existing_transactions
                    ),
                    2,
                )
                sub_ledger_individual_charge_gst = round(order[36] or 0, 2)
                sub_ledger_total_charge_gst = round(order[37] or 0, 2)
                sub_ledger_net_charge_gst = round(order[38] or 0, 2)

                ledger_net_gap_gst = round(ledger_total_charge_gst - sub_ledger_individual_charge_gst, 2)
                sub_ledger_net_gap_gst = round(sub_ledger_net_charge_gst - sub_ledger_individual_charge_gst, 2)

                # Forward charge
                sub_ledger_forward_charge_gst = round(order[39] or 0, 2)
                ledger_forward_charge_gst = round(
                    sum(
                        (existing_transactions[2] or 0) - (existing_transactions[1] or 0)
                        for existing_transactions in existing_transactions
                        if "FORWARD_CHARGE" in existing_transactions[0]
                    ),
                    2,
                )
                forward_charge_diff = round(sub_ledger_forward_charge_gst - ledger_forward_charge_gst, 2)

                # Cod charge
                sub_ledger_cod_charge_gst = round(order[40] or 0, 2)
                ledger_cod_charge_gst = round(
                    sum(
                        (existing_transactions[2] or 0) - (existing_transactions[1] or 0)
                        for existing_transactions in existing_transactions
                        if "COD_CHARGE" in existing_transactions[0]
                    ),
                    2,
                )
                cod_charge_diff = round(sub_ledger_cod_charge_gst - ledger_cod_charge_gst, 2)

                # Rto charge
                sub_ledger_rto_charge_gst = round(order[41] or 0, 2)
                ledger_rto_charge_gst = round(
                    sum(
                        (existing_transactions[2] or 0) - (existing_transactions[1] or 0)
                        for existing_transactions in existing_transactions
                        if "RTO_CHARGE" in existing_transactions[0]
                    ),
                    2,
                )
                rto_charge_diff = round(sub_ledger_rto_charge_gst - ledger_rto_charge_gst, 2)

                # Management fee
                other_sub_ledger_management_fee_gst = round(
                    sum((other_sub_ledger[14]) for other_sub_ledger in other_sub_ledgers), 2
                )
                sub_ledger_management_fee_gst = round(order[42] or 0, 2)
                ledger_management_fee_gst = round(
                    sum(
                        (existing_transactions[2] or 0) - (existing_transactions[1] or 0)
                        for existing_transactions in existing_transactions
                        if "MANAGEMENT_FEE" in existing_transactions[0]
                    ),
                    2,
                )
                management_fee_diff = round(
                    (sub_ledger_management_fee_gst + other_sub_ledger_management_fee_gst) - ledger_management_fee_gst, 2
                )

                # 1. Missing entries
                # -- The ledger will show less charges than the sub ledger in the ideal condition
                # -- The net gap in the sub ledger will be less than the net gap in the sub ledger in the ideal condition
                try:
                    if (ledger_net_gap_gst < 0) or (
                        ledger_net_gap_gst > 0 and abs(ledger_net_gap_gst - sub_ledger_net_gap_gst) > 0.1
                    ):
                        info_log(
                            logger,
                            task_name,
                            "Missing entries",
                            "Client - {0}, Shipment id - {1}, Count - {2}".format(order[43], str(order[7]), count),
                        )

                        if abs(cod_charge_diff) > 0:
                            info_log(
                                logger,
                                task_name,
                                "Cod charge missing entry",
                                "Client - {0}, Shipment id - {1}, Count - {2}".format(order[43], str(order[7]), count),
                            )

                            if cod_charge_diff > 0:
                                unapplied_transactions.append(
                                    (
                                        "DEDUCTION_SHIPPING_COD_CHARGE",
                                        order[43],
                                        order[0],
                                        order[7],
                                        order[15],
                                        0,
                                        round(cod_charge_diff, 2),
                                        time_now,
                                        "surya.narayanan@wareiq.com",
                                    )
                                )

                                ledger_net_gap_gst += cod_charge_diff
                                debit += cod_charge_diff
                            else:
                                unapplied_transactions.append(
                                    (
                                        "PARTIAL_REFUND_DEDUCTION_SHIPPING_COD_CHARGE",
                                        order[43],
                                        order[0],
                                        order[7],
                                        order[15],
                                        round(-1 * cod_charge_diff, 2),
                                        0,
                                        time_now,
                                        "surya.narayanan@wareiq.com",
                                    )
                                )
                                ledger_net_gap_gst += cod_charge_diff
                                credit += -1 * cod_charge_diff

                            cod_charge_diff = 0
                            update = True

                        if abs(rto_charge_diff) > 0:
                            info_log(
                                logger,
                                task_name,
                                "RTO charge missing entry",
                                "Client - {0}, Shipment id - {1}, Count - {2}".format(order[43], str(order[7]), count),
                            )
                            if rto_charge_diff > 0:
                                unapplied_transactions.append(
                                    (
                                        "DEDUCTION_SHIPPING_RTO_CHARGE",
                                        order[43],
                                        order[0],
                                        order[7],
                                        order[15],
                                        0,
                                        round(rto_charge_diff, 2),
                                        time_now,
                                        "surya.narayanan@wareiq.com",
                                    )
                                )
                                ledger_net_gap_gst += rto_charge_diff
                                debit += rto_charge_diff
                            else:
                                unapplied_transactions.append(
                                    (
                                        "PARTIAL_REFUND_DEDUCTION_SHIPPING_RTO_CHARGE",
                                        order[43],
                                        order[0],
                                        order[7],
                                        order[15],
                                        round(-1 * rto_charge_diff, 2),
                                        0,
                                        time_now,
                                        "surya.narayanan@wareiq.com",
                                    )
                                )
                                ledger_net_gap_gst += rto_charge_diff
                                credit += -1 * rto_charge_diff

                            rto_charge_diff = 0
                            update = True

                except Exception as e:
                    error_log(
                        logger,
                        task_name,
                        "Could not fix missing entries",
                        "Client - {0}, Shipment id - {1}, Count - {2}".format(order[43], str(order[7]), count),
                    )
                # 2. Duplicate deductions
                # -- The ledger will show more charges than the sub ledger in the ideal condition
                # -- The net gap in the sub ledger should be matching with the net gap in transactions ledger in the ideal condition
                try:
                    if (ledger_net_gap_gst > 0) and (
                        abs(
                            ledger_net_gap_gst
                            - (
                                sub_ledger_net_gap_gst
                                + (sub_ledger_individual_charge_gst - sub_ledger_total_charge_gst)
                            )
                        )
                        < 0.1
                    ):
                        info_log(
                            logger,
                            task_name,
                            "Duplicate deductions",
                            "Client - {0}, Shipment id - {1}, Count - {2}".format(order[43], str(order[7]), count),
                        )
                        if abs(rto_charge_diff) > 0:
                            info_log(
                                logger,
                                task_name,
                                "RTO charge extra entry",
                                "Client - {0}, Shipment id - {1}, Count - {2}".format(order[43], str(order[7]), count),
                            )
                            if rto_charge_diff > 0:
                                applied_transactions.append(
                                    (
                                        "DEDUCTION_SHIPPING_RTO_CHARGE",
                                        order[43],
                                        order[0],
                                        order[7],
                                        order[15],
                                        0,
                                        round(rto_charge_diff, 2),
                                        time_now,
                                        "surya.narayanan@wareiq.com",
                                    )
                                )
                                ledger_net_gap_gst += rto_charge_diff
                                sub_ledger_net_gap_gst += rto_charge_diff
                                debit += rto_charge_diff
                                update = True
                            else:
                                applied_transactions.append(
                                    (
                                        "PARTIAL_REFUND_DEDUCTION_SHIPPING_RTO_CHARGE",
                                        order[43],
                                        order[0],
                                        order[7],
                                        order[15],
                                        round(-1 * rto_charge_diff, 2),
                                        0,
                                        time_now,
                                        "surya.narayanan@wareiq.com",
                                    )
                                )
                                ledger_net_gap_gst += rto_charge_diff
                                sub_ledger_net_gap_gst += rto_charge_diff
                                credit += -1 * rto_charge_diff
                                update = True
                            rto_charge_diff = 0

                        if abs(management_fee_diff) > 0:
                            info_log(
                                logger,
                                task_name,
                                "Management fee extra entry",
                                "Client - {0}, Shipment id - {1}, Count - {2}".format(order[43], str(order[7]), count),
                            )
                            if management_fee_diff > 0:
                                applied_transactions.append(
                                    (
                                        "DEDUCTION_SHIPPING_MANAGEMENT_FEE",
                                        order[43],
                                        order[0],
                                        order[7],
                                        order[15],
                                        0,
                                        round(management_fee_diff, 2),
                                        time_now,
                                        "surya.narayanan@wareiq.com",
                                    )
                                )
                                ledger_net_gap_gst += management_fee_diff
                                if abs(ledger_net_gap_gst - sub_ledger_net_gap_gst) > 0.1:
                                    sub_ledger_net_gap_gst += management_fee_diff
                                debit += management_fee_diff
                                update = True
                            else:
                                applied_transactions.append(
                                    (
                                        "PARTIAL_REFUND_DEDUCTION_SHIPPING_MANAGEMENT_FEE",
                                        order[43],
                                        order[0],
                                        order[7],
                                        order[15],
                                        round(-1 * management_fee_diff, 2),
                                        0,
                                        time_now,
                                        "surya.narayanan@wareiq.com",
                                    )
                                )
                                ledger_net_gap_gst += management_fee_diff
                                if abs(ledger_net_gap_gst - sub_ledger_net_gap_gst) > 0.1:
                                    sub_ledger_net_gap_gst += management_fee_diff
                                credit += -1 * management_fee_diff
                                update = True
                            management_fee_diff = 0

                except Exception as e:
                    error_log(
                        logger,
                        task_name,
                        "Could not fix duplicate deductions",
                        "Client - {0}, Shipment id - {1}, Count - {2}".format(order[43], str(order[7]), count),
                    )

                # 3. Order management fee bug.
                # -- If the gap in ledger is not explained by either of the above 2 reasons then it could be due to the omf bug
                # -- either mismatched sub ledger or additionally deducted ledger.
                try:
                    if abs(ledger_net_gap_gst) > 0.1:
                        ledger_shipping_charge = round(
                            sum(
                                (existing_transactions[2] or 0) - (existing_transactions[1] or 0)
                                for existing_transactions in existing_transactions
                                if "DEDUCTION_SHIPPING_CHARGE" == existing_transactions[0]
                            ),
                            2,
                        )

                        if (
                            order[26]  # the order is from a marketplace
                            and abs(ledger_shipping_charge - ledger_net_gap_gst)
                            < 0.1  # The gap in ledger is a shipping charge
                            and abs(ledger_shipping_charge - order[42])
                            < 0.1  # The shipping charge is the management fee
                            and ledger_shipping_charge > 0  # The shipping charge is positive
                        ):
                            info_log(
                                logger,
                                task_name,
                                "Extra shipping charge",
                                "Client - {0}, Shipment id - {1}, Count - {2}".format(order[43], str(order[7]), count),
                            )
                            applied_transactions.append(
                                (
                                    "REFUND_DEDUCTION_SHIPPING_CHARGE",
                                    order[43],
                                    order[0],
                                    order[7],
                                    order[15],
                                    round(ledger_shipping_charge, 2),
                                    0,
                                    time_now,
                                    "surya.narayanan@wareiq.com",
                                )
                            )
                            ledger_net_gap_gst -= ledger_shipping_charge
                            credit += ledger_shipping_charge
                            update = True

                    if (
                        abs(ledger_net_gap_gst) < 0.1
                        and abs(sub_ledger_net_gap_gst) > 0.1
                        and (
                            abs(forward_charge_diff)
                            + abs(cod_charge_diff)
                            + abs(rto_charge_diff)
                            + abs(management_fee_diff)
                        )
                        < 0.1
                    ):
                        info_log(
                            logger,
                            task_name,
                            "Additional charges",
                            "Client - {0}, Shipment id - {1}, Count - {2}".format(order[43], str(order[7]), count),
                        )
                        if sub_ledger_net_gap_gst > 0:
                            applied_transactions.append(
                                (
                                    "PARTIAL_REFUND_DEDUCTION_SHIPPING_CHARGE",
                                    order[43],
                                    order[0],
                                    order[7],
                                    order[15],
                                    round(abs(sub_ledger_net_gap_gst), 2),
                                    0,
                                    time_now,
                                    "surya.narayanan@wareiq.com",
                                )
                            )
                            unapplied_transactions.append(
                                (
                                    "DEDUCTION_SHIPPING_CHARGE",
                                    order[43],
                                    order[0],
                                    order[7],
                                    order[15],
                                    0,
                                    round(abs(sub_ledger_net_gap_gst), 2),
                                    time_now,
                                    "surya.narayanan@wareiq.com",
                                )
                            )
                            credit += abs(sub_ledger_net_gap_gst)
                            debit += abs(sub_ledger_net_gap_gst)
                            sub_ledger_net_gap_gst = 0
                        else:
                            applied_transactions.append(
                                (
                                    "DEDUCTION_SHIPPING_CHARGE",
                                    order[43],
                                    order[0],
                                    order[7],
                                    order[15],
                                    0,
                                    round(abs(sub_ledger_net_gap_gst), 2),
                                    time_now,
                                    "surya.narayanan@wareiq.com",
                                )
                            )
                            unapplied_transactions.append(
                                (
                                    "PARTIAL_REFUND_DEDUCTION_SHIPPING_CHARGE",
                                    order[43],
                                    order[0],
                                    order[7],
                                    order[15],
                                    round(abs(sub_ledger_net_gap_gst), 2),
                                    0,
                                    time_now,
                                    "surya.narayanan@wareiq.com",
                                )
                            )
                            debit += abs(sub_ledger_net_gap_gst)
                            credit += abs(sub_ledger_net_gap_gst)
                            sub_ledger_net_gap_gst = 0

                    if abs(sub_ledger_net_gap_gst) > 0.1:  # Sub ledger wrong
                        if (
                            order[26]
                            and abs(sub_ledger_net_gap_gst + order[42]) < 0.1
                            and abs(ledger_net_gap_gst) < 0.1
                        ):  # Sub ledger wrong due to management fee not being accounted for
                            info_log(
                                logger,
                                task_name,
                                "Management fee not accounted for",
                                "Client - {0}, Shipment id - {1}, Count - {2}".format(order[43], str(order[7]), count),
                            )
                            sub_ledger_net_gap_gst += order[42]
                            update = True

                except Exception as e:
                    error_log(
                        logger,
                        task_name,
                        "Could not fix order management fee bug",
                        "Client - {0}, Shipment id - {1}, Count - {2}".format(order[43], str(order[7]), count),
                    )

                # 3. Additional charges
                # -- The ledger and the individual charges in the sub ledger will match but there will be a difference
                # -- in the net charge against the order in the sub ledger. This means some charge is actually missing from the
                # -- client's wallet and needs to be adjusted.
                try:
                    pass

                except Exception as e:
                    error_log(
                        logger,
                        task_name,
                        "Could not fix additional charges",
                        "Client - {0}, Shipment id - {1}, Count - {2}".format(order[43], str(order[7]), count),
                    )

                # Check the charges
                if abs(ledger_net_gap_gst) > 0.1 or abs(sub_ledger_net_gap_gst) > 0.1:
                    mismatch_count += 1
                    info_log(
                        logger,
                        task_name,
                        "Charge mismatch",
                        "Client - {0}, Shipment id - {1}, Count - {2}, Mismatch - {3}".format(
                            order[43], str(order[7]), count, mismatch_count
                        ),
                    )
                    continue
                else:
                    final_total_charge_gst = ledger_total_charge_gst + (debit - credit)
                    final_debit = (
                        round(
                            sum((existing_transactions[2] or 0) for existing_transactions in existing_transactions),
                            2,
                        )
                        + debit
                    )
                    final_credit = (
                        round(
                            sum((existing_transactions[1] or 0) for existing_transactions in existing_transactions),
                            2,
                        )
                        + credit
                    )
                    info_log(
                        logger,
                        task_name,
                        "Charge match",
                        "Client - {0}, Shipment id - {1}, Count - {2}".format(order[43], str(order[7]), count),
                    )

                # 4. Update the sub ledger
                # -- Update the sub ledger with the new values
                try:
                    if unapplied_transactions:
                        cur.execute(
                            "SELECT current_balance FROM client_mapping WHERE client_prefix = %s",
                            (order[43],),
                        )
                        closing_balance = cur.fetchone()[0]
                        entries = []

                        for unapplied_transaction in unapplied_transactions:
                            unapplied_transaction = list(unapplied_transaction)
                            unapplied_transaction.append(round(closing_balance, 2))
                            unapplied_transaction.append(False)
                            entries.append(tuple(unapplied_transaction))

                        # Insert the transaction ledger entries for the charges
                        values = ",".join(
                            cur.mogrify("(%s,%s,%s::numeric,%s::numeric,%s::numeric,%s,%s,%s,%s,%s,%s)", entry).decode(
                                "utf-8"
                            )
                            for entry in entries
                        )
                        (bulk_insert_transaction_ledger_query.format(values))

                    if applied_transactions:
                        charges_difference = sum(
                            (transaction[6] if transaction[6] else -1 * transaction[5] if transaction[5] else 0)
                            for transaction in applied_transactions
                        )

                        # Deduct the sum of the charges from the client's wallet and get the new balance
                        (update_client_balance, (charges_difference, order[43]))
                        # new_balance = cur.fetchone()[0]
                        new_balance = 1000

                        # Update the closing balances for the transactions
                        closing_balance = new_balance + charges_difference
                        entries = []

                        for transaction in applied_transactions:
                            transaction = list(transaction)
                            closing_balance = closing_balance - (
                                transaction[6] if transaction[6] else -1 * transaction[5] if transaction[5] else 0
                            )
                            transaction.append(round(closing_balance, 2))
                            transaction.append(True)
                            entries.append(tuple(transaction))

                        # Insert the transaction ledger entries for the charges
                        values = ",".join(
                            cur.mogrify("(%s,%s,%s::numeric,%s::numeric,%s::numeric,%s,%s,%s,%s,%s,%s)", entry).decode(
                                "utf-8"
                            )
                            for entry in entries
                        )
                        (bulk_insert_transaction_ledger_query.format(values))

                    # Update the sub ledger with the new values
                    (
                        cleanup_update_shipping_costs_sub_ledger_query.format(
                            final_total_charge_gst / 1.18,
                            final_total_charge_gst,
                            final_credit,
                            final_debit,
                            order[15],
                        ),
                    )

                    # conn.commit()
                except Exception as e:
                    # conn.rollback()
                    error_log(
                        logger,
                        task_name,
                        "Could not fix order management fee bug",
                        "Client - {0}, Shipment id - {1}, Count - {2}".format(order[43], str(order[7]), count),
                    )

            except Exception:
                error_log(
                    logger,
                    task_name,
                    "Sub ledger update failed",
                    "Client - {0}, Shipment id - {1}, Count - {2}".format(order[43], str(order[7]), count),
                )

    info_log(logger, task_name, "Task run completed", "")
