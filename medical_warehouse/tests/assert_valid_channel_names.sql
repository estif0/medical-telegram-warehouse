-- Test to ensure channel names are not empty or null
select
    channel_name,
    count(*) as count
from {{ ref('stg_telegram_messages') }}
where channel_name is null 
   or trim(channel_name) = ''
group by channel_name
