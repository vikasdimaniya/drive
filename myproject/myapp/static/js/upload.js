// File upload functionality

// Initialize upload functionality
function initUpload() {
    // Get file name when file is selected
    document.getElementById('fileInput').addEventListener('change', function(e) {
        const fileName = e.target.files[0] ? e.target.files[0].name : 'Choose a file...';
        document.getElementById('fileLabel').textContent = fileName;
    });
    
    // Add click event to upload button
    document.getElementById('uploadBtn').addEventListener('click', startUpload);
}

// Start file upload
async function startUpload() {
    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];
    const progressContainer = document.getElementById("progressContainer");
    const progressFill = document.getElementById("progressFill");
    const progressText = document.getElementById("progressText");
    
    if (!file) {
        alert("Please select a file!");
        return;
    }
    
    // Show progress container
    progressContainer.style.display = "block";
    
    try {
        // Starting multipart upload
        let response = await fetch("/api/upload/multipart/start/", {
            method: "POST",
            body: JSON.stringify({ file_name: file.name }),
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
        });
        
        if (!response.ok) {
            throw new Error(`Failed to start upload: ${response.status}`);
        }
        
        let { upload_id, object_key } = await response.json();
        let chunkSize = 5 * 1024 * 1024; // 5MB per part
        let totalParts = Math.ceil(file.size / chunkSize);
        let uploadedParts = [];
        
        // Uploading each part
        for (let partNumber = 1; partNumber <= totalParts; partNumber++) {
            let start = (partNumber - 1) * chunkSize;
            let end = Math.min(start + chunkSize, file.size);
            let filePart = file.slice(start, end);
            
            // Getting presigned URL
            let presignedResp = await fetch("/api/upload/multipart/part/", {
                method: "POST",
                body: JSON.stringify({ object_key, upload_id, part_number: partNumber }),
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken()
                },
            });
            
            if (!presignedResp.ok) {
                throw new Error(`Failed to get presigned URL: ${presignedResp.status}`);
            }
            
            let { presigned_url } = await presignedResp.json();
            
            // Uploading chunk
            let uploadResponse = await fetch(presigned_url, {
                method: "PUT",
                body: filePart,
            });
            
            if (!uploadResponse.ok) {
                throw new Error(`Upload failed with status: ${uploadResponse.status}`);
            }
            
            let etag = uploadResponse.headers.get("ETag");
            uploadedParts.push({ PartNumber: partNumber, ETag: etag });
            
            // Update progress bar
            let progress = Math.round((partNumber / totalParts) * 100);
            progressFill.style.width = `${progress}%`;
            progressText.textContent = `${progress}%`;
        }
        
        // Completing the upload
        let completeResponse = await fetch("/api/upload/multipart/complete/", {
            method: "POST",
            body: JSON.stringify({ object_key, upload_id, parts: uploadedParts }),
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
        });
        
        if (!completeResponse.ok) {
            throw new Error(`Failed to complete upload: ${completeResponse.status}`);
        }
        
        // Reset file input and progress
        fileInput.value = "";
        document.getElementById("fileLabel").textContent = "Choose a file...";
        
        // Refresh file list
        fetchUserFiles();
        
        // Hide progress after a delay
        setTimeout(() => {
            progressContainer.style.display = "none";
            progressFill.style.width = "0%";
            progressText.textContent = "0%";
        }, 1500);
        
    } catch (error) {
        console.error("Upload error:", error);
        alert(`Upload failed: ${error.message}`);
        progressContainer.style.display = "none";
    }
} 