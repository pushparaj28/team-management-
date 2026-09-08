document.addEventListener('DOMContentLoaded', function () {

    // ================= 1. LOGIN FORM HANDLER =================
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const approvalBanner = document.getElementById('approvalBanner');
            const approvalBannerText = document.getElementById('approvalBannerText');
            const errorBanner = document.getElementById('errorBanner');
            const errorBannerText = document.getElementById('errorBannerText');
            const submitBtn = document.getElementById('submitBtn') || this.querySelector('button[type="submit"]');

            // Purane banners hide karein
            if (approvalBanner) approvalBanner.classList.add('hidden');
            if (errorBanner) errorBanner.classList.add('hidden');

            // Button loading state
            let originalBtnText = '';
            if (submitBtn) {
                originalBtnText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = `<i class="fas fa-spinner fa-spin mr-1"></i> Checking...`;
            }

            const formData = new FormData(this);
            const postData = {
                username: formData.get('username'),
                password: formData.get('password'),
            };

            const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
            const csrfToken = csrfTokenElement ? csrfTokenElement.value : formData.get('csrfmiddlewaretoken');
            const targetUrl = this.getAttribute('data-url') || this.action || window.location.href;

            try {
                const response = await fetch(targetUrl, {
                    method: 'POST',
                    body: JSON.stringify(postData),
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrfToken
                    }
                });

                const data = await response.json();

                // 🟡 Case 1: Account Pending Admin Approval (Status 403)
                if (response.status === 403 && data.status === 'pending') {
                    if (approvalBannerText && approvalBanner) {
                        approvalBannerText.textContent = data.message;
                        approvalBanner.classList.remove('hidden');
                    }
                } 
                // 🟢 Case 2: Login Success
                else if (response.ok && data.status === 'success') {
                    window.location.href = data.redirect_url || '/tasks/';
                    return;
                } 
                // 🔴 Case 3: Invalid Credentials (Status 400 ya custom error)
                else {
                    if (errorBannerText && errorBanner) {
                        errorBannerText.textContent = data.message || 'Invalid username or password.';
                        errorBanner.classList.remove('hidden');
                    }
                }
            } catch (err) {
                console.error('Login Error:', err);
                if (errorBannerText && errorBanner) {
                    errorBannerText.textContent = 'Server se connect nahi ho pa rahe hain. Kripya dubara koshish karein.';
                    errorBanner.classList.remove('hidden');
                }
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnText;
                }
            }
        });
    }

    // ================= 2. REGISTER FORM HANDLER =================
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const formData = new FormData(this);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
            const url = this.getAttribute('data-url') || this.action || window.location.href;

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    window.location.href = data.redirect_url || '/accounts/login/';
                } else {
                    if (data.message) {
                        alert(data.message);
                    } else if (data.errors) {
                        console.log('Validation Errors:', data.errors);
                        alert('Kripya form ki details check karke sahi fill karein.');
                    }
                }
            })
            .catch(error => {
                console.error('Register Error:', error);
            });
        });
    }
});

// ================= 3. GLOBAL PASSWORD TOGGLE =================
window.togglePassword = function () {
    const passwordInput = document.getElementById('id_password');
    const eyeIcon = document.getElementById('eye-icon');

    if (passwordInput && eyeIcon) {
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            eyeIcon.innerHTML = `
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l18 18"></path>
            `;
        } else {
            passwordInput.type = 'password';
            eyeIcon.innerHTML = `
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
            `;
        }
    }
};