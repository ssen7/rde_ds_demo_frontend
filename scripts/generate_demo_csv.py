#!/usr/bin/env python3
"""Generate large demo CSV files for testing."""

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_csv(output_path: Path, num_rows: int, seed: int = 42):
    """Generate a demo CSV file with the specified number of rows.

    Columns:
    - id: sequential integer
    - date: random dates between 2020-01-01 and 2024-12-31
    - category: random category (A, B, C, D, E)
    - value: random float between 0 and 1000
    - description: random text
    """
    random.seed(seed)

    start_date = datetime(2020, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range_days = (end_date - start_date).days

    categories = ["A", "B", "C", "D", "E"]
    descriptions = [
        "Transaction processed",
        "Order completed",
        "Payment received",
        "Shipment dispatched",
        "Return initiated",
        "Refund processed",
        "Account updated",
        "Subscription renewed",
    ]

    print(f"Generating {num_rows:,} rows to {output_path}...")

    with open(output_path, "w") as f:
        # Header
        f.write("id,date,category,value,description\n")

        # Data rows
        for i in range(1, num_rows + 1):
            date = start_date + timedelta(days=random.randint(0, date_range_days))
            category = random.choice(categories)
            value = round(random.uniform(0, 1000), 2)
            description = random.choice(descriptions)

            f.write(f"{i},{date.strftime('%Y-%m-%d')},{category},{value},{description}\n")

            # Progress indicator
            if i % 500_000 == 0:
                print(f"  {i:,} rows written...")

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"Done! File size: {file_size_mb:.1f} MB")


def main():
    parser = argparse.ArgumentParser(description="Generate demo CSV files for testing")
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="demo_data.csv",
        help="Output file path (default: demo_data.csv)"
    )
    parser.add_argument(
        "-n", "--rows",
        type=int,
        default=1_000_000,
        help="Number of rows to generate (default: 1,000,000)"
    )
    parser.add_argument(
        "-s", "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )

    args = parser.parse_args()
    output_path = Path(args.output)

    # Create parent directories if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generate_csv(output_path, args.rows, args.seed)


if __name__ == "__main__":
    main()
