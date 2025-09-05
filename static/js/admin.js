// static/js/admin.js

// static/js/auth.js
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (validateLoginForm()) {
                const formData = new FormData(this);
                const data = Object.fromEntries(formData.entries());
                
                try {
                    const response = await fetch('/api/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        // Store token in localStorage
                        localStorage.setItem('admin_token', result.access_token);
                        localStorage.setItem('admin_user', JSON.stringify(result.user));
                        
                        // Redirect to admin dashboard
                        window.location.href = '/admin/dashboard';
                    } else {
                        alert('Login failed: ' + result.message);
                    }
                } catch (error) {
                    alert('Login error: ' + error.message);
                }
            }
        });
    }
});

// Keep your validation functions the same...
function validateLoginForm() {
    let isValid = true;
    const email = document.getElementById('email');
    const password = document.getElementById('password');

    resetErrors();

    if (!email.value.trim()) {
        showError('email', 'Email is required');
        isValid = false;
    } else if (!isValidEmail(email.value)) {
        showError('email', 'Please enter a valid email');
        isValid = false;
    }

    if (!password.value.trim()) {
        showError('password', 'Password is required');
        isValid = false;
    }

    return isValid;
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function showError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const errorElement = document.getElementById(fieldId + '-error');
    
    field.parentElement.classList.add('error');
    errorElement.textContent = message;
    errorElement.style.display = 'block';
}

function resetErrors() {
    const errorElements = document.querySelectorAll('.error-message');
    errorElements.forEach(el => {
        el.style.display = 'none';
    });

    const formGroups = document.querySelectorAll('.form-group');
    formGroups.forEach(group => {
        group.classList.remove('error');
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    const token = localStorage.getItem('admin_token');
    if (!token) {
        window.location.href = '/admin/login';
        return;
    }

    loadBlogPosts();
    setupBlogForm();
});

function setupBlogForm() {
    const form = document.getElementById('blog-form');
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const data = Object.fromEntries(formData.entries());
        
        try {
            const token = localStorage.getItem('admin_token');
            const response = await fetch('/api/admin/blog', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert('Blog post published successfully!');
                form.reset();
                loadBlogPosts();
            } else {
                alert('Error: ' + result.message);
            }
        } catch (error) {
            alert('Error publishing blog post');
        }
    });
}

async function loadBlogPosts() {
    try {
        const token = localStorage.getItem('admin_token');
        const response = await fetch('/api/admin/blogs', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const blogs = await response.json();
        const container = document.getElementById('blog-posts-list');
        
        if (blogs.length === 0) {
            container.innerHTML = '<p>No blog posts yet.</p>';
            return;
        }
        
        container.innerHTML = blogs.map(blog => `
            <div class="blog-item">
                <h3>${blog.title}</h3>
                <p>Slug: ${blog.slug}</p>
                <p>Created: ${new Date(blog.created_at).toLocaleDateString()}</p>
                <button onclick="deleteBlog('${blog._id}')">Delete</button>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading blogs:', error);
    }
}