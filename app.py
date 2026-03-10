"""
AutoDW - Automated Data Warehouse with Browser Dashboard
Run: python app.py or start.bat
Click: http://localhost:8001
"""

import os
import pandas as pd
import webbrowser
import threading
import shutil
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import pdfplumber
import io

# Global cache for performance
_files_cache = None
_cache_timestamp = None
CACHE_DURATION = 30  # Cache for 30 seconds

app = FastAPI(title="AutoDW", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "data/uploads"
OUTPUT_DIR = "data/output"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mount static files
app.mount("/css", StaticFiles(directory="static/css"), name="css")
app.mount("/js", StaticFiles(directory="static/js"), name="js")

# Setup templates
templates = Jinja2Templates(directory="templates")

# MODELS

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

# API ENDPOINTS

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main dashboard - opens in browser"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    return {"status": "healthy", "time": datetime.now().isoformat()}

@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV or PDF file"""
    
    if not file.filename.endswith(('.csv', '.pdf')):
        raise HTTPException(400, "Only CSV and PDF files allowed")
    
    # Save file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    content = await file.read()
    file_size = len(content)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Clear cache when new file is uploaded
    global _files_cache, _cache_timestamp
    _files_cache = None
    _cache_timestamp = None
    
    # Process based on file type
    if file.filename.endswith('.csv'):
        # Read CSV
        df = pd.read_csv(file_path)
        preview = df.head(5).to_dict(orient='records')
    elif file.filename.endswith('.pdf'):
        # Extract text from PDF
        text_content = []
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
        except Exception as e:
            raise HTTPException(400, f"Error processing PDF: {str(e)}")
        
        # Convert extracted text to a structured format
        full_text = "\n".join(text_content)
        lines = [line.strip() for line in full_text.split("\n") if line.strip()]
        
        # Create a DataFrame with page and line information
        data = []
        for i, line in enumerate(lines[:20]):  # Limit to first 20 lines for preview
            data.append({
                "line_number": i + 1,
                "content": line,
                "word_count": len(line.split())
            })
        
        df = pd.DataFrame(data)
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
    """Build warehouse from uploaded files - creates one project per uploaded file"""
    
    # Get all CSV and PDF files
    files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(('.csv', '.pdf'))]
    
    print(f"DEBUG: Found {len(files)} files in uploads: {files}")
    
    if not files:
        raise HTTPException(400, "No files uploaded. Upload files first.")
    
    # Clear any existing projects to prevent duplicates
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR)
    
    all_fact_tables = []
    all_dim_tables = []
    all_output_files = []
    project_ids = []
    
    # Process each file separately to create individual projects
    for file in files:
        print(f"DEBUG: Processing file: {file}")
        # Generate unique project ID with timestamp and file name
        file_base = file.replace('.csv', '').replace('.pdf', '')
        project_id = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{file_base[:10]}"
        project_dir = os.path.join(OUTPUT_DIR, f"project_{project_id}")
        os.makedirs(project_dir, exist_ok=True)
        
        file_path = os.path.join(UPLOAD_DIR, file)
        
        # Process the file
        if file.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file.endswith('.pdf'):
            # Process PDF and convert to CSV format
            with open(file_path, 'rb') as f:
                pdf_content = f.read()
            
            text_content = []
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
            
            full_text = "\n".join(text_content)
            lines = [line.strip() for line in full_text.split("\n") if line.strip()]
            
            data = []
            for i, line in enumerate(lines):
                data.append({
                    "line_number": i + 1,
                    "content": line,
                    "word_count": len(line.split())
                })
            
            df = pd.DataFrame(data)
        
        table_name = file_base.lower()
        
        # Simple detection: if has numeric columns and many rows -> fact
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        fact_tables = []
        dim_tables = []
        output_files = []
        
        if len(numeric_cols) > len(df.columns) / 2 and len(df) > 10:
            # This is a fact table
            fact_name = f"fact_{table_name}"
            fact_tables.append(fact_name)
            all_fact_tables.append(fact_name)
            
            # Save as CSV
            output_path = os.path.join(project_dir, f"{fact_name}.csv")
            df.to_csv(output_path, index=False)
            output_files.append(f"{fact_name}.csv")
        else:
            # This is a dimension table
            dim_name = f"dim_{table_name}"
            dim_tables.append(dim_name)
            all_dim_tables.append(dim_name)
            
            # Save as CSV
            output_path = os.path.join(project_dir, f"{dim_name}.csv")
            df.to_csv(output_path, index=False)
            output_files.append(f"{dim_name}.csv")
        
        # Create project name based on file
        clean_name = file_base.replace('_', ' ').replace('-', ' ')
        clean_name = ' '.join(word.capitalize() for word in clean_name.split())
        
        # Create metadata for this individual file project
        metadata = f"""Project Name: {clean_name}
Project ID: {project_id}
Date: {datetime.now()}
Files: 1
Source File: {file}
Fact Tables: {', '.join(fact_tables)}
Dimension Tables: {', '.join(dim_tables)}
Relationships: {len(fact_tables)}
"""
        
        with open(os.path.join(project_dir, "README.txt"), "w") as f:
            f.write(metadata)
        
        output_files.append("README.txt")
        all_output_files.extend(output_files)
        project_ids.append(project_id)
    
    return BuildResponse(
        project_id=project_ids[0] if project_ids else datetime.now().strftime("%Y%m%d_%H%M%S"),
        status="success",
        fact_tables=all_fact_tables,
        dimension_tables=all_dim_tables,
        relationships=len(all_fact_tables),
        message=f"Created {len(project_ids)} separate projects from {len(files)} files",
        output_files=all_output_files
    )

@app.get("/files")
async def list_files():
    """List uploaded files - optimized with caching"""
    global _files_cache, _cache_timestamp
    
    current_time = datetime.now()
    
    # Check if cache is valid
    if (_files_cache is not None and 
        _cache_timestamp is not None and 
        (current_time - _cache_timestamp).seconds < CACHE_DURATION):
        return {"uploaded_files": _files_cache}
    
    # Cache expired or not set, rebuild it
    files = []
    if os.path.exists(UPLOAD_DIR):
        for f in os.listdir(UPLOAD_DIR):
            if f.endswith(('.csv', '.pdf')):
                file_path = os.path.join(UPLOAD_DIR, f)
                try:
                    # Quick file info without full processing for list view
                    file_size = os.path.getsize(file_path)
                    file_mtime = os.path.getmtime(file_path)
                    
                    # Simplified row count calculation
                    if f.endswith('.csv'):
                        try:
                            # Quick CSV row count without loading full data
                            with open(file_path, 'r') as file:
                                row_count = sum(1 for _ in file) - 1  # Subtract header
                            col_count = len(pd.read_csv(file_path, nrows=1).columns.tolist())
                        except:
                            row_count, col_count = 0, 0
                    else:
                        # For PDFs, estimate based on file size
                        row_count = min(file_size // 1000, 1000)  # Rough estimate
                        col_count = 3  # Standard PDF processing columns
                    
                    files.append({
                        "name": f,
                        "size": file_size,
                        "rows": row_count,
                        "columns": col_count,
                        "modified": datetime.fromtimestamp(file_mtime).isoformat()
                    })
                except:
                    continue
    
    # Update cache
    _files_cache = files
    _cache_timestamp = current_time
    
    return {"uploaded_files": files}

@app.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request):
    """Projects page - list all built projects"""
    return templates.TemplateResponse("projects.html", {"request": request})

@app.get("/api/projects")
async def list_projects():
    """API endpoint to list all built projects with real data"""
    projects = []
    seen_projects = set()  # Track unique project names
    
    try:
        if os.path.exists(OUTPUT_DIR):
            items = os.listdir(OUTPUT_DIR)
            
            for item in items:
                if item.startswith("project_") and len(item) > 8:
                    project_id = item[8:]  # Remove prefix
                    project_path = os.path.join(OUTPUT_DIR, item)
                    
                    # Skip duplicates by checking project_id
                    if project_id in seen_projects:
                        continue
                    seen_projects.add(project_id)
                    
                    # Get real project data
                    try:
                        files = os.listdir(project_path)
                        
                        # Count fact and dimension tables
                        fact_tables = []
                        dim_tables = []
                        total_size = 0
                        
                        for file in files:
                            file_path = os.path.join(project_path, file)
                            if os.path.isfile(file_path):
                                total_size += os.path.getsize(file_path) / (1024 * 1024)  # MB
                                
                                if file.startswith("fact_"):
                                    fact_tables.append(file)
                                elif file.startswith("dim_"):
                                    dim_tables.append(file)
                        
                        # Extract project name from README if available, with deduplication handling
                        base_name = project_id[:15]  # Use first part of ID
                        project_name = base_name.replace('_', ' ').title()
                        
                        # Add timestamp to make names unique
                        if '_' in project_id:
                            timestamp_part = project_id.split('_')[0] if len(project_id.split('_')) > 1 else ''
                            if timestamp_part and len(timestamp_part) >= 12:  # YYYYMMDDHHMMSS format
                                try:
                                    date_obj = datetime.strptime(timestamp_part, "%Y%m%d%H%M%S")
                                    formatted_date = date_obj.strftime("%m/%d %H:%M")
                                    project_name = f"{base_name} ({formatted_date})"
                                except:
                                    pass
                        
                        created_at = "2024-01-01"  # Default
                        
                        readme_path = os.path.join(project_path, "README.txt")
                        if os.path.exists(readme_path):
                            try:
                                with open(readme_path, 'r') as f:
                                    content = f.read()
                                    for line in content.split('\n'):
                                        if line.startswith('Project Name:'):
                                            project_name = line.replace('Project Name:', '').strip()
                                        elif line.startswith('Date:'):
                                            created_at = line.replace('Date:', '').strip()
                                            # Extract just the date part
                                            if ' ' in created_at:
                                                created_at = created_at.split(' ')[0]
                            except:
                                pass
                        
                        projects.append({
                            "project_id": project_id,
                            "project_name": project_name,
                            "created_at": created_at,
                            "fact_tables": fact_tables,
                            "dimension_tables": dim_tables,
                            "fact_tables_count": len(fact_tables),
                            "dim_tables_count": len(dim_tables),
                            "total_size_mb": round(total_size, 2),
                            "file_count": len(files)
                        })
                        
                    except Exception as e:
                        print(f"Error processing project {project_id}: {e}")
                        # Skip this project and continue
                        continue
        
        # Only add sample data if absolutely no projects exist
        if len(projects) == 0:
            projects = [
                {
                    "project_id": "sample_20240101_120000",
                    "project_name": "Sample Sales Data",
                    "created_at": "2024-01-01",
                    "fact_tables": ["fact_sales"],
                    "dimension_tables": ["dim_customer", "dim_product", "dim_time"],
                    "fact_tables_count": 1,
                    "dim_tables_count": 3,
                    "total_size_mb": 1.5,
                    "file_count": 5
                }
            ]
    
    except Exception as e:
        print(f"API error: {e}")
        projects = []
    
    return JSONResponse(content=projects)

@app.get("/preview/{project_id}/{file_name}")
async def preview_file(project_id: str, file_name: str):
    """Preview a file's content"""
    project_path = os.path.join(OUTPUT_DIR, f"project_{project_id}")
    file_path = os.path.join(project_path, file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found")
    
    try:
        if file_name.endswith('.csv'):
            df = pd.read_csv(file_path)
            preview_data = df.head(10).to_dict(orient='records')
            columns = list(df.columns)
            total_rows = len(df)
            
            return JSONResponse({
                "file_name": file_name,
                "file_type": "csv",
                "columns": columns,
                "total_rows": total_rows,
                "preview_data": preview_data
            })
        else:
            # For text files
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return JSONResponse({
                "file_name": file_name,
                "file_type": "text",
                "content": content[:2000]  # First 2000 characters
            })
    except Exception as e:
        raise HTTPException(500, f"Error reading file: {str(e)}")

@app.get("/download/{project_id}/{file_name}")
async def download_file(project_id: str, file_name: str):
    """Download a specific file from a project"""
    project_path = os.path.join(OUTPUT_DIR, f"project_{project_id}")
    file_path = os.path.join(project_path, file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(file_path, media_type='application/octet-stream', filename=file_name)

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project and all its files - PERMANENT DELETION"""
    project_path = os.path.join(OUTPUT_DIR, f"project_{project_id}")
    
    if not os.path.exists(project_path):
        raise HTTPException(404, f"Project not found: {project_path}")
    
    try:
        import shutil
        
        print(f"Deleting project: {project_path}")
        
        # Check if it's a directory or file
        if os.path.isdir(project_path):
            # Remove the entire project directory permanently
            shutil.rmtree(project_path)
            print(f"Directory deleted: {project_path}")
        else:
            # Remove the file (e.g., zip file) permanently
            os.remove(project_path)
            print(f"File deleted: {project_path}")
        
        # Verify deletion
        if os.path.exists(project_path):
            raise Exception(f"Failed to delete: {project_path} still exists")
        
        # Clear ALL caches to prevent reappearing
        global _files_cache, _cache_timestamp
        _files_cache = None
        _cache_timestamp = None
        
        print(f"Project {project_id} permanently deleted")
        
        return {"message": "Project permanently deleted", "project_id": project_id}
    except PermissionError as e:
        raise HTTPException(403, f"Permission denied: {str(e)}")
    except Exception as e:
        print(f"Delete error: {str(e)}")
        raise HTTPException(500, f"Error deleting project: {str(e)}")

@app.get("/download/{project_id}", response_class=HTMLResponse)
async def download_project(project_id: str, request: Request):
    """Get project details as HTML page"""
    project_path = os.path.join(OUTPUT_DIR, f"project_{project_id}")
    
    if not os.path.exists(project_path):
        raise HTTPException(404, "Project not found")
    
    files = os.listdir(project_path)
    file_sizes = {f: os.path.getsize(os.path.join(project_path, f)) / 1024 for f in files}
    
    return templates.TemplateResponse("project.html", {
        "request": request,
        "project_id": project_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project_path": os.path.abspath(project_path),
        "files": files,
        "file_sizes": file_sizes
    })

# Auto-open browser

def open_browser():
    """Open browser when server starts"""
    import time
    time.sleep(2)  # Wait for server to start
    webbrowser.open("http://localhost:8001")

# MAIN

if __name__ == "__main__":
    # Start browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8001)