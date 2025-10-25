# ECGiga - ECG Course Platform

An educational platform for ECG analysis featuring command-line tools, web interface, and computer vision algorithms for ECG image processing.

## Quick Setup

```bash
# Clone and install dependencies
git clone https://github.com/Drmcoelho/ECGiga
cd ECGiga
pip install -r requirements.txt

# Run tests
pytest -q

# Test CLI commands
python -m cli_app.ecgcourse.cli analyze values --qt 400 --rr 1000 --lead-i 5 --avf -3
python -m cli_app.ecgcourse.cli ingest image samples/ecg_images/synthetic_12lead.png --report

# Launch Dash web app
python web_app/dash_app/app.py
# Then visit http://127.0.0.1:8050
```

## Project Structure

- **cli_app/ecgcourse/** - Command-line interface for ECG analysis
- **web_app/dash_app/** - Dash web application for interactive ECG processing
- **cv/** - Computer vision algorithms (deskew, segmentation, R-peak detection, etc.)
- **quiz/** - Quiz generation and MCQ framework
- **reporting/schema/** - JSON schemas for structured reports (v0.1 - v0.4)
- **samples/** - Sample ECG images and metadata for testing
- **tests/** - Automated tests for core functionality

## Features

### CLI Commands
- **analyze values** - Calculate QTc, axis classification from structured data
- **ingest image** - Process ECG images with computer vision pipeline
- **cv** - Computer vision operations (calibration, segmentation, R-peak detection)
- **quiz** - Generate and run MCQ quizzes
- **assets** - Asset management and preprocessing

### Web Interface
- Upload ECG images (PNG/JPG)
- Optional deskew and normalization
- 12-lead segmentation with overlay visualization
- R-peak detection and interval analysis
- QTc calculator

### Computer Vision Pipeline
- Grid period estimation and calibration
- Image deskewing and normalization
- 12-lead layout detection and segmentation
- R-peak detection (basic and robust Pan-Tompkins)
- PR/QRS/QT interval estimation

## Testing

```bash
# Run all tests
pytest

# Test specific functionality
python -m cli_app.ecgcourse.cli analyze values --help
python -m cli_app.ecgcourse.cli ingest --help
python -m cli_app.ecgcourse.cli cv --help
```

## Development Roadmap

See the original comprehensive documentation (README_original.md) for detailed development phases and `docs/` directory for:
- Architecture overview (`arquitetura.md`)
- Development guides (`dev_*.md`)
- Asset pipeline (`p3b_assets.md`, `p3c_assets_pipeline.md`)
- Quiz system guide (`quiz_guide.md`)

## Next Steps

1. CI/CD workflow implementation
2. Extended R-peak accuracy metrics  
3. Logger centralization
4. CLI modular architecture refinement

For detailed implementation notes, see individual changelog files in `docs/p*_changelog.md`.