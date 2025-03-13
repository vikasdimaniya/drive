/**
 * Shared links functionality
 */

function initShare() {
    // Listen for share button clicks in the file context menu
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('share-file-btn') || e.target.closest('.share-file-btn')) {
            const fileItem = e.target.closest('.file-item');
            const fileKey = fileItem.dataset.key;
            const fileName = fileItem.dataset.name;
            
            createShareLink(fileKey, fileName);
        }
        
        // Listen for revoke access button clicks
        if (e.target.classList.contains('revoke-access-btn') || e.target.closest('.revoke-access-btn')) {
            const fileItem = e.target.closest('.file-item');
            const token = fileItem.dataset.token;
            const fileName = fileItem.dataset.name;
            
            revokeAccess(token, fileName);
        }
    });
    
    // Initialize shared tabs if they exist
    const sharedWithMeTab = document.getElementById('sharedWithMeTab');
    const sharedByMeTab = document.getElementById('sharedByMeTab');
    
    if (sharedWithMeTab) {
        sharedWithMeTab.addEventListener('click', function() {
            loadSharedWithMe();
        });
    }
    
    if (sharedByMeTab) {
        sharedByMeTab.addEventListener('click', function() {
            loadSharedByMe();
        });
    }
}

/**
 * Create a shared link for a file
 * @param {string} fileKey - The file key
 * @param {string} fileName - The file name for display
 */
function createShareLink(fileKey, fileName) {
    // Create modal for sharing options
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Share "${fileName}"</h3>
                <span class="close-modal">&times;</span>
            </div>
            <div class="modal-body">
                <p>Share this file with another user:</p>
                <div class="form-group">
                    <label for="recipientEmail">Recipient Email:</label>
                    <input type="email" id="recipientEmail" placeholder="Enter email address" required>
                </div>
                <div class="form-group">
                    <label for="expiryDays">Link expires after (optional):</label>
                    <select id="expiryDays">
                        <option value="">Never</option>
                        <option value="1">1 day</option>
                        <option value="3">3 days</option>
                        <option value="7">7 days</option>
                        <option value="14">14 days</option>
                        <option value="30">30 days</option>
                    </select>
                </div>
                <div class="share-result" style="display: none;">
                    <p>File shared successfully!</p>
                    <div class="share-link-container">
                        <input type="text" id="shareLink" readonly>
                        <button id="copyLinkBtn"><i class="fas fa-copy"></i></button>
                    </div>
                    <p class="share-note">The recipient will receive an email with the link.</p>
                </div>
            </div>
            <div class="modal-footer">
                <button id="createLinkBtn" class="primary-btn">Share</button>
                <button class="cancel-btn close-modal">Cancel</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Show modal
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
    
    // Handle close modal
    const closeModal = () => {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.remove();
        }, 300);
    };
    
    // Add event listeners
    modal.querySelectorAll('.close-modal').forEach(el => {
        el.addEventListener('click', closeModal);
    });
    
    // Handle create link button
    const createLinkBtn = modal.querySelector('#createLinkBtn');
    createLinkBtn.addEventListener('click', async () => {
        const recipientEmail = modal.querySelector('#recipientEmail').value.trim();
        const expiryDays = modal.querySelector('#expiryDays').value;
        
        if (!recipientEmail) {
            alert('Please enter a recipient email address');
            return;
        }
        
        try {
            createLinkBtn.disabled = true;
            createLinkBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sharing...';
            
            const response = await fetch('/api/user/create-shared-link/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    file_key: fileKey,
                    recipient_email: recipientEmail,
                    expiry_days: expiryDays
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to share file');
            }
            
            const data = await response.json();
            
            // Show the share result
            modal.querySelector('.share-result').style.display = 'block';
            modal.querySelector('#shareLink').value = data.share_url;
            
            // Update button
            createLinkBtn.innerHTML = 'Share Again';
            createLinkBtn.disabled = false;
            
            // Setup copy button
            const copyBtn = modal.querySelector('#copyLinkBtn');
            copyBtn.addEventListener('click', () => {
                const linkInput = modal.querySelector('#shareLink');
                linkInput.select();
                document.execCommand('copy');
                
                // Show copied notification
                const originalText = copyBtn.innerHTML;
                copyBtn.innerHTML = '<i class="fas fa-check"></i>';
                setTimeout(() => {
                    copyBtn.innerHTML = originalText;
                }, 2000);
            });
            
        } catch (error) {
            console.error('Error sharing file:', error);
            alert('Failed to share file. Please try again.');
            createLinkBtn.innerHTML = 'Share';
            createLinkBtn.disabled = false;
        }
    });
}

/**
 * Revoke access to a shared file
 * @param {string} token - The shared link token
 * @param {string} fileName - The file name for display
 */
function revokeAccess(token, fileName) {
    if (confirm(`Are you sure you want to revoke access to "${fileName}"?`)) {
        fetch('/api/user/revoke-access/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                token: token
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert('Access revoked successfully');
                // Refresh the shared by me list
                loadSharedByMe();
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error revoking access:', error);
            alert('Failed to revoke access. Please try again.');
        });
    }
}

/**
 * Load files shared with the current user
 */
function loadSharedWithMe() {
    const container = document.getElementById('sharedWithMeContainer');
    if (!container) return;
    
    container.innerHTML = '<div class="loading-message">Loading shared files...</div>';
    
    fetch('/api/user/shared-with-me/')
        .then(response => response.json())
        .then(data => {
            if (data.files.length === 0) {
                container.innerHTML = '<div class="empty-message">No files have been shared with you.</div>';
                return;
            }
            
            container.innerHTML = '';
            
            data.files.forEach(file => {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                fileItem.dataset.key = file.key;
                fileItem.dataset.name = file.name;
                fileItem.dataset.token = file.token;
                
                const fileIcon = document.createElement('i');
                fileIcon.className = `fas ${getFileIcon(file.name)} file-icon`;
                
                const fileName = document.createElement('div');
                fileName.className = 'file-name';
                fileName.innerText = file.name;
                
                const fileInfo = document.createElement('div');
                fileInfo.className = 'file-info';
                fileInfo.innerHTML = `
                    <span>Shared by: ${file.shared_by}</span>
                    <span>Date: ${formatDate(file.shared_date)}</span>
                    ${file.expires_at ? `<span>Expires: ${formatDate(file.expires_at)}</span>` : ''}
                `;
                
                const fileActions = document.createElement('div');
                fileActions.className = 'file-actions';
                
                const downloadButton = document.createElement('button');
                downloadButton.className = 'file-btn download-btn';
                downloadButton.innerHTML = '<i class="fas fa-download"></i> Download';
                downloadButton.addEventListener('click', function(e) {
                    e.stopPropagation();
                    downloadFile(file.key);
                });
                
                fileActions.appendChild(downloadButton);
                
                fileItem.appendChild(fileIcon);
                fileItem.appendChild(fileName);
                fileItem.appendChild(fileInfo);
                fileItem.appendChild(fileActions);
                
                container.appendChild(fileItem);
            });
        })
        .catch(error => {
            console.error('Error loading shared files:', error);
            container.innerHTML = '<div class="error-message">Error loading shared files. Please try again.</div>';
        });
}

/**
 * Load files shared by the current user
 */
function loadSharedByMe() {
    const container = document.getElementById('sharedByMeContainer');
    if (!container) return;
    
    container.innerHTML = '<div class="loading-message">Loading shared files...</div>';
    
    fetch('/api/user/shared-by-me/')
        .then(response => response.json())
        .then(data => {
            if (data.files.length === 0) {
                container.innerHTML = '<div class="empty-message">You haven\'t shared any files yet.</div>';
                return;
            }
            
            container.innerHTML = '';
            
            data.files.forEach(file => {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                fileItem.dataset.key = file.key;
                fileItem.dataset.name = file.name;
                fileItem.dataset.token = file.token;
                
                // Add status class
                if (!file.is_active) {
                    fileItem.classList.add('revoked');
                } else if (file.expires_at && new Date(file.expires_at) < new Date()) {
                    fileItem.classList.add('expired');
                }
                
                const fileIcon = document.createElement('i');
                fileIcon.className = `fas ${getFileIcon(file.name)} file-icon`;
                
                const fileName = document.createElement('div');
                fileName.className = 'file-name';
                fileName.innerText = file.name;
                
                const fileInfo = document.createElement('div');
                fileInfo.className = 'file-info';
                fileInfo.innerHTML = `
                    <span>Shared with: ${file.shared_with}</span>
                    <span>Date: ${formatDate(file.shared_date)}</span>
                    ${file.expires_at ? `<span>Expires: ${formatDate(file.expires_at)}</span>` : ''}
                    <span class="status-badge ${file.is_valid ? 'active' : 'inactive'}">${file.is_valid ? 'Active' : 'Inactive'}</span>
                `;
                
                const fileActions = document.createElement('div');
                fileActions.className = 'file-actions';
                
                if (file.is_active) {
                    const revokeButton = document.createElement('button');
                    revokeButton.className = 'file-btn revoke-access-btn';
                    revokeButton.innerHTML = '<i class="fas fa-ban"></i> Revoke Access';
                    revokeButton.addEventListener('click', function(e) {
                        e.stopPropagation();
                        // The revoke functionality is handled by the event listener
                    });
                    
                    fileActions.appendChild(revokeButton);
                }
                
                fileItem.appendChild(fileIcon);
                fileItem.appendChild(fileName);
                fileItem.appendChild(fileInfo);
                fileItem.appendChild(fileActions);
                
                container.appendChild(fileItem);
            });
        })
        .catch(error => {
            console.error('Error loading shared files:', error);
            container.innerHTML = '<div class="error-message">Error loading shared files. Please try again.</div>';
        });
}

/**
 * Format a date string
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
} 