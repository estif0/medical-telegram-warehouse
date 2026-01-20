"""
Fact table for YOLO image detections.

This model stores object detection results from YOLOv8 analysis,
joined with channel and date dimensions for analytical queries.
"""

WITH detection_raw AS (
    SELECT
        message_id,
        channel_name,
        image_path,
        detected_class,
        confidence,
        image_category,
        processed_at
    FROM {{ source('raw', 'image_detections') }}
),

messages AS (
    SELECT * FROM {{ ref('fct_messages') }}
),

channels AS (
    SELECT * FROM {{ ref('dim_channels') }}
),

dates AS (
    SELECT * FROM {{ ref('dim_dates') }}
),

final AS (
    SELECT
        -- Generate surrogate key for detection
        {{ dbt_utils.generate_surrogate_key(['det.message_id', 'det.detected_class', 'det.confidence']) }} AS detection_key,
        
        -- Foreign keys
        msg.message_id,
        ch.channel_key,
        dt.date_key,
        
        -- Detection attributes
        det.detected_class,
        det.confidence,
        det.image_category,
        det.image_path,
        
        -- Metadata
        det.processed_at,
        CURRENT_TIMESTAMP AS loaded_at
        
    FROM detection_raw AS det
    INNER JOIN messages AS msg
        ON det.message_id = msg.message_id
    INNER JOIN channels AS ch
        ON msg.channel_key = ch.channel_key
    INNER JOIN dates AS dt
        ON msg.date_key = dt.date_key
)

SELECT * FROM final
