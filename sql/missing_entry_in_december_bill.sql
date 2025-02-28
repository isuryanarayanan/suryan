-- select the sub ledger for the awb 80625497982

SELECT scsl.*
FROM
    shipping_costs_sub_ledger scsl
    LEFT JOIN shipments shp ON shp.id = scsl.shipment_id
WHERE
    shp.awb = '80625497982';

SELECT tl.*
FROM
    transactions_ledger tl
    LEFT JOIN shipping_costs_sub_ledger scsl ON scsl.id = tl.shipping_costs_sub_ledger_id
    LEFT JOIN shipments shp ON shp.id = scsl.shipment_id
WHERE
    shp.awb = '80625497982'