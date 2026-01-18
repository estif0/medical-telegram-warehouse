{{
    config(
        materialized='table',
        schema='marts'
    )
}}

with messages as (
    select * from {{ ref('stg_telegram_messages') }}
),

channels as (
    select 
        channel_key,
        channel_name
    from {{ ref('dim_channels') }}
),

dates as (
    select
        date_key,
        full_date
    from {{ ref('dim_dates') }}
)

select
    -- Primary key
    m.message_id,
    
    -- Foreign keys
    c.channel_key,
    d.date_key,
    
    -- Message attributes
    m.message_text,
    m.message_length,
    m.content_type,
    m.has_media,
    m.media_type,
    m.image_path,
    
    -- Engagement metrics
    m.views,
    m.forwards,
    m.replies,
    
    -- Calculated metrics
    case 
        when m.views > 0 then round(cast(m.forwards as decimal) / m.views * 100, 2)
        else 0
    end as forward_rate,
    
    case 
        when m.views > 0 then round(cast(m.replies as decimal) / m.views * 100, 2)
        else 0
    end as reply_rate,
    
    -- Engagement category
    case 
        when m.views >= 1000 then 'high'
        when m.views >= 100 then 'medium'
        when m.views >= 10 then 'low'
        else 'minimal'
    end as engagement_level,
    
    -- Timestamps
    m.message_date,
    m.scraped_at,
    
    -- Metadata
    current_timestamp as created_at
    
from messages m
inner join channels c on m.channel_name = c.channel_name
inner join dates d on date(m.message_date) = d.full_date
