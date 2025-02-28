/* 

Orders to check:
1. Orders created in December 2024
2. Orders reassigned in December 2024
3. Orders created after 15th January 2025
4. Orders reassigned after 15th January 2025

*/
select scsl.order_id, scsl.shipment_id, scsl.id
from
    shipping_costs_sub_ledger scsl
    left join orders ord on ord.id = scsl.order_id
    left join marketplace_config mkt_conf on mkt_conf.master_channel_id = ord.master_channel_id
where
    ord.date_created > '2024-12-01'
    and ord.date_created < '2025-01-01'
    and scsl.client_prefix != 'POPCLUB'
    and mkt_conf.id is not null;

-- Get a marketplace order that was reassigned in December 2024
select ord.status, scsl.id, scsl.order_id, scsl.shipment_id, scsl.forward_charge_gst, scsl.cod_charge_gst, scsl.rto_charge_gst, scsl.management_fee_gst, scsl.total_charged_gst, scsl.debit, scsl.credit
from
    shipping_costs_sub_ledger scsl
    left join orders ord on ord.id = scsl.order_id
where
    scsl.order_id in (
        select scsl2.order_id
        from
            shipping_costs_sub_ledger scsl2
            left join orders ord on ord.id = scsl2.order_id
            left join marketplace_config mkt_conf on mkt_conf.master_channel_id = ord.master_channel_id
        where
            ord.date_created > '2024-12-01'
            and ord.date_created < '2025-01-01'
            and scsl2.client_prefix != 'POPCLUB'
            and mkt_conf.id is not null
            and ord.status NOT IN (
                'CANCELED',
                'NOT SHIPPED',
                'CLOSED'
            )
            and parent_order_id is null
        group by
            scsl2.order_id
        having
            count(distinct scsl2.id) > 1
    );

-- Get all reassigned orders

select ord.client_prefix, ord.status, scsl.order_id, scsl.shipment_id
from
    shipping_costs_sub_ledger scsl
    left join orders ord on ord.id = scsl.order_id
where
    scsl.order_id in (
        select scsl2.order_id
        from shipping_costs_sub_ledger scsl2
        where
            scsl2.date_created > '2024-12-01'
        group by
            scsl2.order_id
        having
            count(distinct scsl2.id) > 1
    )
limit 10;

SELECT ord.id, scsl.shipment_id
FROM
    orders ord
    LEFT JOIN shipping_costs_sub_ledger scsl ON scsl.order_id = ord.id
    LEFT JOIN shipments shp ON shp.id = scsl.shipment_id
    LEFT JOIN marketplace_config mkt_conf ON mkt_conf.master_channel_id = ord.master_channel_id
WHERE
    scsl.id IS NOT NULL
    AND scsl.shipment_id IS NOT NULL
    AND (
        -- Pick those orders which have charges existing in the sub ledger
        -- and the status of the order is either NOT SHIPPED, CLOSED or CANCELED
        (
            ord.status IN (
                'NOT SHIPPED',
                'CLOSED',
                'CANCELED'
            )
            AND (
                shp.order_id IS NOT NULL
                AND (
                    (scsl.debit - scsl.credit >= 1)
                    OR (
                        scsl.debit - scsl.credit <= -1
                    )
                )
                AND (
                    mkt_conf.id IS NULL
                    OR (
                        mkt_conf.id IS NOT NULL
                        -- Order management fee for marketplace orders are not refunded, skip them
                        AND ROUND(
                            CAST(
                                (scsl.total_charged_gst) AS numeric
                            ),
                            0
                        ) != ROUND(
                            CAST(
                                (scsl.management_fee_gst) AS numeric
                            ),
                            0
                        )
                    )
                )
            )
        )
        OR
        -- Pick those orders which have charges existing in the sub ledger
        -- but the shipment associated with it is unassigned.
        (
            shp.order_id IS NULL
            AND (
                (scsl.debit - scsl.credit >= 1)
                OR (
                    scsl.debit - scsl.credit <= -1
                )
            )
        )
    )
    AND ord.id = 15469878
GROUP BY
    ord.id,
    scsl.shipment_id