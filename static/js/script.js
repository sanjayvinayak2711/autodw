async function uploadFiles(files) {
    showToast('Uploading files...', 'loading');
    
    for (let file of files) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                showToast(`✅ ${file.name} uploaded successfully`);
            } else {
                showToast(`❌ Failed to upload ${file.name}`);
            }
        } catch (error) {
            showToast(`❌ Error uploading ${file.name}`);
        }
    }
    
    refreshData();
}

async function buildWarehouse() {
    showToast('🏗️ Building warehouse...', 'loading');
    
    try {
        const response = await fetch('/build', {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast(`✅ ${data.message}`);
            
            // Open the project in new tab
            window.open(`/download/${data.project_id}`, '_blank');
        } else {
            showToast('❌ Build failed');
        }
    } catch (error) {
        showToast('❌ Build error');
    }
    
    refreshData();
}

async function refreshData() {
    // Get files
    const filesResponse = await fetch('/files');
    const filesData = await filesResponse.json();
    
    // Get projects
    const projectsResponse = await fetch('/projects');
    const projectsData = await projectsResponse.json();
    
    updateUI(filesData, projectsData);
}

function updateUI(filesData, projectsData) {
    // Update counts
    document.getElementById('file-count').textContent = filesData.uploaded_files?.length || 0;
    document.getElementById('project-count').textContent = projectsData.projects?.length || 0;
    
    // Calculate total rows
    let totalRows = 0;
    if (filesData.uploaded_files) {
        filesData.uploaded_files.forEach(f => totalRows += f.rows || 0);
    }
    document.getElementById('total-rows').textContent = totalRows.toLocaleString();
    
    // Update files grid
    const filesGrid = document.getElementById('files-grid');
    if (filesData.uploaded_files?.length) {
        filesGrid.innerHTML = filesData.uploaded_files.map(file => `
            <div class="file-card">
                <div class="file-icon">📄</div>
                <div class="file-name">${file.name}</div>
                <div class="file-meta">
                    📊 ${file.rows.toLocaleString()} rows<br>
                    📋 ${file.columns} columns<br>
                    📦 ${(file.size / 1024).toFixed(2)} KB
                </div>
            </div>
        `).join('');
    } else {
        filesGrid.innerHTML = '<div style="text-align: center; padding: 40px; color: #999;">No files uploaded yet</div>';
    }
    
    // Update projects list
    const projectsList = document.getElementById('projects-list');
    if (projectsData.projects?.length) {
        projectsList.innerHTML = projectsData.projects.map(project => `
            <div class="project-item">
                <div>
                    <strong>🆔 ${project.project_id}</strong><br>
                    <small>${new Date(project.created).toLocaleString()}</small>
                </div>
                <a href="/download/${project.project_id}" target="_blank" class="btn btn-secondary" style="padding: 8px 15px;">View</a>
            </div>
        `).join('');
    } else {
        projectsList.innerHTML = '<div style="text-align: center; padding: 20px; color: #999;">No projects built yet</div>';
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.innerHTML = message;
    toast.style.display = 'block';
    
    if (type !== 'loading') {
        setTimeout(() => {
            toast.style.display = 'none';
        }, 3000);
    }
}

// Initial load
refreshData();

// Auto refresh every 10 seconds
setInterval(refreshData, 10000);
