#!/usr/bin/env python3
import argparse
import json
import os
import sys

import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.gui_helpers import FieldSpec, build_form, render_output, run_script_capture
from utils.output_helpers import get_output_base_dir


def convert_csv_to_json(input_path: str, output_path: str) -> None:
    df = pd.read_csv(input_path)
    submission = df.to_dict(orient="records")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(submission, file, indent=4)

    print(f"Wrote JSON to: {output_path}")
    print(df)


def default_input_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset", "dataset.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a CSV file to JSON using pandas.",
    )
    parser.add_argument(
        "--input",
        default=default_input_path(),
        help="Path to the CSV file to convert.",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(get_output_base_dir(), "submission.json"),
        help="Output JSON file path.",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the GUI.",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def should_launch_gui() -> bool:
    return "--cli" not in sys.argv and ("--gui" in sys.argv or len(sys.argv) == 1)


def launch_gui() -> None:
    fields = [
        FieldSpec(key="input", label="Input CSV file", field_type="file", default=default_input_path()),
        FieldSpec(
            key="output",
            label="Output JSON file",
            field_type="save",
            default=os.path.join(get_output_base_dir(), "submission.json"),
        ),
    ]

    def on_submit(values, output_widget):
        args = ["--input", values["input"], "--output", values["output"]]
        code, stdout, stderr = run_script_capture(__file__, args)
        if code != 0 and not stderr:
            stderr = f"Command failed with exit code {code}."
        render_output(output_widget, stdout, stderr)

    build_form("CSV to JSON Converter", fields, on_submit)


def main() -> None:
    if should_launch_gui():
        launch_gui()
        return

    args = parse_args()
    convert_csv_to_json(args.input, args.output)


if __name__ == "__main__":
    main()
