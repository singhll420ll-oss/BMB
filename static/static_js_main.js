/**
 * Main JavaScript file for Bite Me Buddy
 */

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Form validation
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Cart quantity controls
    document.querySelectorAll('.quantity-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var input = this.parentNode.querySelector('input[type=number]');
            if (this.classList.contains('minus')) {
                input.stepDown();
            } else {
                input.stepUp();
            }
            input.dispatchEvent(new Event('change'));
        });
    });
    
    // Image preview for file inputs
    document.querySelectorAll('input[type="file"][accept^="image"]').forEach(function(input) {
        input.addEventListener('change', function() {
            var preview = document.getElementById(this.dataset.preview);
            if (preview && this.files && this.files[0]) {
                var reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    });
    
    // Search functionality
    var searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            var searchTerm = this.value.toLowerCase();
            var items = document.querySelectorAll(this.dataset.target);
            
            items.forEach(function(item) {
                var text = item.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });
    
    // Confirm before delete
    document.querySelectorAll('[data-confirm]').forEach(function(element) {
        element.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });
});

// Utility Functions
function formatCurrency(amount) {
    return '₹' + parseFloat(amount).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    var toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast
    var toastId = 'toast-' + Date.now();
    var toast = document.createElement('div');
    toast.id = toastId;
    toast.className = 'toast align-items-center text-bg-' + type + ' border-0';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Show toast
    var bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// HTMX Event Handlers
document.addEventListener('htmx:beforeRequest', function(event) {
    // Show loading indicator
    var target = event.detail.target;
    if (target) {
        target.classList.add('loading');
    }
});

document.addEventListener('htmx:afterRequest', function(event) {
    // Hide loading indicator
    var target = event.detail.target;
    if (target) {
        target.classList.remove('loading');
    }
});

document.addEventListener('htmx:responseError', function(event) {
    // Show error message
    var detail = event.detail;
    showToast('Error: ' + (detail.xhr.statusText || 'Request failed'), 'danger');
});

// Session Timer
class SessionTimer {
    constructor(timeoutMinutes = 25) {
        this.timeout = timeoutMinutes * 60 * 1000; // Convert to milliseconds
        this.warningTime = 5 * 60 * 1000; // 5 minutes warning
        this.timer = null;
        this.warningTimer = null;
        this.startTime = Date.now();
        
        this.setupEvents();
        this.start();
    }
    
    setupEvents() {
        // Reset timer on user activity
        ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, () => this.reset());
        });
    }
    
    start() {
        this.startTime = Date.now();
        
        // Set warning timer
        this.warningTimer = setTimeout(() => {
            this.showWarning();
        }, this.timeout - this.warningTime);
        
        // Set logout timer
        this.timer = setTimeout(() => {
            this.logout();
        }, this.timeout);
    }
    
    reset() {
        clearTimeout(this.warningTimer);
        clearTimeout(this.timer);
        this.start();
    }
    
    showWarning() {
        if (confirm('Your session will expire in 5 minutes due to inactivity. Do you want to continue?')) {
            this.reset();
        }
    }
    
    logout() {
        window.location.href = '/auth/logout?reason=timeout';
    }
    
    getRemainingTime() {
        const elapsed = Date.now() - this.startTime;
        return Math.max(0, this.timeout - elapsed);
    }
}

// Initialize session timer on pages that need it
if (document.querySelector('[data-enable-session-timer]')) {
    window.sessionTimer = new SessionTimer(25);
}