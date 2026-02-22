# 🏗️ AutoDW - Automated Data Warehouse

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)

## ✨ **The Problem It Solves**
Data engineers waste **40% of their time** on manual warehouse setup. AutoDW automates it in **30 seconds**.

## 🚀 **What It Does**
Upload CSVs → Get a production-ready dimensional warehouse automatically.

```bash
# One command to run everything
docker-compose up --build

# Upload your data
curl -X POST http://localhost:8000/upload -F "file=@sales.csv"

# Get your warehouse
curl -X POST http://localhost:8000/build