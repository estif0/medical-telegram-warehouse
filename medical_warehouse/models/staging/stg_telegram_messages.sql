{{
    config(
        materialized='view',
        schema='staging'
    )
}}

with source_data as (
    select
        message_id,
        channel_name,
        message_date,
        message_text,
        has_media,
        media_type,
        image_path,
        views,
        forwards,
        replies,
        scraped_at
    from {{ source('raw', 'telegram_messages') }}
),

cleaned_data as (
    select
        -- Primary key
        message_id::bigint as message_id,
        
        -- Channel information
        lower(trim(channel_name)) as channel_name,
        
        -- Message content
        message_date::timestamp as message_date,
        trim(message_text) as message_text,
        length(trim(coalesce(message_text, ''))) as message_length,
        
        -- Media information
        coalesce(has_media, false) as has_media,
        media_type,
        image_path,
        
        -- Engagement metrics
        coalesce(views, 0)::integer as views,
        coalesce(forwards, 0)::integer as forwards,
        coalesce(replies, 0)::integer as replies,
        
        -- Metadata
        scraped_at::timestamp as scraped_at,
        
        -- Calculated fields
        case 
            when has_media = true then 'with_media'
            else 'text_only'
        end as content_type,
        
        case 
            when length(trim(coalesce(message_text, ''))) = 0 then true
            else false
        end as is_empty_text
        
    from source_data
    where message_id is not null
      and channel_name is not null
      and message_date is not null
      -- Filter out future messages
      and message_date <= current_timestamp
      -- Filter out messages with invalid metrics
      and views >= 0
      and forwards >= 0
)

select * from cleaned_data
