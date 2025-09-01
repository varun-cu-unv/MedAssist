// Enhanced Typewriter Effect for Multiple Elements
class TypeWriter {
    constructor(element, text, speed = 50) {
        this.element = element;
        this.text = text;
        this.speed = speed;
        this.index = 0;
    }

    start() {
        return new Promise((resolve) => {
            this.type(resolve);
        });
    }

    type(resolve) {
        if (this.index < this.text.length) {
            this.element.innerHTML += this.text.charAt(this.index);
            this.index++;
            setTimeout(() => this.type(resolve), this.speed);
        } else {
            resolve();
        }
    }
}

// Sequential typewriter effect for multiple elements
async function startSequentialTyping() {
    const elements = [
        {
            id: 'mainTagline',
            text: 'Your health, your assistant.',
            speed: 10
        },
        {
            id: 'description1',
            text: 'Experience the future of healthcare with AI-powered assistance. Your personal health companion is here to help you manage your wellness journey with intelligent insights and personalized care.',
            speed: 30
        },
        {
            id: 'feature1',
            text: 'AI-Powered Insights - Get personalized health recommendations',
            speed: 40
        },
        {
            id: 'feature2',
            text: 'Multilingual support to access health information in your preferred language',
            speed: 40
        },
        {
            id: 'feature3',
            text: 'Book an appointment with a healthcare professional',
            speed: 40
        },
        {
            id: 'feature4',
            text: 'Voice mode - Interact with your health assistant using voice commands',
            speed: 40
        }
    ];

    // Start typing each element sequentially
    for (const item of elements) {
        const element = document.getElementById(item.id);
        if (element) {
            const typewriter = new TypeWriter(element, item.text, item.speed);
            await typewriter.start();
            // Small delay between each text
            await new Promise(resolve => setTimeout(resolve, 300));
        }
    }
}

// Initialize typing animation on page load
window.addEventListener('load', function() {
    // Start the sequential typing after a short delay
    setTimeout(startSequentialTyping, 500);
});

// Theme toggle functionality
function toggleTheme() {
    const body = document.body;
    const themeBtn = document.querySelector('.theme-toggle');

    body.classList.toggle('light-mode');

    if (body.classList.contains('light-mode')) {
        themeBtn.textContent = '☀️';
        localStorage.setItem('theme', 'light');
    } else {
        themeBtn.textContent = '🌙';
        localStorage.setItem('theme', 'dark');
    }
}

// Load saved theme on page load
window.addEventListener('load', function() {
    const savedTheme = localStorage.getItem('theme');
    const body = document.body;
    const themeBtn = document.querySelector('.theme-toggle');

    if (savedTheme === 'light') {
        body.classList.add('light-mode');
        themeBtn.textContent = '☀️';
    }
});

// Form switching functionality
function showForm(formType) {
    const tabs = document.querySelectorAll('.tab');
    const forms = document.querySelectorAll('.form');

    // Remove active class from all tabs and forms
    tabs.forEach(tab => tab.classList.remove('active'));
    forms.forEach(form => form.classList.remove('active'));

    // Add active class to selected tab and form
    if (formType === 'signin') {
        tabs[0].classList.add('active');
        document.getElementById('signinForm').classList.add('active');
    } else {
        tabs[1].classList.add('active');
        document.getElementById('signupForm').classList.add('active');
    }

    // Clear any error messages
    hideMessages();
}

// Message handling functions
function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    document.getElementById('successMessage').style.display = 'none';
}

function showSuccess(message) {
    const successDiv = document.getElementById('successMessage');
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    document.getElementById('errorMessage').style.display = 'none';
}

function hideMessages() {
    document.getElementById('errorMessage').style.display = 'none';
    document.getElementById('successMessage').style.display = 'none';
}

// Form validation
function validateForm(formType) {
    const form = document.getElementById(formType + 'Form');
    const inputs = form.querySelectorAll('input[required]');

    for (let input of inputs) {
        if (!input.value.trim()) {
            showError('Please fill in all required fields.');
            return false;
        }
    }

    if (formType === 'signup') {
        const email = document.getElementById('signup-email').value;
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            showError('Please enter a valid email address.');
            return false;
        }

        const password = document.getElementById('signup-password').value;
        if (password.length < 6) {
            showError('Password must be at least 6 characters long.');
            return false;
        }
    }

    return true;
}

// Add form submission handlers
document.addEventListener('DOMContentLoaded', function() {
    const signinForm = document.getElementById('signinForm');
    const signupForm = document.getElementById('signupForm');

    if (signinForm) {
        signinForm.addEventListener('submit', function(e) {
            if (!validateForm('signin')) {
                e.preventDefault();
            }
        });
    }

    if (signupForm) {
        signupForm.addEventListener('submit', function(e) {
            if (!validateForm('signup')) {
                e.preventDefault();
            }
        });
    }
});

// Handle URL parameters for error/success messages
window.addEventListener('load', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    const success = urlParams.get('success');

    if (error) {
        showError(decodeURIComponent(error));
    }
    if (success) {
        showSuccess(decodeURIComponent(success));
    }
});

// Add smooth scroll behavior for better UX
document.documentElement.style.scrollBehavior = 'smooth';

// Add loading animation for form submissions
function addLoadingState(button) {
    const originalText = button.textContent;
    button.textContent = 'Loading...';
    button.disabled = true;

    setTimeout(() => {
        button.textContent = originalText;
        button.disabled = false;
    }, 2000);
}