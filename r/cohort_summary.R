#!/usr/bin/env Rscript
# Demonstration only: research QA summaries for 100% synthetic inputs.
# Requires R plus tidyverse; no real clinical data or PHI may be used.
suppressPackageStartupMessages(library(tidyverse))
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) {
  stop('Usage: Rscript r/cohort_summary.R analysis_ready.csv site_summary.csv')
}
input <- args[[1]]
output <- args[[2]]

cohort <- readr::read_csv(input, show_col_types = FALSE)
required <- c('site_id', 'case_id', 'recipient_age', 'ebl_ml', 'anesthesia_minutes')
missing_columns <- setdiff(required, names(cohort))
if (length(missing_columns) > 0) {
  stop(paste('Required columns absent:', paste(missing_columns, collapse = ', ')))
}

# Confirm no duplicate case keys and quantify missingness before reporting.
if (anyDuplicated(cohort$case_id) > 0) stop('Duplicate case IDs present')
missingness <- cohort %>%
  summarise(across(all_of(required), ~sum(is.na(.x))))
print(missingness)

summary <- cohort %>%
  mutate(
    recipient_age = as.numeric(recipient_age),
    ebl_ml = as.numeric(ebl_ml),
    anesthesia_minutes = as.numeric(anesthesia_minutes)
  ) %>%
  group_by(site_id) %>%
  summarise(
    cases = n(),
    missing_ebl = sum(is.na(ebl_ml)),
    mean_age = mean(recipient_age, na.rm = TRUE),
    median_ebl_ml = median(ebl_ml, na.rm = TRUE),
    mean_anesthesia_minutes = mean(anesthesia_minutes, na.rm = TRUE),
    .groups = 'drop'
  )
readr::write_csv(summary, output)
message(paste('Wrote synthetic-only site summary to', output))
