#!/usr/bin/env python
"""
CLI runner for the Shopify ingestion pipeline.

Usage:
    python -m pipelines.run               # Run the pipeline once
    python -m pipelines.run --schedule     # Run with weekly schedule
"""
import argparse
import sys

from pipelines.pipeline import shopify_ingestion_pipeline


def main():
    parser = argparse.ArgumentParser(description="Run the Shopify ingestion pipeline")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Register a weekly schedule (requires a ZenML orchestrator that supports scheduling)",
    )
    args = parser.parse_args()

    if args.schedule:
        from zenml.config.schedule import Schedule

        schedule = Schedule(cron_expression="0 3 * * 1")  # Every Monday at 03:00 UTC
        shopify_ingestion_pipeline.with_options(schedule=schedule)()
        print("Pipeline scheduled: every Monday at 03:00 UTC")
    else:
        shopify_ingestion_pipeline()
        print("Pipeline run complete.")


if __name__ == "__main__":
    main()
