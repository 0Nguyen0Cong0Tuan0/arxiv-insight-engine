const Upload = {
    init() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const uploadBtn = document.getElementById('uploadBtn');
        
        // Click to upload
        uploadArea.addEventListener('click', () => fileInput.click());
        
        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            this.handleFiles(e.dataTransfer.files);
        });
        
        // File input change
        fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
        });
        
        // Upload button click
        uploadBtn.addEventListener('click', () => this.uploadFiles());
    },
    
    handleFiles(files) {
        const uploadArea = document.getElementById('uploadArea');
        const uploadBtn = document.getElementById('uploadBtn');
        
        const pdfFiles = Array.from(files).filter(f => f.type === 'application/pdf');
        AppState.setSelectedFiles(pdfFiles);
        
        if (pdfFiles.length > 0) {
            uploadArea.innerHTML = `
                <div class="upload-icon">
                    <i data-lucide="check-circle" size="32" color="white"></i>
                </div>
                <h3>${pdfFiles.length} PDF${pdfFiles.length > 1 ? 's' : ''} selected</h3>
                <p style="color: var(--text-secondary); font-size: 14px;">
                    ${pdfFiles.map(f => f.name).slice(0, 3).join(', ')}${pdfFiles.length > 3 ? '...' : ''}
                </p>
            `;
            uploadBtn.disabled = false;
            lucide.createIcons();
        }
    },
    
    async uploadFiles() {
        if (AppState.selectedFiles.length === 0) return;
        
        const uploadBtn = document.getElementById('uploadBtn');
        uploadBtn.innerHTML = '<div class="loading"></div> Processing...';
        uploadBtn.disabled = true;
        
        try {
            const result = await API.uploadPDFs(AppState.selectedFiles);
            
            if (result.success) {
                UI.showToast('Papers uploaded and indexed successfully!', 'success');
                await this.loadStats();
            } else {
                UI.showToast('Error uploading files', 'error');
            }
        } catch (error) {
            console.error('Upload error:', error);
            UI.showToast('Error uploading files', 'error');
        }
        
        this.resetUploadArea();
    },
    
    resetUploadArea() {
        const uploadArea = document.getElementById('uploadArea');
        const uploadBtn = document.getElementById('uploadBtn');
        
        uploadArea.innerHTML = `
            <div class="upload-icon">
                <i data-lucide="file-text" size="32" color="white"></i>
            </div>
            <h3>Drop PDF files here</h3>
            <p style="color: var(--text-secondary); font-size: 14px;">
                or click to browse
            </p>
        `;
        
        uploadBtn.innerHTML = '<i data-lucide="upload-cloud" size="20"></i> Upload & Process';
        uploadBtn.disabled = false;
        
        AppState.setSelectedFiles([]);
        lucide.createIcons();
    },
    
    async loadStats() {
        try {
            const stats = await API.getStats();
            document.getElementById('papersCount').textContent = stats.papers_count;
            document.getElementById('chunksCount').textContent = stats.chunks_count;
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }
};