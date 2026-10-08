"""Small data quality assertions. A failed check stops the pipeline."""


class DataQualityError(Exception):
    pass


def expect(condition, message):
    if not condition:
        raise DataQualityError(message)


def assert_min_rows(df, n, table):
    expect(len(df) >= n, f"{table}: expected at least {n} rows, got {len(df)}")


def assert_unique(df, col, table):
    dupes = df[col].duplicated().sum()
    expect(dupes == 0, f"{table}.{col}: {dupes} duplicate values")


def assert_not_null(df, col, table):
    nulls = df[col].isna().sum()
    expect(nulls == 0, f"{table}.{col}: {nulls} null values")


def assert_between(df, col, low, high, table):
    bad = (~df[col].between(low, high)).sum()
    expect(bad == 0, f"{table}.{col}: {bad} values outside [{low}, {high}]")


def assert_foreign_key(df, col, ref_df, ref_col, table):
    orphans = (~df[col].isin(ref_df[ref_col])).sum()
    expect(orphans == 0, f"{table}.{col}: {orphans} values not found in {ref_col}")
