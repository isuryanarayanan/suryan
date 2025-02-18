
WITH
    tl_summary AS (
        SELECT
            tl.order_id,
            tl.shipping_costs_sub_ledger_id AS sub_ledger_id,
            SUM(tl.debit - tl.credit) AS total_charge,
            MAX(tl.date_created) AS latest_date_created
        FROM transactions_ledger tl
        WHERE
            tl.client_prefix = $client_prefix
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
            scsl.client_prefix = $client_prefix
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

