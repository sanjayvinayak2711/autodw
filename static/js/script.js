// AutoDW - Automated Data Warehouse - Working Version
class AutoDWApp {
    constructor() {
        this.apiBase = '';
        this.uploadedFiles = [];
        this.projects = [];
        this.init();
    }

    init() {
        console.log('Initializing AutoDW App...');
        this.bindEvents();
        // Load data with a small delay to allow page to render first
        setTimeout(() => {
            this.loadInitialData();
        }, 100);
        console.log('AutoDW App initialized');
    }

    bindEvents() {
        // File upload drag and drop
        const uploadArea = document.querySelector('.upload-area');
        if (uploadArea) {
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.style.borderColor = '#0066ff';
                uploadArea.style.background = 'var(--bg-card-hover)';
            });

            uploadArea.addEventListener('dragleave', (e) => {
                e.preventDefault();
                uploadArea.style.borderColor = '';
                uploadArea.style.background = '';
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.style.borderColor = '';
                uploadArea.style.background = '';
                const files = Array.from(e.dataTransfer.files).filter(f => 
                    f.name.endsWith('.csv') || f.name.endsWith('.pdf')
                );
                if (files.length > 0) {
                    this.uploadFiles(files);
                } else {
                    this.showToast('Please drop CSV or PDF files only', 'error');
                }
            });
        }
    }

    async loadInitialData() {
        // Show loading indicators
        this.showLoadingIndicators();
        
        try {
            // Load data in parallel for better performance
            const [filesData, projectsData] = await Promise.allSettled([
                this.loadFiles(),
                this.loadProjects()
            ]);
            
            // Update stats only after both are loaded
            this.updateStats();
            
            // Hide loading indicators
            this.hideLoadingIndicators();
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.hideLoadingIndicators();
            this.showToast('Error loading data', 'error');
        }
    }

    showLoadingIndicators() {
        // Show loading state for files and projects
        const filesGrid = document.getElementById('files-grid');
        const projectsList = document.getElementById('projects-list');
        
        if (filesGrid) {
            filesGrid.innerHTML = '<div class="loading-spinner"></div><p style="text-align: center; color: var(--text-tertiary);">Loading files...</p>';
        }
        
        if (projectsList) {
            projectsList.innerHTML = '<div class="loading-spinner"></div><p style="text-align: center; color: var(--text-tertiary);">Loading projects...</p>';
        }
    }

    hideLoadingIndicators() {
        // Loading indicators will be replaced by actual content when renderFiles/renderProjects is called
    }

    async loadFiles() {
        try {
            const response = await fetch(`${this.apiBase}/files`);
            const data = await response.json();
            this.uploadedFiles = data.uploaded_files || [];
            console.log('Loaded files:', this.uploadedFiles);
            this.renderFiles();
        } catch (error) {
            console.error('Error loading files:', error);
        }
    }

    async loadProjects() {
        try {
            const response = await fetch(`${this.apiBase}/api/projects`);
            const data = await response.json();
            // Handle both direct array and wrapped responses
            this.projects = data.value || data || [];
            console.log('Loaded projects:', this.projects);
            this.renderProjects();
        } catch (error) {
            console.error('Error loading projects:', error);
        }
    }

    updateStats() {
        const fileCount = document.getElementById('file-count');
        const projectCount = document.getElementById('project-count');
        const totalRows = document.getElementById('total-rows');
        
        if (fileCount) fileCount.textContent = this.uploadedFiles.length;
        if (projectCount) projectCount.textContent = this.projects.length;
        
        const totalRowsCount = this.uploadedFiles.reduce((sum, file) => sum + (file.rows || 0), 0);
        if (totalRows) totalRows.textContent = this.formatNumber(totalRowsCount);
    }

    formatNumber(num) {
        return num.toLocaleString();
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    renderFiles() {
        const filesGrid = document.getElementById('files-grid');
        if (!filesGrid) return;

        if (this.uploadedFiles.length === 0) {
            filesGrid.innerHTML = '<p style="text-align: center; color: var(--text-tertiary); grid-column: 1 / -1;">No files uploaded yet</p>';
            return;
        }

        filesGrid.innerHTML = this.uploadedFiles.map((file, index) => `
            <div class="file-card">
                <div class="file-icon">
                    <i class="fas fa-file-${file.name.endsWith('.pdf') ? 'pdf' : 'csv'}"></i>
                </div>
                <div class="file-details">
                    <div class="file-name">${file.name}</div>
                    <div class="file-meta">
                        <span>${this.formatNumber(file.rows || 0)} rows</span>
                        <span>•</span>
                        <span>${file.columns || 12} columns</span>
                        <span>•</span>
                        <span>${this.formatFileSize(file.size || 0)}</span>
                    </div>
                </div>
                <button class="btn btn-danger" onclick="app.deleteFile('${file.name}', ${index})" title="Delete file">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `).join('');
    }

    renderProjects() {
        const projectsList = document.getElementById('projects-list');
        if (!projectsList) return;

        if (this.projects.length === 0) {
            projectsList.innerHTML = '<p style="text-align: center; color: var(--text-tertiary);">No projects built yet</p>';
            return;
        }

        projectsList.innerHTML = this.projects.map(project => `
            <div class="project-item">
                <div class="project-info">
                    <h4>${project.project_name || `Project ${project.project_id}`}</h4>
                    <div class="project-meta">
                        <span><i class="fas fa-calendar"></i> ${new Date(project.created).toLocaleDateString()}</span>
                        <span><i class="fas fa-cubes"></i> ${(project.fact_tables || []).length} fact, ${(project.dimension_tables || []).length} dim</span>
                    </div>
                </div>
                <div class="project-actions">
                    <button class="btn btn-primary" onclick="app.viewProject('${project.project_id}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                </div>
            </div>
        `).join('');
    }

    async uploadFiles(files) {
        console.log('Starting upload of', files.length, 'files');
        
        if (!files || files.length === 0) {
            this.showToast('Please select files to upload', 'error');
            return;
        }

        try {
            for (let file of files) {
                console.log('Processing file:', file.name);
                
                const formData = new FormData();
                formData.append('file', file);

                this.showToast(`Uploading ${file.name}...`, 'info');

                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `Upload failed: ${response.status}`);
                }

                const result = await response.json();
                console.log('Upload successful:', result);
                
                this.showToast(`${file.name} uploaded successfully!`, 'success');
            }
            
            // Reload files list
            await this.loadFiles();
            this.updateStats();
            
        } catch (error) {
            console.error('Upload error:', error);
            this.showToast(`Upload failed: ${error.message}`, 'error');
        }
    }

    async buildWarehouse() {
        if (this.uploadedFiles.length === 0) {
            this.showToast('Please upload files first', 'error');
            return;
        }

        const buildBtn = document.querySelector('.btn-primary');
        if (buildBtn) {
            const originalText = buildBtn.innerHTML;
            buildBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Building...';
            buildBtn.disabled = true;

            try {
                this.showToast('Starting warehouse build process...', 'info');

                const response = await fetch(`${this.apiBase}/build`, {
                    method: 'POST'
                });

                if (!response.ok) {
                    throw new Error('Build failed');
                }

                const result = await response.json();
                console.log('Build result:', result);
                
                this.showToast(`✨ Warehouse built successfully!`, 'success');
                this.showToast(`📁 Created ${result.message}`, 'success');
                this.showToast(`🗄️ Access your projects in the Warehouse button!`, 'info');
                
                // Add blinking effect to Warehouse button
                this.addWarehouseBlinking();
                
                // Clear uploaded files after successful build
                this.uploadedFiles = [];
                this.renderFiles();
                this.updateStats();
                
                // Suggest going to warehouse
                setTimeout(() => {
                    this.showToast('👉 Click the "Warehouse" button to see your projects!', 'info');
                }, 2000);
                
            } catch (error) {
                console.error('Build error:', error);
                this.showToast('Build failed: ' + error.message, 'error');
            } finally {
                buildBtn.innerHTML = originalText;
                buildBtn.disabled = false;
            }
        }
    }

    // Add blinking effect to Warehouse button when new files are processed
    addWarehouseBlinking() {
        console.log('🔔 Attempting to add warehouse blinking effect...');
        const warehouseNav = document.querySelector('a[href="/projects"]');
        console.log('🔍 Warehouse nav element found:', warehouseNav);
        
        if (warehouseNav) {
            // Remove existing blinking class if any
            warehouseNav.classList.remove('blinking');
            
            // Force reflow to restart animation
            void warehouseNav.offsetWidth;
            
            // Add blinking class
            warehouseNav.classList.add('blinking');
            
            // Store the blinking state
            this.isWarehouseBlinking = true;
            
            console.log('✨ Warehouse button is now blinking to indicate new files!');
            console.log('🔔 Classes on warehouse button:', warehouseNav.className);
            
            // Add a test message
            this.showToast('🔔 Warehouse button is blinking! Check the navigation!', 'success');
        } else {
            console.error('❌ Warehouse navigation element not found!');
            this.showToast('❌ Warehouse button not found!', 'error');
        }
    }

    // Remove blinking effect when user clicks on Warehouse
    removeWarehouseBlinking() {
        const warehouseNav = document.querySelector('a[href="/projects"]');
        if (warehouseNav) {
            warehouseNav.classList.remove('blinking');
            this.isWarehouseBlinking = false;
            console.log('👁️ Warehouse button blinking stopped - user viewed the files');
        }
    }

    // Load initial data
    loadInitialData() {
        this.loadFiles();
        this.updateStats();
    }

    viewProject(projectId) {
        window.open(`/download/${projectId}`, '_blank');
    }

    deleteFile(filename, index) {
        this.showDeleteConfirmModal(filename, index);
    }

    showDeleteConfirmModal(filename, index) {
        // Create modal if it doesn't exist
        let modal = document.getElementById('delete-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'delete-modal';
            modal.className = 'delete-modal';
            document.body.appendChild(modal);
        }

        modal.innerHTML = `
            <div class="modal-overlay" onclick="app.closeDeleteModal()">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <div class="modal-header">
                        <div class="modal-icon">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                        <h3>Delete File</h3>
                        <button class="modal-close" onclick="app.closeDeleteModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <p>Are you sure you want to delete <strong>${filename}</strong>?</p>
                        <p class="warning-text">This action cannot be undone.</p>
                    </div>
                    <div class="modal-actions">
                        <button class="btn btn-secondary" onclick="app.closeDeleteModal()">
                            <i class="fas fa-times"></i>
                            Cancel
                        </button>
                        <button class="btn btn-danger" onclick="app.confirmDelete('${filename}', ${index})">
                            <i class="fas fa-trash"></i>
                            Delete
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Add modal styles if not exists
        if (!document.querySelector('#delete-modal-styles')) {
            const style = document.createElement('style');
            style.id = 'delete-modal-styles';
            style.textContent = `
                .delete-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    z-index: 10000;
                    display: flex !important;
                    justify-content: center !important;
                    align-items: center !important;
                    animation: fadeIn 0.3s ease-out;
                }
                
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                
                @keyframes slideUp {
                    from { 
                        opacity: 0;
                        transform: translateY(30px) scale(0.9);
                    }
                    to { 
                        opacity: 1;
                        transform: translateY(0) scale(1);
                    }
                }
                
                .modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100vw;
                    height: 100vh;
                    background: rgba(0, 0, 0, 0.8);
                    backdrop-filter: blur(5px);
                    animation: fadeIn 0.3s ease-out;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }
                
                .modal-content {
                    position: relative;
                    background: var(--bg-card);
                    border: 1px solid var(--border-color);
                    border-radius: 20px;
                    max-width: 450px;
                    width: 90%;
                    overflow: hidden;
                    animation: slideUp 0.3s ease-out;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8);
                }
                
                .modal-header {
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    padding: 25px 30px 20px;
                    border-bottom: 1px solid var(--border-color);
                }
                
                .modal-icon {
                    width: 50px;
                    height: 50px;
                    background: linear-gradient(135deg, #ff3d00, #ff6b35);
                    border-radius: 15px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                    color: white;
                    animation: pulse 2s infinite;
                }
                
                @keyframes pulse {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.05); }
                }
                
                .modal-header h3 {
                    margin: 0;
                    font-size: 24px;
                    color: var(--text-primary);
                    flex: 1;
                }
                
                .modal-close {
                    background: none;
                    border: none;
                    color: var(--text-tertiary);
                    font-size: 20px;
                    cursor: pointer;
                    padding: 8px;
                    border-radius: 8px;
                    transition: all 0.3s;
                }
                
                .modal-close:hover {
                    color: var(--text-primary);
                    background: var(--bg-card-hover);
                }
                
                .modal-body {
                    padding: 20px 30px 25px;
                }
                
                .modal-body p {
                    margin: 0 0 15px;
                    color: var(--text-secondary);
                    font-size: 16px;
                    line-height: 1.5;
                }
                
                .modal-body strong {
                    color: var(--text-primary);
                    font-weight: 600;
                }
                
                .warning-text {
                    color: var(--warning) !important;
                    font-size: 14px !important;
                    font-style: italic;
                }
                
                .modal-actions {
                    display: flex;
                    gap: 15px;
                    padding: 20px 30px 25px;
                    border-top: 1px solid var(--border-color);
                }
                
                .modal-actions .btn {
                    flex: 1;
                    padding: 12px 20px;
                    border-radius: 12px;
                    font-size: 15px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s;
                    border: none;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                }
                
                .modal-actions .btn-secondary {
                    background: var(--bg-primary);
                    color: var(--text-primary);
                    border: 1px solid var(--border-color);
                }
                
                .modal-actions .btn-secondary:hover {
                    background: var(--bg-card-hover);
                    border-color: var(--accent-primary);
                    transform: translateY(-2px);
                }
                
                .modal-actions .btn-danger {
                    background: linear-gradient(135deg, #ff3d00, #ff6b35);
                    color: white;
                    box-shadow: 0 4px 15px rgba(255, 61, 0, 0.3);
                }
                
                .modal-actions .btn-danger:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(255, 61, 0, 0.4);
                }
            `;
            document.head.appendChild(style);
        }
    }

    closeDeleteModal() {
        const modal = document.getElementById('delete-modal');
        if (modal) {
            modal.remove();
        }
    }

    confirmDelete(filename, index) {
        // Remove file from array
        this.uploadedFiles.splice(index, 1);
        this.renderFiles();
        this.updateStats();
        
        // Close modal
        this.closeDeleteModal();
        
        // Show success message
        this.showToast(`${filename} deleted successfully`, 'success');
    }

    refreshData() {
        this.loadInitialData();
        this.showToast('Data refreshed', 'success');
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        if (!toast) return;
        
        toast.textContent = message;
        toast.className = `toast ${type}`;
        toast.style.display = 'block';
        
        setTimeout(() => {
            toast.style.display = 'none';
        }, 3000);
    }
}

// Global functions
window.uploadFiles = function(files) {
    if (window.app) {
        window.app.uploadFiles(files);
    }
};

window.buildWarehouse = function() {
    if (window.app) {
        window.app.buildWarehouse();
    }
};

window.refreshData = function() {
    if (window.app) {
        window.app.refreshData();
    }
};

// Test function for blinking effect
window.testBlinking = function() {
    if (window.app) {
        window.app.addWarehouseBlinking();
    }
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing AutoDW...');
    window.app = new AutoDWApp();
    
    // Add event listener to Warehouse button to stop blinking when clicked
    const warehouseNav = document.querySelector('a[href="/projects"]');
    if (warehouseNav) {
        warehouseNav.addEventListener('click', () => {
            if (window.app.isWarehouseBlinking) {
                window.app.removeWarehouseBlinking();
            }
        });
    }
    
    console.log('AutoDW ready!');
});
