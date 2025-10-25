# ECG Course Archive Extraction Workflow

This repository includes a GitHub Actions workflow that automatically extracts the `ECG_Curso_Megaprojeto_p3b_append.zip` file.

## How to Use

### Manual Trigger
1. Go to the **Actions** tab in your GitHub repository
2. Select **"Unzip ECG Course Archive"** workflow
3. Click **"Run workflow"** button
4. Click **"Run workflow"** again to confirm

### Automatic Trigger
The workflow also runs automatically when you push to the `main` branch, but only if the ZIP file still exists (making it idempotent).

## What It Does

The workflow will:
1. ✅ Check if `ECG_Curso_Megaprojeto_p3b_append.zip` exists
2. 📦 List the ZIP file contents for logging
3. 🚀 Extract files to a temporary directory
4. 🔄 Safely move files to the repository root
5. ⚠️ Handle conflicts by moving conflicting files to `extracted_conflicts/`
6. 💾 Commit and push the extracted files

## File Structure

After extraction, you'll get:
- `README.md` - Main project documentation
- `docs/` - Documentation files
- `cli_app/` - Command line application
- `web_app/` - Web application
- `notebooks/` - Jupyter notebooks
- `assets/` - Project assets
- And more...

## Conflict Handling

If any extracted files would overwrite existing files, the workflow:
- Keeps your existing files unchanged
- Moves the conflicting extracted files to `extracted_conflicts/`
- Adds timestamps to conflicting filenames for easy identification

## Requirements

- Repository must have `ECG_Curso_Megaprojeto_p3b_append.zip` at the root
- Workflow needs write permissions (handled automatically by GitHub Actions)