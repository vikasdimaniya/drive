// File explorer functionality

// Global variables
let currentView = 'grid';
let currentSize = 'medium';
let currentSort = 'date';
let currentSortOrder = 'desc';
let currentPage = 1;
let pageSize = 20;
let totalPages = 1;

// Initialize file explorer
function initFileExplorer() {
    // Set up sort order button first so it's available for fetchUserFiles
    const sortOptions = document.querySelector('.sort-options');
    if (sortOptions && !document.querySelector('.sort-order-btn')) {
        const sortOrderBtn = document.createElement('button');
        sortOrderBtn.className = 'sort-order-btn';
        sortOrderBtn.title = currentSortOrder === 'asc' ? 'Ascending' : 'Descending';
        sortOrderBtn.innerHTML = currentSortOrder === 'asc' ? 
            '<i class="fas fa-sort-amount-up"></i>' : 
            '<i class="fas fa-sort-amount-down"></i>';
        
        sortOrderBtn.addEventListener('click', function() {
            currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
            this.title = currentSortOrder === 'asc' ? 'Ascending' : 'Descending';
            this.innerHTML = currentSortOrder === 'asc' ? 
                '<i class="fas fa-sort-amount-up"></i>' : 
                '<i class="fas fa-sort-amount-down"></i>';
            fetchUserFiles(1, currentSort, currentSortOrder);
        });
        
        sortOptions.appendChild(sortOrderBtn);
    }
    
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
    
    // Set up sort option buttons
    document.querySelectorAll('.sort-option-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            changeSort(this.dataset.sort);
        });
    });
    
    // Set up search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                searchFiles();
            }
        });
    }
    
    const searchButton = document.getElementById('searchButton');
    if (searchButton) {
        searchButton.addEventListener('click', function() {
            searchFiles();
        });
    }
    
    // Initialize trash functionality if available
    if (typeof initTrash === 'function') {
        initTrash();
    }
    
    // Set up tab navigation
    setupTabNavigation();
}

// Set up tab navigation
function setupTabNavigation() {
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Remove active class from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Hide all tab contents
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Show the corresponding tab content
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId + 'Content').classList.add('active');
            
            // If trash tab is clicked, load trash
            if (tabId === 'trash' && typeof loadTrash === 'function') {
                loadTrash();
            }
        });
    });
}

// Fetch user files
async function fetchUserFiles(page = currentPage, sort = currentSort, order = currentSortOrder) {
    try {
        // Update current values
        currentPage = page;
        currentSort = sort;
        currentSortOrder = order;
        
        // Build query parameters
        const params = new URLSearchParams({
            page: page,
            page_size: pageSize,
            sort_by: sort,
            sort_order: order
        });
        
        let response = await fetch(`/api/user/files/?${params.toString()}`);
        let data = await response.json();
        let filesContainer = document.getElementById("filesContainer");
        
        filesContainer.innerHTML = "";  // Clear existing content
        
        if (data.files.length === 0) {
            filesContainer.innerHTML = '<div class="empty-message">No files uploaded yet.</div>';
            return;
        }
        
        // Store pagination info
        totalPages = data.pagination.num_pages;
        
        // Create file items based on current view
        data.files.forEach(file => {
            const fileElement = createFileElement(file);
            filesContainer.appendChild(fileElement);
        });
        
        // Create pagination controls
        createPaginationControls(filesContainer, data.pagination);
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
    console.log("Creating grid view item for file:", file);
    
    const fileItem = document.createElement("div");
    fileItem.className = "file-item";
    fileItem.dataset.key = file.key;
    fileItem.dataset.fileKey = file.key;
    fileItem.dataset.name = file.name;
    
    console.log("File item dataset:", fileItem.dataset);
    
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
    
    // Share button
    const shareButton = document.createElement("button");
    shareButton.className = "file-btn share-file-btn";
    shareButton.innerHTML = '<i class="fas fa-share-alt"></i>';
    shareButton.title = 'Share';
    shareButton.addEventListener("click", function(e) {
        console.log("Share button clicked directly (grid view)");
        e.stopPropagation();
        // Directly call createShareLink if it exists
        if (typeof createShareLink === 'function') {
            createShareLink(file.key, file.name);
        } else {
            console.error("createShareLink function not found");
        }
    });
    
    // Download button
    const downloadButton = document.createElement("button");
    downloadButton.className = "file-btn download-btn";
    downloadButton.innerHTML = '<i class="fas fa-download"></i>';
    downloadButton.title = 'Download';
    downloadButton.addEventListener("click", function(e) {
        e.stopPropagation();
        downloadFile(file.key);
    });
    
    // Trash button
    const trashButton = document.createElement('button');
    trashButton.className = 'file-btn trash-btn';
    trashButton.innerHTML = '<i class="fas fa-trash"></i>';
    trashButton.title = 'Move to Trash';
    trashButton.addEventListener('click', function(e) {
        e.stopPropagation();
        if (typeof moveToTrash === 'function') {
            moveToTrash(file.key, file.name);
        } else {
            console.error("moveToTrash function not found");
            alert("Trash functionality is not available");
        }
    });
    
    fileActions.appendChild(shareButton);
    fileActions.appendChild(downloadButton);
    fileActions.appendChild(trashButton);
    
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
    fileItem.dataset.key = file.key;
    fileItem.dataset.fileKey = file.key;
    fileItem.dataset.name = file.name;
    
    // File icon
    const fileIcon = document.createElement("i");
    fileIcon.className = `fas ${getFileIcon(file.name)} file-icon`;
    
    // File name
    const fileName = document.createElement("div");
    fileName.className = "file-name";
    fileName.innerText = file.name;
    
    // File details
    const fileDetails = document.createElement("div");
    fileDetails.className = "file-details";
    
    // File size
    const fileSize = document.createElement("span");
    fileSize.className = "file-size";
    fileSize.textContent = formatFileSize(file.size);
    
    // File date
    const fileDate = document.createElement("span");
    fileDate.className = "file-date";
    fileDate.textContent = formatDate(file.upload_date);
    
    // File type
    const fileType = document.createElement("span");
    fileType.className = "file-type";
    fileType.textContent = file.type || file.name.split('.').pop().toUpperCase();
    
    // Add details to file details container
    fileDetails.appendChild(fileSize);
    fileDetails.appendChild(fileDate);
    fileDetails.appendChild(fileType);
    
    // File actions
    const fileActions = document.createElement("div");
    fileActions.className = "file-actions";
    
    // Share button
    const shareButton = document.createElement("button");
    shareButton.className = "file-btn share-file-btn";
    shareButton.innerHTML = '<i class="fas fa-share-alt"></i> Share';
    shareButton.addEventListener("click", function(e) {
        console.log("Share button clicked directly (list view)");
        e.stopPropagation();
        // Directly call createShareLink if it exists
        if (typeof createShareLink === 'function') {
            createShareLink(file.key, file.name);
        } else {
            console.error("createShareLink function not found");
        }
    });
    
    // Download button
    const downloadButton = document.createElement("button");
    downloadButton.className = "file-btn download-btn";
    downloadButton.innerHTML = '<i class="fas fa-download"></i> Download';
    downloadButton.addEventListener("click", function(e) {
        e.stopPropagation();
        downloadFile(file.key);
    });
    
    // Trash button
    const trashButton = document.createElement('button');
    trashButton.className = 'file-btn trash-btn';
    trashButton.innerHTML = '<i class="fas fa-trash"></i> Trash';
    trashButton.addEventListener('click', function(e) {
        e.stopPropagation();
        if (typeof moveToTrash === 'function') {
            moveToTrash(file.key, file.name);
        } else {
            console.error("moveToTrash function not found");
            alert("Trash functionality is not available");
        }
    });
    
    fileActions.appendChild(shareButton);
    fileActions.appendChild(downloadButton);
    fileActions.appendChild(trashButton);
    
    fileItem.appendChild(fileIcon);
    fileItem.appendChild(fileName);
    fileItem.appendChild(fileDetails);
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
    if (!fileKey) {
        console.error("No file key provided for download");
        return;
    }
    
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
    if (!fileKey) {
        console.error("No file key provided for deletion");
        return;
    }
    
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

// Create pagination controls
function createPaginationControls(container, pagination) {
    // Remove any existing pagination bar
    const existingPaginationBar = document.querySelector('.pagination-bar');
    if (existingPaginationBar) {
        existingPaginationBar.remove();
    }
    
    // Create pagination bar (similar to view options bar)
    const paginationBar = document.createElement('div');
    paginationBar.className = 'pagination-bar';
    
    // Page info
    const pageInfo = document.createElement('span');
    pageInfo.className = 'pagination-info';
    pageInfo.textContent = `Page ${pagination.page} of ${pagination.num_pages}`;
    
    // Pagination controls container
    const paginationControls = document.createElement('div');
    paginationControls.className = 'pagination-controls';
    
    // Previous button
    const prevButton = document.createElement('button');
    prevButton.className = 'pagination-btn prev-btn';
    prevButton.innerHTML = '<i class="fas fa-chevron-left"></i> Previous';
    prevButton.disabled = !pagination.has_previous;
    prevButton.addEventListener('click', () => {
        if (pagination.has_previous) {
            fetchUserFiles(currentPage - 1);
        }
    });
    
    // Next button
    const nextButton = document.createElement('button');
    nextButton.className = 'pagination-btn next-btn';
    nextButton.innerHTML = 'Next <i class="fas fa-chevron-right"></i>';
    nextButton.disabled = !pagination.has_next;
    nextButton.addEventListener('click', () => {
        if (pagination.has_next) {
            fetchUserFiles(currentPage + 1);
        }
    });
    
    // Add elements to pagination controls
    paginationControls.appendChild(prevButton);
    paginationControls.appendChild(nextButton);
    
    // Add elements to pagination bar
    paginationBar.appendChild(pageInfo);
    paginationBar.appendChild(paginationControls);
    
    // Add pagination bar to the container
    // Insert it before the files container
    const filesContainer = document.getElementById('filesContainer');
    filesContainer.parentNode.insertBefore(paginationBar, filesContainer.nextSibling);
} 