document.addEventListener('DOMContentLoaded', function () {

    // --- LOGIN FORM LOGIC ---
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const formData = new FormData(this);
            const data = Object.fromEntries(formData.entries());
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            // HTML se URL fetch kar rahe hain
            const url = this.getAttribute('data-url');

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    window.location.href = data.redirect_url;
                } else {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert("Something went wrong. Please try again.");
            });
        });
    }

    // --- REGISTER FORM LOGIC ---
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault(); 
            
            const formData = new FormData(this);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            // HTML se URL fetch kar rahe hain
            const url = this.getAttribute('data-url');

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData 
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert(data.message);
                    window.location.href = data.redirect_url;
                } else {
                    if (data.message) {
                        alert(data.message);
                    } else if (data.errors) {
                        alert("Please correct the errors in the form.");
                        console.log(data.errors);
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert("Something went wrong. Please try again.");
            });
        });
    }
});

// --- TOGGLE PASSWORD LOGIC ---
window.togglePassword = function() {
    const passwordInput = document.getElementById('id_password');
    const eyeIcon = document.getElementById('eye-icon');
    
    if (passwordInput && eyeIcon) {
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            eyeIcon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.542-7a9.978 9.978 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l18 18"></path>`;
        } else {
            passwordInput.type = 'password';
            eyeIcon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943-9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>`;
        }
    }
};