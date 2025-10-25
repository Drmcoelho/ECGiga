# ECGCourse — Interactive ECG Learning Platform

[![CI](https://github.com/Drmcoelho/ECGiga/actions/workflows/ci.yml/badge.svg)](https://github.com/Drmcoelho/ECGiga/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

ECGCourse is a comprehensive interactive platform for ECG (electrocardiogram) education and analysis, combining computer vision, machine learning, and clinical expertise to provide automated ECG interpretation and educational tools.

## 🚀 Quick Start

### Installation

```bash
# Basic installation
pip install -e .

# With all optional dependencies
pip install -e ".[all]"

# Development installation
pip install -e ".[dev]"
```

### Basic Usage

```bash
# Analyze ECG values
ecgcourse analyze values --qt 400 --rr 800 --lead-i 0.5 --avf 1.2 --verbose

# Run interactive quiz
ecgcourse quiz run samples/quiz/example.json

# Process ECG image (placeholder)
ecgcourse ingest image samples/ecg_images/synthetic_12lead.png --auto-grid --rpeaks-robust

# Computer vision operations
ecgcourse cv deskew input_image.png --output corrected_image.png

# Asset management
ecgcourse assets list-manifests
```

## 📋 Features

### Core Capabilities

- **📊 ECG Analysis**: Automated interval measurement (PR, QRS, QT), QTc calculation, and axis determination
- **🎯 Interactive Quizzes**: Structured learning with multiple question banks and progress tracking
- **🖼️ Image Processing**: ECG image ingestion with deskewing, grid detection, and signal extraction
- **🧠 R-peak Detection**: Robust Pan-Tompkins-based algorithm for heart rate analysis
- **📈 Benchmarking**: Synthetic ECG generation and performance evaluation tools
- **🔄 Schema Migration**: Automatic migration of legacy reports to current format

### Modular CLI Architecture

The CLI is organized into focused modules:

- **`analyze`**: ECG value analysis and calculations
- **`quiz`**: Interactive learning and assessment
- **`ingest`**: ECG image processing and analysis
- **`cv`**: Computer vision operations (deskew, grid detection, segmentation)
- **`assets`**: Asset management and downloads

## 📖 Usage Examples

### ECG Value Analysis

```bash
# Analyze from command line parameters
ecgcourse analyze values --pr 160 --qrs 90 --qt 400 --rr 800 --sexo F --report

# Analyze from JSON file
ecgcourse analyze values samples/values/exemplo1.json --verbose

# Calculate QTc with different heart rates
ecgcourse analyze values --qt 380 --fc 75 --sexo M
```

### Interactive Quizzes

```bash
# Single quiz item
ecgcourse quiz run quiz/bank/p2/p2_0001.json

# Quiz bank session with reporting
ecgcourse quiz bank quiz/bank/p2/ --report --shuffle

# Validate quiz schema
ecgcourse quiz validate quiz/bank/exemplo_arrtimias.json
```

### ECG Image Processing

```bash
# Basic image ingestion
ecgcourse ingest image ecg_sample.png --auto-grid --normalize

# Batch processing
ecgcourse ingest batch input_images/ output_results/ --rpeaks-robust --intervals
```

### Computer Vision Operations

```bash
# Deskew ECG image
ecgcourse cv deskew rotated_ecg.png --method auto --angle-range 10

# Grid detection
ecgcourse cv grid-detect ecg_with_grid.png --min-period 10 --max-period 30

# Lead segmentation
ecgcourse cv segment-leads ecg_12lead.png --layout 3x4

# R-peak detection from image
ecgcourse cv detect-rpeaks ecg_image.png --lead II --method robust
```

### Schema Migration

```bash
# Migrate single report
python scripts/python/migrate_reports.py --in legacy_report.json --out migrated_report.json

# Migrate directory
python scripts/python/migrate_reports.py --in legacy_reports/ --out migrated_reports/ --force

# Generate migration report
python scripts/python/migrate_reports.py --in reports/ --out migrated/ --report migration_log.json --validate
```

### Benchmarking

```bash
# Quick benchmark with defaults
python scripts/python/benchmark_ecg.py

# Custom parameters
python scripts/python/benchmark_ecg.py --heart-rates 60 80 100 --noise-levels 0.01 0.05 0.1

# Save detailed results
python scripts/python/benchmark_ecg.py --out benchmark_results.json --trials 5 --verbose
```

## 🔧 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/Drmcoelho/ECGiga.git
cd ECGiga

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest -xvs

# Run linting
ruff check .
ruff format .
black --check .
```

### Project Structure

```
ECGiga/
├── cli_app/ecgcourse/          # Modular CLI application
│   ├── __main__.py             # Main entry point
│   ├── cli_root.py             # Root command dispatcher
│   ├── analyze_cli.py          # ECG analysis commands
│   ├── quiz_cli.py             # Quiz management
│   ├── ingest_cli.py           # Image ingestion
│   ├── cv_cli.py               # Computer vision operations
│   ├── assets_cli.py           # Asset management
│   ├── logging_utils.py        # Centralized logging
│   └── config.py               # Configuration constants
├── cv/                         # Computer vision modules
├── quiz/                       # Quiz data and schemas
├── reporting/                  # Report schemas and validation
├── scripts/python/             # Utility scripts
├── tests/                      # Test suite
├── samples/                    # Sample data
└── docs/                       # Documentation
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/test_rpeaks.py -v
pytest tests/test_intervals.py -v
pytest tests/test_migration.py -v

# Run with coverage
pytest --cov=cli_app --cov=scripts --cov-report=html

# Run only fast tests
pytest -m "not slow"
```

### Continuous Integration

The project uses GitHub Actions for CI with:

- ✅ Python 3.11 and 3.12 matrix testing
- ✅ Linting with `ruff` and `black`
- ✅ Test execution with `pytest`
- ✅ Coverage reporting
- ✅ CLI smoke tests

## 📊 Project Roadmap

### ✅ Completed (p0-p7, current)
- [x] Core ECG analysis algorithms
- [x] Interactive quiz system
- [x] Basic image processing pipeline
- [x] R-peak detection (Pan-Tompkins)
- [x] Interval extraction algorithms
- [x] Modular CLI architecture
- [x] Comprehensive test suite
- [x] CI/CD pipeline setup
- [x] Schema migration utility
- [x] Synthetic benchmarking

### 🚧 In Progress (p8-p11)
- [ ] Advanced OCR for lead labels
- [ ] Machine learning models training
- [ ] Web dashboard interface
- [ ] Real-time signal processing
- [ ] Clinical validation studies

### 🔮 Planned (p12+)
- [ ] Mobile application
- [ ] Cloud deployment
- [ ] Multi-language support
- [ ] Advanced arrhythmia detection
- [ ] Integration with PACS systems

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and add tests
4. Ensure CI passes (`pytest` and `ruff check .`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Create a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add type hints for all functions
- Write comprehensive tests for new features
- Update documentation for API changes
- Use descriptive commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏥 Medical Disclaimer

This software is for educational and research purposes only. It is not intended for clinical diagnosis or patient care. Always consult qualified medical professionals for clinical decisions.

## 📧 Support

- 📖 Documentation: [GitHub Wiki](https://github.com/Drmcoelho/ECGiga/wiki)
- 🐛 Issues: [GitHub Issues](https://github.com/Drmcoelho/ECGiga/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/Drmcoelho/ECGiga/discussions)

---

**ECGCourse** — Empowering medical education through technology 🚀