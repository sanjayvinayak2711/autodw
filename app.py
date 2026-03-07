"""
AutoDW - Automated Data Warehouse with Browser Dashboard
Run in terminal: docker-compose up
Click the link: http://localhost:8001
"""

import os
import uuid
import pandas as pd
import webbrowser
import threading
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import json

# ============================================================================
# SETUP
# ============================================================================

app = FastAPI(title="AutoDW", version="1.0.0")
UPLOAD_DIR = "data/uploads"
OUTPUT_DIR = "data/output"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# ============================================================================
# MODELS
# ============================================================================

class UploadResponse(BaseModel):
    filename: str
    rows: int
    columns: List[str]
    file_size: int
    preview: List[Dict[str, Any]]

class BuildResponse(BaseModel):
    project_id: str
    status: str
    fact_tables: List[str]
    dimension_tables: List[str]
    relationships: int
    message: str
    output_files: List[str]

class FileInfo(BaseModel):
    name: str
    size: int
    rows: int
    columns: int
    modified: str

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main dashboard - opens in browser"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    return {"status": "healthy", "time": datetime.now().isoformat()}

@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV file"""
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, "Only CSV files allowed")
    
    # Save file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    content = await file.read()
    file_size = len(content)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Read and analyze
    df = pd.read_csv(file_path)
    preview = df.head(5).to_dict(orient='records')
    
    return UploadResponse(
        filename=file.filename,
        rows=len(df),
        columns=list(df.columns),
        file_size=file_size,
        preview=preview
    )

@app.post("/build", response_model=BuildResponse)
async def build_warehouse():
    """Build warehouse from uploaded files"""
    
    # Get all CSV files
    files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.csv')]
    
    if not files:
        raise HTTPException(400, "No files uploaded. Upload files first.")
    
    project_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_dir = os.path.join(OUTPUT_DIR, f"project_{project_id}")
    os.makedirs(project_dir, exist_ok=True)
    
    fact_tables = []
    dim_tables = []
    output_files = []
    
    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file)
        df = pd.read_csv(file_path)
        table_name = file.replace('.csv', '').lower()
        
        # Simple detection: if has numeric columns and many rows -> fact
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if len(numeric_cols) > len(df.columns) / 2 and len(df) > 10:
            # This is a fact table
            fact_name = f"fact_{table_name}"
            fact_tables.append(fact_name)
            
            # Save as CSV
            output_path = os.path.join(project_dir, f"{fact_name}.csv")
            df.to_csv(output_path, index=False)
            output_files.append(f"{fact_name}.csv")
        else:
            # This is a dimension table
            dim_name = f"dim_{table_name}"
            dim_tables.append(dim_name)
            
            # Save as CSV
            output_path = os.path.join(project_dir, f"{dim_name}.csv")
            df.to_csv(output_path, index=False)
            output_files.append(f"{dim_name}.csv")
    
    # Create metadata
    metadata = f"""Project: {project_id}
Date: {datetime.now()}
Files: {len(files)}
Fact Tables: {', '.join(fact_tables)}
Dimension Tables: {', '.join(dim_tables)}
Relationships: {len(fact_tables)}
"""
    
    with open(os.path.join(project_dir, "README.txt"), "w") as f:
        f.write(metadata)
    
    output_files.append("README.txt")
    
    return BuildResponse(
        project_id=project_id,
        status="success",
        fact_tables=fact_tables,
        dimension_tables=dim_tables,
        relationships=len(fact_tables),
        message=f"Warehouse built with {len(fact_tables)} fact tables and {len(dim_tables)} dimensions",
        output_files=output_files
    )

@app.get("/files")
async def list_files():
    """List uploaded files"""
    files = []
    if os.path.exists(UPLOAD_DIR):
        for f in os.listdir(UPLOAD_DIR):
            if f.endswith('.csv'):
                file_path = os.path.join(UPLOAD_DIR, f)
                try:
                    df = pd.read_csv(file_path)
                    files.append({
                        "name": f,
                        "size": os.path.getsize(file_path),
                        "rows": len(df),
                        "columns": len(df.columns),
                        "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })
                except:
                    continue
    return {"uploaded_files": files}

@app.get("/projects")
async def list_projects():
    """List all built projects"""
    projects = []
    if os.path.exists(OUTPUT_DIR):
        for item in os.listdir(OUTPUT_DIR):
            if item.startswith("project_"):
                project_path = os.path.join(OUTPUT_DIR, item)
                project_id = item.replace("project_", "")
                projects.append({
                    "project_id": project_id,
                    "path": item,
                    "created": datetime.fromtimestamp(os.path.getctime(project_path)).isoformat()
                })
    return {"projects": sorted(projects, key=lambda x: x['created'], reverse=True)}

@app.get("/download/{project_id}", response_class=HTMLResponse)
async def download_project(project_id: str):
    """Get project details as HTML page"""
    project_path = os.path.join(OUTPUT_DIR, f"project_{project_id}")
    
    if not os.path.exists(project_path):
        raise HTTPException(404, "Project not found")
    
    files = os.listdir(project_path)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AutoDW - Project {project_id}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.2);
            }}
            h1 {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 20px;
            }}
            .file-list {{
                margin-top: 20px;
            }}
            .file-item {{
                display: flex;
                align-items: center;
                padding: 15px;
                background: #f8f9ff;
                border-radius: 10px;
                margin-bottom: 10px;
                transition: transform 0.2s;
            }}
            .file-item:hover {{
                transform: translateX(5px);
            }}
            .file-icon {{
                font-size: 24px;
                margin-right: 15px;
            }}
            .file-name {{
                flex-grow: 1;
                font-weight: 500;
            }}
            .btn {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                text-decoration: none;
                cursor: pointer;
            }}
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }}
            .location {{
                background: #f0f0f0;
                padding: 15px;
                border-radius: 10px;
                font-family: monospace;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Project: {project_id}</h1>
            <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            
            <div class="location">
                📁 Files saved at:<br>
                <strong>{os.path.abspath(project_path)}</strong>
            </div>
            
            <h2>📄 Files Generated:</h2>
            <div class="file-list">
                {''.join([f'''
                <div class="file-item">
                    <span class="file-icon">{"📊" if "fact" in f else "📁" if "dim" in f else "📝"}</span>
                    <span class="file-name">{f}</span>
                    <span class="file-size">{os.path.getsize(os.path.join(project_path, f)) / 1024:.1f} KB</span>
                </div>
                ''' for f in files])}
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <button class="btn" onclick="window.location.href='/'">🏠 Back to Dashboard</button>
                <button class="btn" onclick="window.location.href='file:///{os.path.abspath(project_path).replace(chr(92), '/')}'" style="margin-left: 10px;">
                    📂 Open Folder
                </button>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# ============================================================================
# Auto-open browser
# ============================================================================

def open_browser():
    """Open browser when server starts"""
    import time
    time.sleep(2)  # Wait for server to start
    webbrowser.open("http://localhost:8001")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Start browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8001)