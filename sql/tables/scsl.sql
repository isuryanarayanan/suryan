select 
    scsl.id,
    scsl.order_id,
    scsl.forward_charge_gst, 
    scsl.cod_charge_gst, 
    scsl.rto_charge_gst, 
    scsl.management_fee_gst, 
    scsl.total_charged_gst,
    (
        scsl.forward_charge_gst + scsl.cod_charge_gst + scsl.rto_charge_gst + scsl.management_fee_gst - COALESCE(scsl.credit_adjustment_gst, 0) + COALESCE(scsl.debit_adjustment_gst, 0)
    ) as individual_charges,
    scsl.credit, 
    scsl.debit, 
    scsl.credit_adjustment_gst, 
    scsl.debit_adjustment_gst, 
    scsl.updated_by
from 
    shipping_costs_sub_ledger scsl
where
    scsl.order_id = 15958255;

-- 100, 100, 200
-- 100, 95, 200
-- 100, 95, 195

select tl.shipment_id, tc.category, tl.credit, tl.debit, tl.date_created, tl.category_id
from
    transactions_ledger tl
    left join transaction_category tc on tc.id = tl.category_id
where
    tl.order_id = 17068672
order by tl.date_created asc;




-- inactive shipments query from calculate costs util
SELECT
  ord.id,
  scsl.shipment_id
FROM
  orders ord
  LEFT JOIN shipping_costs_sub_ledger scsl ON scsl.order_id = ord.id
  LEFT JOIN shipments shp ON shp.id = scsl.shipment_id
  LEFT JOIN marketplace_config mkt_conf ON mkt_conf.master_channel_id = ord.master_channel_id
WHERE
  scsl.id IS NOT NULL
  AND mkt_conf.id IS NOT NULL
  AND scsl.shipment_id IS NOT NULL
  AND shp.order_id IS NULL
  AND (
    (scsl.debit - scsl.credit) >= 1
    OR (scsl.debit - scsl.credit) <= -1
  )
  AND scsl.date_created > '2024-11-01'
GROUP BY
  ord.id,
  scsl.shipment_id

-- inactive shipments query from cleanup script


WITH
  inactive_sub_ledger_orders AS (
    select
      scsl.order_id,
      scsl.shipment_id
    from
      shipping_costs_sub_ledger scsl
      left join shipments shp on scsl.shipment_id = shp.id
      left join orders ord on scsl.order_id = ord.id
      left join marketplace_config mkt_conf on mkt_conf.master_channel_id = ord.master_channel_id
    where
      shp.order_id is null
      and mkt_conf.id is not null
      and (
        (scsl.debit - scsl.credit) >= 1
        or (scsl.debit - scsl.credit) <= -1
      )
      and scsl.shipment_id is not null
      and scsl.date_created > '2024-11-01'
    group by
        scsl.order_id,
        scsl.shipment_id
  )
select
  ord.id
from
  orders ord
where
  ord.id in (
    select
      order_id
    from
      inactive_sub_ledger_orders
  )
