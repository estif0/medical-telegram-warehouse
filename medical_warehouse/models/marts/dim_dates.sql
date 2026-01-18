{{
    config(
        materialized='table',
        schema='marts'
    )
}}

with date_spine as (
    -- Generate dates from earliest message to today
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2020-01-01' as date)",
        end_date="cast(current_date + interval '1 year' as date)"
    )}}
),

date_dimension as (
    select
        date_day as full_date,
        
        -- Date components
        extract(year from date_day) as year,
        extract(quarter from date_day) as quarter,
        extract(month from date_day) as month,
        extract(week from date_day) as week_of_year,
        extract(day from date_day) as day_of_month,
        extract(dow from date_day) as day_of_week,
        
        -- Formatted strings
        to_char(date_day, 'Month') as month_name,
        to_char(date_day, 'Mon') as month_abbr,
        to_char(date_day, 'Day') as day_name,
        to_char(date_day, 'Dy') as day_abbr,
        to_char(date_day, 'YYYY-MM-DD') as date_string,
        to_char(date_day, 'YYYY-MM') as year_month,
        to_char(date_day, 'YYYY-Q') as year_quarter,
        
        -- Boolean flags
        case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend,
        case when extract(day from date_day) = 1 then true else false end as is_month_start,
        case when date_day = date_trunc('month', date_day) + interval '1 month' - interval '1 day' 
             then true else false end as is_month_end,
        case when extract(month from date_day) in (1, 7) and extract(day from date_day) = 1 
             then true else false end as is_quarter_start
        
    from date_spine
)

select
    -- Surrogate key
    {{ dbt_utils.generate_surrogate_key(['full_date']) }} as date_key,
    
    -- All attributes
    full_date,
    year,
    quarter,
    month,
    week_of_year,
    day_of_month,
    day_of_week,
    month_name,
    month_abbr,
    day_name,
    day_abbr,
    date_string,
    year_month,
    year_quarter,
    is_weekend,
    is_month_start,
    is_month_end,
    is_quarter_start
    
from date_dimension
