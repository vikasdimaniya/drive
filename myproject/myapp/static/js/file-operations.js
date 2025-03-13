// Common utility functions and file operations
function getCSRFToken() {
    return document.cookie.split("; ")
        .find(row => row.startsWith("csrftoken="))
        ?.split("=")[1];
}

const csrfToken = getCSRFToken() || "";

// Load the user's file list on page load
document.addEventListener("DOMContentLoaded", function() {
    fetchUserFiles();
});

function getFileIcon(fileName) {
    const extension = fileName.split('.').pop().toLowerCase();
    
    const iconMap = {
        'pdf': 'fa-file-pdf',
        'doc': 'fa-file-word',
        'docx': 'fa-file-word',
        'xls': 'fa-file-excel',
        'xlsx': 'fa-file-excel',
        'ppt': 'fa-file-powerpoint',
        'pptx': 'fa-file-powerpoint',
        'jpg': 'fa-file-image',
        'jpeg': 'fa-file-image',
        'png': 'fa-file-image',
        'gif': 'fa-file-image',
        'txt': 'fa-file-alt',
        'zip': 'fa-file-archive',
        'rar': 'fa-file-archive',
        'mp3': 'fa-file-audio',
        'mp4': 'fa-file-video',
        'mov': 'fa-file-video'
    };
    
    return iconMap[extension] || 'fa-file';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

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
        
        // Get current view and size
        const currentView = filesContainer.className.includes('view-list') ? 'list' : 
                           filesContainer.className.includes('view-columns') ? 'columns' : 'grid';
        const currentSize = filesContainer.className.includes('size-small') ? 'small' : 
                           filesContainer.className.includes('size-large') ? 'large' : 'medium';
        
        // Create files based on current view
        data.files.forEach(file => {
            const fileElement = createFileElement(file, currentView);
            filesContainer.appendChild(fileElement);
        });
        
        // If column view, initialize the first column
        if (currentView === 'columns') {
            initializeColumnView(filesContainer, data.files);
        }
    } catch (error) {
        console.error("Error fetching files:", error);
        document.getElementById("filesContainer").innerHTML = 
            '<div class="empty-message">Error loading files. Please try again.</div>';
    }
}

function createFileElement(file, viewType) {
    if (viewType === 'list') {
        return createListViewItem(file);
    } else if (viewType === 'columns') {
        return createColumnViewItem(file);
    } else {
        return createGridViewItem(file);
    }
}

function createGridViewItem(file) {
    const fileItem = document.createElement("div");
    fileItem.className = "file-item";
    fileItem.dataset.fileKey = file.key;
    fileItem.dataset.fileName = file.name;
    
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
    fileItem.addEventListener("click", function() {
        // Toggle selection
        document.querySelectorAll(".file-item").forEach(item => {
            item.classList.remove("selected");
        });
        this.classList.add("selected");
    });
    
    return fileItem;
}

function createListViewItem(file) {
    const fileItem = document.createElement("div");
    fileItem.className = "file-item";
    fileItem.dataset.fileKey = file.key;
    fileItem.dataset.fileName = file.name;
    
    // File icon
    const fileIcon = document.createElement("i");
    fileIcon.className = `fas ${getFileIcon(file.name)} file-icon`;
    
    // File name
    const fileName = document.createElement("div");
    fileName.className = "file-name";
    fileName.innerText = file.name;
    
    // File details (we'll use placeholder data since we don't have this info)
    const fileDetails = document.createElement("div");
    fileDetails.className = "file-details";
    
    const fileSize = document.createElement("span");
    fileSize.className = "file-size";
    fileSize.textContent = formatFileSize(file.size);
    
    fileDetails.appendChild(fileSize);
    return fileDetails;
} 