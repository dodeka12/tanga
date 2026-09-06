# Changes since version 1.17.0 (2.0.0-rc2)

## New Features
- **Configurable CSV delimiter & decimal separator** — `TableView.to_csv` /
  `from_csv` (and `Table.to_csv` / `from_csv`) now take `delimiter` and
  `decimal_separator`. Import auto-detects the delimiter (`;` vs `,`) and
  decimal separator (`,` vs `.`) so German/European CSV files load without
  configuration, normalizing numbers to the canonical `.` decimal form; both
  parameters can be overridden explicitly, and export defaults to the `,`/`.`
  (US) dialect.
