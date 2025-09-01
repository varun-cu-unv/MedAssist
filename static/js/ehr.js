// Theme toggle functionality
function toggleTheme() {
    const body = document.body;
    const themeBtn = document.querySelector('.theme-toggle');

    if (!body || !themeBtn) return;

    body.classList.toggle('light-mode');

    if (body.classList.contains('light-mode')) {
        themeBtn.textContent = '☀️';
        localStorage.setItem('theme', 'light');
    } else {
        themeBtn.textContent = '🌙';
        localStorage.setItem('theme', 'dark');
    }
}

// Load saved theme
function loadSavedTheme() {
    const savedTheme = localStorage.getItem('theme');
    const body = document.body;
    const themeBtn = document.querySelector('.theme-toggle');

    if (!body || !themeBtn) return;

    if (savedTheme === 'light') {
        body.classList.add('light-mode');
        themeBtn.textContent = '☀️';
    } else {
        themeBtn.textContent = '🌙';
    }
}

// Toggle add record form
function toggleAddForm() {
    const form = document.getElementById('addRecordForm');
    if (form) {
        form.style.display = form.style.display === 'none' ? 'block' : 'none';
        
        // Set today's date as default
        if (form.style.display === 'block') {
            const dateInput = document.getElementById('date_recorded');
            if (dateInput) {
                dateInput.value = new Date().toISOString().split('T')[0];
            }
        }
    }
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    const requiredFields = form.querySelectorAll('[required]');
    
    for (let field of requiredFields) {
        if (!field.value.trim()) {
            alert(`Please fill in the ${field.previousElementSibling.textContent} field.`);
            field.focus();
            return false;
        }
    }
    
    return true;
}

// Logout functionality
function confirmLogout() {
    if (confirm('Are you sure you want to logout?')) {
        document.getElementById('logoutForm').submit();
    }
}

// Handle URL parameters for success/error messages
function handleURLMessages() {
    const urlParams = new URLSearchParams(window.location.search);
    const success = urlParams.get('success');
    const error = urlParams.get('error');
    
    if (success) {
        showMessage(decodeURIComponent(success), 'success');
    }
    if (error) {
        showMessage(decodeURIComponent(error), 'error');
    }
}

// Show message notifications
function showMessage(message, type) {
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        padding: 15px 25px;
        border-radius: 10px;
        font-weight: 600;
        z-index: 1001;
        max-width: 400px;
        text-align: center;
        animation: slideDown 0.3s ease;
    `;
    
    if (type === 'success') {
        messageDiv.style.background = 'linear-gradient(135deg, #10B981, #34D399)';
        messageDiv.style.color = 'white';
    } else {
        messageDiv.style.background = 'linear-gradient(135deg, #EF4444, #F87171)';
        messageDiv.style.color = 'white';
    }
    
    messageDiv.textContent = message;
    document.body.appendChild(messageDiv);
    
    // Remove message after 4 seconds
    setTimeout(() => {
        messageDiv.style.animation = 'slideUp 0.3s ease';
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 300);
    }, 4000);
}

// Add CSS animations for messages
function addMessageStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideDown {
            from { transform: translateX(-50%) translateY(-100%); opacity: 0; }
            to { transform: translateX(-50%) translateY(0); opacity: 1; }
        }
        
        @keyframes slideUp {
            from { transform: translateX(-50%) translateY(0); opacity: 1; }
            to { transform: translateX(-50%) translateY(-100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
}

// Auto-fill current date for new forms
function setCurrentDate() {
    const today = new Date().toISOString().split('T')[0];
    const dateInputs = document.querySelectorAll('input[type="date"]');
    
    dateInputs.forEach(input => {
        if (!input.value) {
            input.value = today;
        }
    });
}

// Initialize page
function initializePage() {
    loadSavedTheme();
    handleURLMessages();
    addMessageStyles();
    setCurrentDate();
    
    // Add smooth scroll behavior
    if (document.documentElement) {
        document.documentElement.style.scrollBehavior = 'smooth';
    }
    
    // Add form validation on submit
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this.id)) {
                e.preventDefault();
            }
        });
    });
}

// Confirm and delete medical record
function confirmDelete(recordId) {
    if (confirm('Are you sure you want to delete this medical record? This action cannot be undone.')) {
        // Create a form and submit it
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/delete-medical-record/${recordId}`;
        document.body.appendChild(form);
        form.submit();
    }
}

// Make the function globally available
window.confirmDelete = confirmDelete;

// Global functions
window.toggleTheme = toggleTheme;
window.toggleAddForm = toggleAddForm;
window.confirmLogout = confirmLogout;

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', initializePage);