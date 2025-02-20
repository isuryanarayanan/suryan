WITH cte AS (
    SELECT unnest(ARRAY[14907719, 14929275, 14954528]::bigint[]) AS order_id
)
SELECT
    ms.id,
    ms.courier_name,
    ms.logo_url,
    cc.type,
    ms.weight_offset,
    ms.additional_weight_offset,
    ctc.zone_a,
    ctc.zone_b,
    ctc.zone_c,
    ctc.zone_d,
    ctc.zone_e,
    ctc.cod_min,
    ctc.cod_ratio,
    ctc.a_step,
    ctc.b_step,
    ctc.c_step,
    ctc.d_step,
    ctc.e_step,
    cdc.zone_a,
    cdc.zone_b,
    cdc.zone_c,
    cdc.zone_d,
    cdc.zone_e,
    cdc.cod_min,
    cdc.cod_ratio,
    cdc.a_step,
    cdc.b_step,
    cdc.c_step,
    cdc.d_step,
    cdc.e_step,
    CASE WHEN cmp.management_fee_static IS NOT NULL THEN
        cmp.management_fee_static
    WHEN cmp.management_fee IS NOT NULL THEN
        cmp.management_fee
    ELSE
        5
    END AS management_fee,
    mkt_conf.id
FROM
    master_couriers ms
    LEFT JOIN client_couriers clc ON clc.courier_id = ms.id
        AND clc.client_prefix = 'suryan'
    LEFT JOIN cost_to_clients ctc ON ctc.courier_id = ms.id
        AND ctc.client_prefix = 'suryan'
    LEFT JOIN client_default_cost cdc ON cdc.courier_id = ms.id
    LEFT JOIN couriers cc ON ms.courier_id = cc.id
    LEFT JOIN client_mapping cmp ON cmp.client_prefix = ctc.client_prefix
    LEFT JOIN orders o ON o.id IN (SELECT order_id FROM cte)
    LEFT JOIN marketplace_config mkt_conf ON mkt_conf.master_channel_id = o.master_channel_id
    LEFT JOIN client_mapping mkt_client_map ON mkt_conf.client_prefix = mkt_client_map.client_prefix
WHERE
    ms.courier_name ILIKE 'Delhivery'
    AND (ms.client_code = 'suryan'
        OR ms.integrated IS TRUE)
    AND clc.active = TRUE
    AND cdc.client_type IS NULL
    AND cdc.account_tier IS NULL