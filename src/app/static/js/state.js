const AppState = {
    selectedFiles: [],
    selectedPapers: [],
    arxivResults: [],
    uploadedImage: null,
    
    // Setters
    setSelectedFiles(files) {
        this.selectedFiles = files;
    },
    
    addSelectedPaper(paperId) {
        if (!this.selectedPapers.includes(paperId)) {
            this.selectedPapers.push(paperId);
        }
    },
    
    removeSelectedPaper(paperId) {
        this.selectedPapers = this.selectedPapers.filter(id => id !== paperId);
    },
    
    clearSelectedPapers() {
        this.selectedPapers = [];
    },
    
    setArxivResults(results) {
        this.arxivResults = results;
    },
    
    setUploadedImage(image) {
        this.uploadedImage = image;
    },
    
    clearUploadedImage() {
        this.uploadedImage = null;
    }
};