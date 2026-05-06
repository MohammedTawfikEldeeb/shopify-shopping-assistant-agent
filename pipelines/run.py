#!/usr/bin/env python
"""
CLI runner for the Shopify ingestion pipeline.

Usage:
    python -m pipelines.run               # Run the pipeline once (with cache)
    python -m pipelines.run --no-cache     # Run fresh, ignoring all cached steps
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
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable step caching and force a fresh run",
    )
    args = parser.parse_args()

    if args.no_cache:
        shopify_ingestion_pipeline.with_options(enable_cache=False)()
        print("Pipeline run complete (no cache).")
    elif args.schedule:
        from zenml.config.schedule import Schedule

        schedule = Schedule(cron_expression="0 3 * * 1")  # Every Monday at 03:00 UTC
        shopify_ingestion_pipeline.with_options(schedule=schedule)()
        print("Pipeline scheduled: every Monday at 03:00 UTC")
    else:
        shopify_ingestion_pipeline()
        print("Pipeline run complete.")


if __name__ == "__main__":
    main()
