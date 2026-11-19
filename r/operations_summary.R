#!/usr/bin/env Rscript
# Independent operations analytics demonstration, never real customer information.
# To run: Rscript r/operations_summary.R outputs/clean_tickets.csv outputs/r_region_summary.csv
suppressPackageStartupMessages(library(tidyverse))
args <- commandArgs(trailingOnly = TRUE)
input <- if (length(args) >= 1) args[[1]] else 'outputs/clean_tickets.csv'
output <- if (length(args) >= 2) args[[2]] else 'outputs/r_region_summary.csv'

tickets <- read_csv(input, show_col_types = FALSE,
                    col_types = cols(ticket_id = col_character(),
                                     region = col_character(),
                                     .default = col_guess()))
stopifnot('ticket_id' %in% names(tickets))
stopifnot('region' %in% names(tickets))
stopifnot(!anyDuplicated(tickets$ticket_id))
stopifnot(!any(is.na(tickets$region)))

result <- tickets %>%
  mutate(ticket_day = as.Date(ticket_day),
         sla_breached = as.logical(sla_breached),
         resolution_minutes = as.numeric(resolution_minutes),
         month = format(ticket_day, '%Y-%m')) %>%
  group_by(region, month) %>%
  summarise(ticket_count = n_distinct(ticket_id),
            missing_resolution = sum(is.na(resolution_minutes)),
            breach_rate = mean(sla_breached, na.rm = TRUE),
            p50_resolution_minutes = median(resolution_minutes, na.rm = TRUE),
            .groups = 'drop')

stopifnot(sum(result$ticket_count) == nrow(tickets))
write_csv(result, output, na = '')
message(sprintf('Checked %d ticket IDs across %d region-month groups; saved %s',
                nrow(tickets), nrow(result), output))
