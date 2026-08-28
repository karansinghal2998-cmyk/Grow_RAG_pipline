# Phase 2 Embedding Verification & Vector Space Report

* **Total Indexed Chunks**: `25`
* **Embedding Model**: `BAAI/bge-small-en-v1.5` (`384` dimensions)
* **Vector Space Metric**: Cosine Similarity (`hnsw:space = cosine`)
* **Average L2 Norm**: `1.000000` (Normalized embeddings enabled)

## Indexed Chunk Vectors Overview

| Index | Chunk ID | Scheme Name | Chunk Type | Dim | L2 Norm | Min | Max | First 5 Dims |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `hdfc-gold-etf-fund-of-fund-direct-plan-growth_chunk_overview` | HDFC Gold ETF Fund of Fund Direct Plan Growth | `overview` | 384 | `1.0000` | `-0.2841` | `0.3487` | `[0.019, -0.081, -0.030, 0.036, -0.034]` |
| 2 | `hdfc-gold-etf-fund-of-fund-direct-plan-growth_chunk_expense_ratio` | HDFC Gold ETF Fund of Fund Direct Plan Growth | `expense_ratio` | 384 | `1.0000` | `-0.2485` | `0.3527` | `[0.018, -0.064, -0.029, 0.028, 0.012]` |
| 3 | `hdfc-gold-etf-fund-of-fund-direct-plan-growth_chunk_exit_load` | HDFC Gold ETF Fund of Fund Direct Plan Growth | `exit_load` | 384 | `1.0000` | `-0.2961` | `0.3504` | `[-0.016, -0.088, -0.018, 0.034, -0.005]` |
| 4 | `hdfc-gold-etf-fund-of-fund-direct-plan-growth_chunk_sip_and_nav` | HDFC Gold ETF Fund of Fund Direct Plan Growth | `sip_and_nav` | 384 | `1.0000` | `-0.2857` | `0.3268` | `[0.021, -0.072, -0.040, 0.002, -0.031]` |
| 5 | `hdfc-gold-etf-fund-of-fund-direct-plan-growth_chunk_statement_download` | HDFC Gold ETF Fund of Fund Direct Plan Growth | `statement_download` | 384 | `1.0000` | `-0.3169` | `0.3593` | `[0.010, -0.061, -0.022, 0.063, -0.001]` |
| 6 | `hdfc-large-cap-fund-direct-growth_chunk_overview` | HDFC Large Cap Fund Direct Growth | `overview` | 384 | `1.0000` | `-0.2957` | `0.3620` | `[0.013, -0.081, -0.051, -0.008, -0.029]` |
| 7 | `hdfc-large-cap-fund-direct-growth_chunk_expense_ratio` | HDFC Large Cap Fund Direct Growth | `expense_ratio` | 384 | `1.0000` | `-0.2682` | `0.3460` | `[0.012, -0.061, -0.043, -0.018, 0.020]` |
| 8 | `hdfc-large-cap-fund-direct-growth_chunk_exit_load` | HDFC Large Cap Fund Direct Growth | `exit_load` | 384 | `1.0000` | `-0.3098` | `0.3427` | `[-0.019, -0.085, -0.029, -0.007, 0.004]` |
| 9 | `hdfc-large-cap-fund-direct-growth_chunk_sip_and_nav` | HDFC Large Cap Fund Direct Growth | `sip_and_nav` | 384 | `1.0000` | `-0.3012` | `0.3311` | `[0.014, -0.059, -0.054, -0.046, -0.024]` |
| 10 | `hdfc-large-cap-fund-direct-growth_chunk_statement_download` | HDFC Large Cap Fund Direct Growth | `statement_download` | 384 | `1.0000` | `-0.3350` | `0.3557` | `[0.006, -0.061, -0.027, 0.022, 0.005]` |
| 11 | `hdfc-small-cap-fund-direct-growth_chunk_overview` | HDFC Small Cap Fund Direct Growth | `overview` | 384 | `1.0000` | `-0.2787` | `0.3697` | `[0.021, -0.070, -0.048, -0.023, -0.025]` |
| 12 | `hdfc-small-cap-fund-direct-growth_chunk_expense_ratio` | HDFC Small Cap Fund Direct Growth | `expense_ratio` | 384 | `1.0000` | `-0.2505` | `0.3624` | `[0.019, -0.052, -0.041, -0.034, 0.030]` |
| 13 | `hdfc-small-cap-fund-direct-growth_chunk_exit_load` | HDFC Small Cap Fund Direct Growth | `exit_load` | 384 | `1.0000` | `-0.2932` | `0.3552` | `[-0.012, -0.077, -0.026, -0.026, 0.007]` |
| 14 | `hdfc-small-cap-fund-direct-growth_chunk_sip_and_nav` | HDFC Small Cap Fund Direct Growth | `sip_and_nav` | 384 | `1.0000` | `-0.2835` | `0.3351` | `[0.020, -0.052, -0.043, -0.060, -0.012]` |
| 15 | `hdfc-small-cap-fund-direct-growth_chunk_statement_download` | HDFC Small Cap Fund Direct Growth | `statement_download` | 384 | `1.0000` | `-0.3171` | `0.3681` | `[0.016, -0.052, -0.020, 0.011, 0.011]` |
| 16 | `hdfc-silver-etf-fof-direct-growth_chunk_overview` | HDFC Silver ETF FoF Direct Growth | `overview` | 384 | `1.0000` | `-0.2923` | `0.3370` | `[0.027, -0.073, -0.049, -0.016, -0.002]` |
| 17 | `hdfc-silver-etf-fof-direct-growth_chunk_expense_ratio` | HDFC Silver ETF FoF Direct Growth | `expense_ratio` | 384 | `1.0000` | `-0.2545` | `0.3262` | `[0.029, -0.058, -0.053, -0.025, 0.056]` |
| 18 | `hdfc-silver-etf-fof-direct-growth_chunk_exit_load` | HDFC Silver ETF FoF Direct Growth | `exit_load` | 384 | `1.0000` | `-0.3045` | `0.3290` | `[-0.002, -0.076, -0.032, -0.017, 0.029]` |
| 19 | `hdfc-silver-etf-fof-direct-growth_chunk_sip_and_nav` | HDFC Silver ETF FoF Direct Growth | `sip_and_nav` | 384 | `1.0000` | `-0.2964` | `0.3171` | `[0.032, -0.065, -0.053, -0.042, 0.003]` |
| 20 | `hdfc-silver-etf-fof-direct-growth_chunk_statement_download` | HDFC Silver ETF FoF Direct Growth | `statement_download` | 384 | `1.0000` | `-0.3195` | `0.3477` | `[0.018, -0.058, -0.033, 0.019, 0.022]` |
| 21 | `hdfc-mid-cap-fund-direct-growth_chunk_overview` | HDFC Mid Cap Fund Direct Growth | `overview` | 384 | `1.0000` | `-0.2891` | `0.3814` | `[0.009, -0.067, -0.039, -0.021, -0.040]` |
| 22 | `hdfc-mid-cap-fund-direct-growth_chunk_expense_ratio` | HDFC Mid Cap Fund Direct Growth | `expense_ratio` | 384 | `1.0000` | `-0.2603` | `0.3710` | `[0.002, -0.048, -0.029, -0.030, 0.007]` |
| 23 | `hdfc-mid-cap-fund-direct-growth_chunk_exit_load` | HDFC Mid Cap Fund Direct Growth | `exit_load` | 384 | `1.0000` | `-0.2998` | `0.3617` | `[-0.026, -0.074, -0.019, -0.020, -0.012]` |
| 24 | `hdfc-mid-cap-fund-direct-growth_chunk_sip_and_nav` | HDFC Mid Cap Fund Direct Growth | `sip_and_nav` | 384 | `1.0000` | `-0.2930` | `0.3495` | `[0.010, -0.050, -0.044, -0.056, -0.033]` |
| 25 | `hdfc-mid-cap-fund-direct-growth_chunk_statement_download` | HDFC Mid Cap Fund Direct Growth | `statement_download` | 384 | `1.0000` | `-0.3242` | `0.3690` | `[0.004, -0.044, -0.011, 0.010, -0.006]` |