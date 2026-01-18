-- Test to ensure no messages have dates in the future
select
    message_id,
    channel_name,
    message_date
from {{ ref('stg_telegram_messages') }}
where message_date > current_timestamp
