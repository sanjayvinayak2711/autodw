# AutoDW

[![FastAPI](https://img.shields.io/badge/FastAPI-0.108+-green)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](https://opensource.org/licenses/MIT)

> **Transform CSV files into star schema structures for analytics**

---

## The Problem

Building data warehouse schemas manually requires:
- Understanding dimensional modeling concepts
- Writing ETL scripts for each data source
- Manually identifying fact vs dimension tables
- Maintaining documentation and metadata

AutoDW automates the initial schema classification and file organization to reduce setup time.

---

## Core Features

### Automated Schema Classification
- **Heuristic-based detection**: Uses column data types and row counts to classify tables
  - Tables with >50% numeric columns and >10 rows → Fact tables
  - Other tables → Dimension tables
- Prefixes output files (`fact_`/`dim_`) for clear identification
- Generates metadata README for each project

### Data Processing
- CSV and PDF file ingestion
- Automatic data type inference via Pandas
- File-level duplicate detection
- Row count validation and preview generation

### Web Interface
- Drag-and-drop file upload
- Project dashboard with table listings
- File preview and download capabilities
- Project management (create, view, delete)

### API
- RESTful endpoints for upload, build, and retrieval
- JSON responses with file metadata
- Project lifecycle management

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   Browser    │  │   HTTP CLI   │  │  External Apps  │  │
│  │  (Dashboard) │  │   (cURL)     │  │    (API)        │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Server                         │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │  /upload    │  │   /build    │  │  /api/projects   │  │
│  │ File Upload │  │ Schema Gen  │  │   List/Delete    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │  /preview   │  │  /download  │  │     /health      │  │
│  │ View Data   │  │ Get Files   │  │   Status Check   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Data Processing Layer                       │
│  ┌──────────────────┐  ┌─────────────────────────────────┐  │
│  │   Pandas Engine  │  │      Classification Logic       │  │
│  │  - CSV parsing   │  │  - Numeric column ratio check   │  │
│  │  - Type inference│  │  - Row count threshold (>10)   │  │
│  │  - PDF extraction│  │  - fact_/dim_ prefix assignment│  │
│  └──────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Storage Layer                          │
│  ┌────────────────────┐  ┌────────────────────────────┐  │
│  │   data/uploads/    │  │       data/output/         │  │
│  │  (Raw CSV/PDF)     │  │  ┌────────────────────┐   │  │
│  │                    │  │  │  project_{id}/     │   │  │
│  │                    │  │  │  ├── fact_*.csv      │   │  │
│  │                    │  │  │  ├── dim_*.csv       │   │  │
│  │                    │  │  │  └── README.txt      │   │  │
│  │                    │  │  └────────────────────┘   │  │
│  └────────────────────┘  └────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/sanjayvinayak2711/autodw.git
cd autodw

# Run with Docker
docker-compose up -d

# Open browser
open http://localhost:8000
```

---

## Performance Characteristics

Based on local testing with sample datasets:

| Dataset Size | Processing Time | Output Files |
|--------------|-----------------|--------------|
| 1K rows      | <1 second       | 1-2 tables   |
| 10K rows     | 1-2 seconds     | 1-2 tables   |
| 100K rows    | 3-5 seconds     | 1-2 tables   |

*Note: Performance depends on file complexity and hardware. PDF processing is slower than CSV.*

---

## API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main dashboard |
| POST | `/upload` | Upload CSV/PDF files |
| POST | `/build` | Generate star schema structure |
| GET | `/api/projects` | List all projects |
| GET | `/projects` | Projects page |
| DELETE | `/api/projects/{id}` | Delete project |
| GET | `/preview/{project_id}/{file}` | Preview file content |
| GET | `/download/{project_id}/{file}` | Download file |

### Example Usage

```python
import requests

# Upload a file
with open('sales.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload',
        files={'file': f}
    )

# Build the warehouse structure
response = requests.post('http://localhost:8000/build')
print(f"Project created: {response.json()['project_id']}")
```

---

## Classification Methodology

The system uses a rule-based heuristic for table classification:

1. **Fact Table Detection**: 
   - >50% of columns are numeric (int/float)
   - Row count > 10
   - Typical examples: sales transactions, event logs, measurements

2. **Dimension Table Detection**:
   - Default classification if fact conditions not met
   - Typical examples: customer lists, product catalogs, date tables

3. **Output Structure**:
   - Fact tables prefixed with `fact_`
   - Dimension tables prefixed with `dim_`
   - Metadata README generated per project

---

## Project Structure

```
AutoDW/
├── app.py                 # FastAPI application
├── docker-compose.yml     # Docker configuration
├── requirements.txt       # Python dependencies
├── static/                # Frontend assets
│   ├── css/
│   │   └── style.css     # Stylesheet
│   └── js/
│       └── script.js      # Frontend logic
├── templates/             # HTML templates
│   ├── index.html        # Main dashboard
│   └── projects.html     # Projects interface
└── data/                 # Data storage
    ├── uploads/          # Uploaded files
    └── output/           # Generated projects
```

---

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Upload test file
curl -X POST -F "file=@test.csv" http://localhost:8000/upload

# Build warehouse structure
curl -X POST http://localhost:8000/build
```

---

## Current Limitations

- **No database integration**: Outputs to CSV files only (no PostgreSQL/MySQL)
- **Single-file projects**: Each upload creates a separate project
- **Basic classification**: Heuristic-based, not ML-powered
- **No relationship detection**: Foreign keys must be defined manually
- **Local storage only**: No cloud persistence

---

## Roadmap

- [ ] Database integration (PostgreSQL/MySQL output)
- [ ] Multi-file project support
- [ ] Relationship inference between tables
- [ ] SQL DDL generation
- [ ] Cloud deployment templates (AWS/GCP/Azure)

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Connect

- GitHub: [@sanjayvinayak2711](https://github.com/sanjayvinayak2711)
