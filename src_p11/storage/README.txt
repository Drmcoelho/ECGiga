# Storage Directory

This directory contains application data for the ECG Course API.

## Structure

- `reports/YYYY-MM/` - ECG reports organized by month
- `index/reports.idx.json` - Lightweight metadata index

## Notes

- This directory is created automatically by the application
- Contents should not be manually edited
- Individual report files are named `{report_id}.json`
- The index file enables efficient listing and searching

## Backup Considerations

When backing up the application:
- Include the entire `storage/` directory
- The index file can be rebuilt from individual report files if needed
- Monthly directories allow for easy archival strategies