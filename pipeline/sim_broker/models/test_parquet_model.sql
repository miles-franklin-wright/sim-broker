cat <<'EOF' > models/test_parquet_model.sql
{{ config(materialized='table') }}

select *
from read_parquet('{{ project_root }}/lake/bronze/test.parquet')
EOF