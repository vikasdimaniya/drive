// File explorer functionality

// Global variables
let currentView = 'grid';
let currentSize = 'medium';
let currentSort = 'name';

// Initialize file explorer
function initFileExplorer() {
    // Load files on page load
    fetchUserFiles();
    
    // Set up view option buttons
    document.querySelectorAll('.view-option-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            changeView(this.dataset.view);
        });
    });
    
    // Set up size option buttons
    document.querySelectorAll('.size-option-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            changeSize(this.dataset.size);
        });
    });
    
    // Set up sort select
    document.getElementById('sortSelect').addEventListener('change', function() {
        currentSort = this.value;
        sortFiles();
    });
}

// Fetch user files
async function fetchUserFiles() {
    try {
        let response = await fetch("/api/user/files/");
        let data = await response.json();
        let filesContainer = document.getElementById("filesContainer");
        
        filesContainer.innerHTML = "";  // Clear existing content
        
        if (data.files.length === 0) {
            filesContainer.innerHTML = '<div class="empty-message">No files uploaded yet.</div>';
            return;
        }
        
        // Sort files
        sortFileData(data.files);
        
        // Create file items based on current view
        data.files.forEach(file => {
            const fileElement = createFileElement(file);
            filesContainer.appendChild(fileElement);
        });
    } catch (error) {
        console.error("Error fetching files:", error);
        document.getElementById("filesContainer").innerHTML = 
            '<div class="empty-message">Error loading files. Please try again.</div>';
    }
}

// Sort file data
function sortFileData(files) {
    switch(currentSort) {
        case 'name':
            files.sort((a, b) => a.name.localeCompare(b.name));
            break;
        case 'date':
            // Assuming we have a date field, if not this will need to be adjusted
            files.sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0));
            break;
        case 'size':
            // Assuming we have a size field, if not this will need to be adjusted
            files.sort((a, b) => (b.size || 0) - (a.size || 0));
            break;
        case 'type':
            files.sort((a, b) => {
                const typeA = a.name.split('.').pop().toLowerCase();
                const typeB = b.name.split('.').pop().toLowerCase();
                return typeA.localeCompare(typeB);
            });
            break;
    }
}

// Create file element based on current view
function createFileElement(file) {
    if (currentView === 'list') {
        return createListViewItem(file);
    } else {
        return createGridViewItem(file);
    }
}

// Create grid view item
function createGridViewItem(file) {
    const fileItem = document.createElement("div");
    fileItem.className = "file-item";
    fileItem.dataset.fileKey = file.key;
    
    // File icon
    const fileIcon = document.createElement("i");
    fileIcon.className = `fas ${getFileIcon(file.name)} file-icon`;
    
    // File name
    const fileName = document.createElement("div");
    fileName.className = "file-name";
    fileName.innerText = file.name;
    
    // File actions
    const fileActions = document.createElement("div");
    fileActions.className = "file-actions";
    
    // Download button
    const downloadButton = document.createElement("button");
    downloadButton.className = "file-btn download-btn";
    downloadButton.innerHTML = '<i class="fas fa-download"></i>';
    downloadButton.title = "Download";
    downloadButton.addEventListener("click", function(e) {
        e.stopPropagation();
        downloadFile(file.key);
    });
    
    // Delete button
    const deleteButton = document.createElement("button");
    deleteButton.className = "file-btn delete-btn";
    deleteButton.innerHTML = '<i class="fas fa-trash-alt"></i>';
    deleteButton.title = "Delete";
    deleteButton.addEventListener("click", function(e) {
        e.stopPropagation();
        deleteFile(file.key);
    });
    
    fileActions.appendChild(downloadButton);
    fileActions.appendChild(deleteButton);
    
    fileItem.appendChild(fileIcon);
    fileItem.appendChild(fileName);
    fileItem.appendChild(fileActions);
    
    // Add click event to select the file
    return addClickEvent(fileItem);
}

// Create list view item
function createListViewItem(file) {
    const fileItem = document.createElement("div");
    fileItem.className = "file-item";
    fileItem.dataset.fileKey = file.key;
    
    // File icon
    const fileIcon = document.createElement("i");
    fileIcon.className = `fas ${getFileIcon(file.name)} file-icon`;
    
    // File name
    const fileName = document.createElement("div");
    fileName.className = "file-name";
    fileName.innerText = file.name;
    
    // File actions
    const fileActions = document.createElement("div");
    fileActions.className = "file-actions";
    
    // Download button
    const downloadButton = document.createElement("button");
    downloadButton.className = "file-btn download-btn";
    downloadButton.innerHTML = '<i class="fas fa-download"></i> Download';
    downloadButton.addEventListener("click", function(e) {
        e.stopPropagation();
        downloadFile(file.key);
    });
    
    // Delete button
    const deleteButton = document.createElement("button");
    deleteButton.className = "file-btn delete-btn";
    deleteButton.innerHTML = '<i class="fas fa-trash-alt"></i> Delete';
    deleteButton.addEventListener("click", function(e) {
        e.stopPropagation();
        deleteFile(file.key);
    });
    
    fileActions.appendChild(downloadButton);
    fileActions.appendChild(deleteButton);
    
    fileItem.appendChild(fileIcon);
    fileItem.appendChild(fileName);
    fileItem.appendChild(fileActions);
    
    // Add click event to select the file
    return addClickEvent(fileItem);
}

// Add click event to select the file
function addClickEvent(fileItem) {
    fileItem.addEventListener("click", function() {
        document.querySelectorAll(".file-item").forEach(item => {
            item.classList.remove("selected");
        });
        this.classList.add("selected");
    });
    
    return fileItem;
}

// Change view (grid, list)
function changeView(viewType) {
    currentView = viewType;
    
    const filesContainer = document.getElementById('filesContainer');
    const searchResultsContainer = document.getElementById('searchResultsContainer');
    
    // Remove all view classes
    filesContainer.classList.remove('view-grid', 'view-list');
    searchResultsContainer.classList.remove('view-grid', 'view-list');
    
    // Add the selected view class
    filesContainer.classList.add(`view-${viewType}`);
    searchResultsContainer.classList.add(`view-${viewType}`);
    
    // Update active button
    document.querySelectorAll('.view-option-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.view-option-btn[data-view="${viewType}"]`).classList.add('active');
    
    // Refresh files with new view
    fetchUserFiles();
}

// Change icon size
function changeSize(sizeType) {
    currentSize = sizeType;
    
    const filesContainer = document.getElementById('filesContainer');
    const searchResultsContainer = document.getElementById('searchResultsContainer');
    
    // Remove all size classes
    filesContainer.classList.remove('size-small', 'size-medium', 'size-large');
    searchResultsContainer.classList.remove('size-small', 'size-medium', 'size-large');
    
    // Add the selected size class
    filesContainer.classList.add(`size-${sizeType}`);
    searchResultsContainer.classList.add(`size-${sizeType}`);
    
    // Update active button
    document.querySelectorAll('.size-option-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.size-option-btn[data-size="${sizeType}"]`).classList.add('active');
}

// Sort files
function sortFiles() {
    fetchUserFiles();
}

// Download file
async function downloadFile(fileKey) {
    try {
        let response = await fetch("/api/user/file-url/", {
            method: "POST",
            body: JSON.stringify({ file_key: fileKey }),
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
        });
        
        let data = await response.json();
        if (data.presigned_url) {
            let tempLink = document.createElement("a");
            tempLink.href = data.presigned_url;
            tempLink.style.display = "none";
            tempLink.download = fileKey.split('/').pop(); // Extracts file name
            
            document.body.appendChild(tempLink);
            tempLink.click();  // Force browser to start download
            document.body.removeChild(tempLink); // Cleanup
        } else {
            alert("Failed to generate download link.");
        }
    } catch (error) {
        console.error("Error fetching pre-signed URL:", error);
        alert("Error downloading file. Please try again.");
    }
}

// Delete file
async function deleteFile(fileKey) {
    let confirmation = confirm("Are you sure you want to delete this file?");
    if (!confirmation) return;
    
    try {
        let response = await fetch("/api/user/delete-file/", {
            method: "POST",
            body: JSON.stringify({ file_key: fileKey }),
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
        });
        
        let data = await response.json();
        if (data.message === "File deleted successfully") {
            fetchUserFiles();
        } else {
            alert("Failed to delete file: " + data.error);
        }
    } catch (error) {
        console.error("Error deleting file:", error);
        alert("Error deleting file. Please try again.");
    }
} 