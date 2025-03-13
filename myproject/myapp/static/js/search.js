// Search functionality

// Global variables for search pagination and sorting
let searchCurrentPage = 1;
let searchPageSize = 20;
let searchCurrentSort = 'date';  // Default sort by date
let searchCurrentSortOrder = 'desc';  // Default newest first
let searchTotalPages = 1;
let lastSearchQuery = '';

// Initialize search functionality
function initSearch() {
    // Add click event to search button
    document.getElementById('searchBtn').addEventListener('click', () => searchFiles());
    
    // Add event listener for Enter key in search input
    document.getElementById("searchQuery").addEventListener("keyup", function(event) {
        if (event.key === "Enter") {
            searchFiles();
        }
    });
    
    // Listen for sort changes from the main sort select
    document.getElementById('sortSelect').addEventListener('change', function() {
        if (document.getElementById('searchResultsSection').style.display === 'block') {
            searchCurrentSort = this.value;
            searchFiles(1, searchCurrentSort, searchCurrentSortOrder);
        }
    });
    
    // Listen for sort order changes from the sort order button
    document.querySelector('.sort-order-btn')?.addEventListener('click', function() {
        if (document.getElementById('searchResultsSection').style.display === 'block') {
            searchCurrentSortOrder = searchCurrentSortOrder === 'asc' ? 'desc' : 'asc';
            searchFiles(1, searchCurrentSort, searchCurrentSortOrder);
        }
    });
}

// Search files
async function searchFiles(page = 1, sort = searchCurrentSort, order = searchCurrentSortOrder) {
    const query = document.getElementById("searchQuery").value;
    if (!query) return;
    
    // Update current values
    searchCurrentPage = page;
    searchCurrentSort = sort;
    searchCurrentSortOrder = order;
    lastSearchQuery = query;
    
    // Update the sort select in the UI to match current sort
    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect && sortSelect.value !== searchCurrentSort) {
        sortSelect.value = searchCurrentSort;
    }
    
    try {
        // Build query parameters
        const params = new URLSearchParams({
            query: query,
            page: page,
            page_size: searchPageSize,
            sort_by: sort,
            sort_order: order
        });
        
        let response = await fetch(`/api/user/search-files/?${params.toString()}`);
        let data = await response.json();
        let resultsList = document.getElementById("searchResultsContainer");
        let resultsSection = document.getElementById("searchResultsSection");
        
        resultsList.innerHTML = "";
        resultsSection.style.display = "block";
        
        if (data.files.length === 0) {
            resultsList.innerHTML = '<div class="empty-message">No matching files found.</div>';
            return;
        }
        
        // Store pagination info
        searchTotalPages = data.pagination.num_pages;
        
        // Create file items
        data.files.forEach(file => {
            const fileElement = createFileElement(file);
            resultsList.appendChild(fileElement);
        });
        
        // Create pagination controls
        createSearchPaginationControls(resultsList, data.pagination);
    } catch (error) {
        console.error("Error searching files:", error);
        document.getElementById("searchResultsContainer").innerHTML = 
            '<div class="empty-message">Error searching files. Please try again.</div>';
    }
}

// Create pagination controls for search results
function createSearchPaginationControls(container, pagination) {
    // Remove any existing pagination bar
    const existingPaginationBar = document.querySelector('.search-pagination-bar');
    if (existingPaginationBar) {
        existingPaginationBar.remove();
    }
    
    // Create pagination bar (similar to view options bar)
    const paginationBar = document.createElement('div');
    paginationBar.className = 'pagination-bar search-pagination-bar';
    
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
            searchFiles(searchCurrentPage - 1);
        }
    });
    
    // Next button
    const nextButton = document.createElement('button');
    nextButton.className = 'pagination-btn next-btn';
    nextButton.innerHTML = 'Next <i class="fas fa-chevron-right"></i>';
    nextButton.disabled = !pagination.has_next;
    nextButton.addEventListener('click', () => {
        if (pagination.has_next) {
            searchFiles(searchCurrentPage + 1);
        }
    });
    
    // Add elements to pagination controls
    paginationControls.appendChild(prevButton);
    paginationControls.appendChild(nextButton);
    
    // Add elements to pagination bar
    paginationBar.appendChild(pageInfo);
    paginationBar.appendChild(paginationControls);
    
    // Add pagination bar to the container
    // Insert it before the search results container
    const searchResultsContainer = document.getElementById('searchResultsContainer');
    searchResultsContainer.parentNode.insertBefore(paginationBar, searchResultsContainer.nextSibling);
} 