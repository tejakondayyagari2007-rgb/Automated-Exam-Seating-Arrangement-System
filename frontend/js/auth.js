document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    if (!loginForm) return;

    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const payload = {
            username: document.getElementById('username').value,
            password: document.getElementById('password').value,
            role: document.getElementById('role').value,
        };

        try {
            const result = await apiRequest('/api/auth/login', {
                method: 'POST',
                body: payload,
            });
            if (result.success) {
                sessionStorage.setItem('currentUser', JSON.stringify(result.user));
                window.location.href = '/dashboard';
            } else {
                showToast(result.message || 'Login failed', 'error');
            }
        } catch (error) {
            showToast(error.message, 'error');
        }
    });
});

const ROLE_PAGE_ACCESS = {
    ADMIN: ['/dashboard', '/students', '/teachers', '/rooms', '/subjects', '/exams', '/timetable', '/seating', '/attendance', '/reports', '/notifications', '/settings'],
    TEACHER: ['/dashboard', '/students', '/teachers', '/rooms', '/subjects', '/exams', '/timetable', '/seating', '/attendance', '/reports', '/notifications'],
    STUDENT: ['/dashboard', '/students', '/exams', '/timetable', '/seating', '/notifications'],
};

function getCurrentUser() {
    try {
        return JSON.parse(sessionStorage.getItem('currentUser') || 'null');
    } catch (error) {
        return null;
    }
}

async function checkAuth() {
    try {
        const result = await apiRequest('/api/auth/me');
        if (!result.success || !result.user) {
            window.location.href = '/login';
            return null;
        }
        const user = result.user;
        user.role = String(user.role || '').toUpperCase();
        sessionStorage.setItem('currentUser', JSON.stringify(user));
        if (typeof applyRoleAccess === 'function') applyRoleAccess(user);

        const allowedPages = ROLE_PAGE_ACCESS[user.role] || [];
        if (!allowedPages.includes(window.location.pathname)) {
            window.location.href = '/dashboard';
            return null;
        }
        return user;
    } catch (error) {
        window.location.href = '/login';
        return null;
    }
}
