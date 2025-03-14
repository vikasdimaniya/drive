// Trash functionality

/**
 * Initialize trash functionality
 */
window.initTrash = function() {
    console.log("Initializing trash functionality");
    
    // Load trash when the trash tab is clicked
    const trashTab = document.getElementById('trashTab');
    if (trashTab) {
        trashTab.addEventListener('click', function() {
            loadTrash();
        });
    }
};

/**
 * Load trashed files
 */
window.loadTrash = function() {
    const container = document.getElementById('trashContainer');
    if (!container) {
        console.error("Could not find trashContainer element");
        return;
    }
    
    console.log("Loading trashed files...");
    container.innerHTML = '<div class="loading-message">Loading trash...</div>';
    
    fetch('/api/user/trash/')
        .then(response => response.json())
        .then(data => {
            if (data.files.length === 0) {
                container.innerHTML = '<div class="empty-message">Your trash is empty.</div>';
                return;
            }
            
            container.innerHTML = '';
            
            data.files.forEach(file => {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                fileItem.dataset.key = file.key;
                fileItem.dataset.name = file.name;
                
                const fileIcon = document.createElement('i');
                fileIcon.className = `fas ${getFileIcon(file.name)} file-icon`;
                
                const fileName = document.createElement('div');
                fileName.className = 'file-name';
                fileName.innerText = file.name;
                
                const fileInfo = document.createElement('div');
                fileInfo.className = 'file-info';
                fileInfo.innerHTML = `
                    <span>Size: ${formatFileSize(file.size)}</span>
                    <span>Trashed: ${formatDate(file.trash_date)}</span>
                    <span class="days-remaining">Deletes in: ${file.days_remaining} days</span>
                `;
                
                const fileActions = document.createElement('div');
                fileActions.className = 'file-actions';
                
                const restoreButton = document.createElement('button');
                restoreButton.className = 'file-btn restore-btn';
                restoreButton.innerHTML = '<i class="fas fa-trash-restore"></i> Restore';
                restoreButton.addEventListener('click', function(e) {
                    e.stopPropagation();
                    restoreFile(file.key, file.name);
                });
                
                fileActions.appendChild(restoreButton);
                
                fileItem.appendChild(fileIcon);
                fileItem.appendChild(fileName);
                fileItem.appendChild(fileInfo);
                fileItem.appendChild(fileActions);
                
                container.appendChild(fileItem);
            });
        })
        .catch(error => {
            console.error('Error loading trash:', error);
            container.innerHTML = '<div class="error-message">Error loading trash. Please try again.</div>';
        });
};

/**
 * Move a file to trash
 */
window.moveToTrash = function(fileKey, fileName) {
    if (confirm(`Are you sure you want to move "${fileName}" to trash? It will be automatically deleted after 30 days.`)) {
        // First, update the UI immediately for better user experience
        const fileItem = document.querySelector(`.file-item[data-key="${fileKey}"]`);
        if (fileItem) {
            fileItem.style.opacity = '0.5';
            fileItem.style.pointerEvents = 'none';
        }
        
        fetch('/api/user/move-to-trash/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                file_key: fileKey
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                console.log('File moved to trash:', data.message);
                
                // Remove the file from the UI
                if (fileItem) {
                    fileItem.remove();
                }
                
                // Check if there are any files left
                const container = document.getElementById('filesContainer');
                if (container && container.querySelectorAll('.file-item').length === 0) {
                    container.innerHTML = '<div class="empty-message">No files found.</div>';
                }
            } else {
                alert('Error: ' + data.error);
                // Restore the file item if there was an error
                if (fileItem) {
                    fileItem.style.opacity = '1';
                    fileItem.style.pointerEvents = 'auto';
                }
            }
        })
        .catch(error => {
            console.error('Error moving file to trash:', error);
            alert('Failed to move file to trash. Please try again.');
            // Restore the file item if there was an error
            if (fileItem) {
                fileItem.style.opacity = '1';
                fileItem.style.pointerEvents = 'auto';
            }
        });
    }
};

/**
 * Restore a file from trash
 */
window.restoreFile = function(fileKey, fileName) {
    if (confirm(`Are you sure you want to restore "${fileName}" from trash?`)) {
        // First, update the UI immediately for better user experience
        const fileItem = document.querySelector(`.file-item[data-key="${fileKey}"]`);
        if (fileItem) {
            fileItem.style.opacity = '0.5';
            fileItem.style.pointerEvents = 'none';
        }
        
        fetch('/api/user/restore-from-trash/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                file_key: fileKey
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                console.log('File restored from trash:', data.message);
                
                // Remove the file from the trash UI
                if (fileItem) {
                    fileItem.remove();
                }
                
                // Check if there are any files left in trash
                const container = document.getElementById('trashContainer');
                if (container && container.querySelectorAll('.file-item').length === 0) {
                    container.innerHTML = '<div class="empty-message">Your trash is empty.</div>';
                }
            } else {
                alert('Error: ' + data.error);
                // Restore the file item if there was an error
                if (fileItem) {
                    fileItem.style.opacity = '1';
                    fileItem.style.pointerEvents = 'auto';
                }
            }
        })
        .catch(error => {
            console.error('Error restoring file from trash:', error);
            alert('Failed to restore file. Please try again.');
            // Restore the file item if there was an error
            if (fileItem) {
                fileItem.style.opacity = '1';
                fileItem.style.pointerEvents = 'auto';
            }
        });
    }
};

/**
 * Empty trash (permanently delete all files)
 */
window.emptyTrash = function() {
    if (confirm('Are you sure you want to permanently delete all files in trash? This action cannot be undone.')) {
        fetch('/api/user/empty-trash/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert(data.message);
                // Reload the trash container
                const container = document.getElementById('trashContainer');
                if (container) {
                    container.innerHTML = '<div class="empty-message">Your trash is empty.</div>';
                }
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error emptying trash:', error);
            alert('Failed to empty trash. Please try again.');
        });
    }
};
