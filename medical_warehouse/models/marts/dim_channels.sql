{{
    config(
        materialized='table',
        schema='marts'
    )
}}

with channel_stats as (
    select
        channel_name,
        min(message_date) as first_post_date,
        max(message_date) as last_post_date,
        count(*) as total_posts,
        avg(views) as avg_views,
        avg(forwards) as avg_forwards,
        sum(case when has_media then 1 else 0 end) as posts_with_media,
        sum(views) as total_views,
        sum(forwards) as total_forwards
    from {{ ref('stg_telegram_messages') }}
    group by channel_name
)

select
    -- Surrogate key
    {{ dbt_utils.generate_surrogate_key(['channel_name']) }} as channel_key,
    
    -- Channel attributes
    channel_name,
    
    -- Activity metrics
    first_post_date,
    last_post_date,
    total_posts,
    posts_with_media,
    round(cast(posts_with_media as decimal) / nullif(total_posts, 0) * 100, 2) as media_percentage,
    
    -- Engagement metrics
    round(avg_views, 2) as avg_views,
    round(avg_forwards, 2) as avg_forwards,
    total_views,
    total_forwards,
    
    -- Derived metrics
    case 
        when total_posts >= 100 then 'high'
        when total_posts >= 50 then 'medium'
        else 'low'
    end as activity_level,
    
    -- Metadata
    current_timestamp as created_at,
    current_timestamp as updated_at
    
from channel_stats
