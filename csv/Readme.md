# CSV Converter

`csv-converter.py` pivots the sample data inside `dataset/dataset.csv` into a list-of-dictionaries JSON payload that is saved as `submission.json`. The helper keeps the schema intact and prints the dataframe so you can quickly verify the CSV was parsed correctly.

## Features

- Loads `dataset/dataset.csv` with `pandas.read_csv` and keeps the original column order.
- Converts every row into a JSON object (list of dictionaries) and writes the formatted result to `submission.json`.
- Prints the dataframe so developers can spot parsing issues before they propagate to the JSON output.

## How to Run

1. Install the dependency: `pip install pandas`.
2. Make sure `converters/dataset/dataset.csv` is populated with the latest rows.
3. Run `python converters/csv-converter.py` from the repository root.
4. Review `submission.json` to confirm the conversion and share it with downstream tooling.

## Usage Example

```
$ python converters/csv-converter.py
>      id     name    value
>  0    1  Example  123.45
>  1    2  Sample   678.90
> [2 rows x 3 columns]
```

The printed dataframe confirms the columns that were read and lets you know if the CSV parser encountered any surprises before writing `submission.json`.
