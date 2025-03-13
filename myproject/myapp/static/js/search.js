// Search functionality

// Initialize search functionality
function initSearch() {
    // Add click event to search button
    document.getElementById('searchBtn').addEventListener('click', searchFiles);
    
    // Add event listener for Enter key in search input
    document.getElementById("searchQuery").addEventListener("keyup", function(event) {
        if (event.key === "Enter") {
            searchFiles();
        }
    });
}

// Search files
async function searchFiles() {
    const query = document.getElementById("searchQuery").value;
    if (!query) return;
    
    try {
        let response = await fetch(`/api/user/search-files/?query=${query}`);
        let data = await response.json();
        let resultsList = document.getElementById("searchResultsContainer");
        let resultsSection = document.getElementById("searchResultsSection");
        
        resultsList.innerHTML = "";
        resultsSection.style.display = "block";
        
        if (data.files.length === 0) {
            resultsList.innerHTML = '<div class="empty-message">No matching files found.</div>';
            return;
        }
        
        // Sort files if needed
        sortFileData(data.files);
        
        // Create file items
        data.files.forEach(file => {
            const fileElement = createFileElement(file);
            resultsList.appendChild(fileElement);
        });
    } catch (error) {
        console.error("Error searching files:", error);
        document.getElementById("searchResultsContainer").innerHTML = 
            '<div class="empty-message">Error searching files. Please try again.</div>';
    }
} 