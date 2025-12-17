/**
 * Secret Admin Clock with Hidden Trigger
 * No visual hints, no timer bar, completely hidden
 * Only activates on 15-second long press + 5 taps
 */

class SecretAdminClock {
    constructor() {
        this.clockElement = document.getElementById('secret-clock');
        this.isEditMode = false;
        this.longPressTimer = null;
        this.longPressDuration = 15000; // 15 seconds
        this.tapCount = 0;
        this.tapTimeout = null;
        this.isLongPressing = false;
        
        this.init();
    }
    
    init() {
        // Update clock every second
        this.updateClock();
        setInterval(() => this.updateClock(), 1000);
        
        // Setup event listeners for secret trigger
        this.setupSecretTrigger();
    }
    
    updateClock() {
        if (!this.clockElement) return;
        
        if (this.isEditMode) {
            // Don't update in edit mode
            return;
        }
        
        // Get current Indian Standard Time (IST)
        const now = new Date();
        const istOffset = 5.5 * 60 * 60 * 1000; // IST is UTC+5:30
        const istTime = new Date(now.getTime() + istOffset);
        
        // Format time in 12-hour format with AM/PM
        let hours = istTime.getUTCHours();
        const minutes = istTime.getUTCMinutes().toString().padStart(2, '0');
        const seconds = istTime.getUTCSeconds().toString().padStart(2, '0');
        const ampm = hours >= 12 ? 'PM' : 'AM';
        
        hours = hours % 12;
        hours = hours ? hours : 12; // Convert 0 to 12
        
        this.clockElement.textContent = `${hours}:${minutes}:${seconds} ${ampm}`;
    }
    
    setupSecretTrigger() {
        if (!this.clockElement) return;
        
        // Mouse/touch events
        this.clockElement.addEventListener('mousedown', (e) => this.startLongPress(e));
        this.clockElement.addEventListener('touchstart', (e) => this.startLongPress(e));
        
        this.clockElement.addEventListener('mouseup', (e) => this.endLongPress(e));
        this.clockElement.addEventListener('touchend', (e) => this.endLongPress(e));
        this.clockElement.addEventListener('mouseleave', (e) => this.endLongPress(e));
        
        // Click/tap events
        this.clockElement.addEventListener('click', (e) => this.handleTap(e));
        this.clockElement.addEventListener('touchend', (e) => this.handleTap(e));
    }
    
    startLongPress(e) {
        e.preventDefault();
        
        // Only start if not already in edit mode
        if (this.isEditMode) return;
        
        this.isLongPressing = true;
        
        // Clear any existing timer
        if (this.longPressTimer) {
            clearTimeout(this.longPressTimer);
        }
        
        // Start new long press timer
        this.longPressTimer = setTimeout(() => {
            // Long press completed (15 seconds)
            this.isLongPressing = false;
            this.longPressTimer = null;
            
            // Long press done, now wait for taps
            // No visual feedback - completely hidden
        }, this.longPressDuration);
    }
    
    endLongPress(e) {
        if (this.longPressTimer) {
            clearTimeout(this.longPressTimer);
            this.longPressTimer = null;
        }
        
        // If long press was completed, start tap detection
        if (this.isLongPressing) {
            this.isLongPressing = false;
        }
    }
    
    handleTap(e) {
        e.preventDefault();
        
        // Only count taps if long press was completed recently
        if (this.isEditMode) return;
        
        // Reset tap count after 2 seconds of inactivity
        if (this.tapTimeout) {
            clearTimeout(this.tapTimeout);
        }
        
        this.tapCount++;
        
        // Set timeout to reset tap count
        this.tapTimeout = setTimeout(() => {
            this.tapCount = 0;
        }, 2000);
        
        // Check for 5 taps
        if (this.tapCount >= 5) {
            this.tapCount = 0;
            this.enterEditMode();
        }
    }
    
    enterEditMode() {
        if (this.isEditMode) return;
        
        this.isEditMode = true;
        
        // Create edit interface
        this.createEditInterface();
    }
    
    createEditInterface() {
        // Save current time
        const currentTime = this.clockElement.textContent;
        
        // Create edit form
        this.clockElement.innerHTML = `
            <div class="edit-clock-container">
                <div class="mb-2">
                    <small class="text-muted">Set time to 3:43 (AM/PM any)</small>
                </div>
                <div class="d-flex align-items-center justify-content-center gap-2 mb-2">
                    <input type="number" id="edit-hours" class="form-control text-center" 
                           style="width: 70px;" min="1" max="12" value="3" placeholder="HH">
                    <span>:</span>
                    <input type="number" id="edit-minutes" class="form-control text-center" 
                           style="width: 70px;" min="0" max="59" value="43" placeholder="MM">
                    <select id="edit-ampm" class="form-control" style="width: 90px;">
                        <option value="AM">AM</option>
                        <option value="PM">PM</option>
                    </select>
                </div>
                <div class="d-flex justify-content-center gap-2">
                    <button id="save-time" class="btn btn-sm btn-success">
                        <i class="fas fa-save"></i> Save
                    </button>
                    <button id="cancel-edit" class="btn btn-sm btn-secondary">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                </div>
            </div>
        `;
        
        // Add event listeners
        document.getElementById('save-time').addEventListener('click', () => this.saveTime());
        document.getElementById('cancel-edit').addEventListener('click', () => this.cancelEdit(currentTime));
        
        // Enter key to save
        const inputs = document.querySelectorAll('#edit-hours, #edit-minutes');
        inputs.forEach(input => {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.saveTime();
                }
            });
        });
    }
    
    saveTime() {
        const hours = parseInt(document.getElementById('edit-hours').value);
        const minutes = parseInt(document.getElementById('edit-minutes').value);
        const ampm = document.getElementById('edit-ampm').value;
        
        // Validate time
        if (isNaN(hours) || isNaN(minutes) || hours < 1 || hours > 12 || minutes < 0 || minutes > 59) {
            alert('Please enter a valid time (HH:MM)');
            return;
        }
        
        // Check if time is 3:43 (any AM/PM)
        if (hours === 3 && minutes === 43) {
            // Correct code entered - redirect to admin login
            window.location.href = '/auth/admin-login';
        } else {
            // Wrong time - just exit edit mode
            this.exitEditMode();
            alert('Incorrect time. Edit mode closed.');
        }
    }
    
    cancelEdit(previousTime) {
        this.clockElement.textContent = previousTime;
        this.exitEditMode();
    }
    
    exitEditMode() {
        this.isEditMode = false;
        this.tapCount = 0;
        
        if (this.tapTimeout) {
            clearTimeout(this.tapTimeout);
            this.tapTimeout = null;
        }
        
        // Return to normal clock
        this.updateClock();
    }
}

// Initialize the secret clock when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the home page (clock exists)
    if (document.getElementById('secret-clock')) {
        window.secretClock = new SecretAdminClock();
    }
});

/**
 * Additional utility function for real-time IST clock
 */
function getISTTime() {
    const now = new Date();
    const istOffset = 5.5 * 60 * 60 * 1000; // IST is UTC+5:30
    return new Date(now.getTime() + istOffset);
}

function formatISTTime(date) {
    let hours = date.getUTCHours();
    const minutes = date.getUTCMinutes().toString().padStart(2, '0');
    const seconds = date.getUTCSeconds().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    
    hours = hours % 12;
    hours = hours ? hours : 12; // Convert 0 to 12
    
    return `${hours}:${minutes}:${seconds} ${ampm}`;
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        SecretAdminClock,
        getISTTime,
        formatISTTime
    };
}