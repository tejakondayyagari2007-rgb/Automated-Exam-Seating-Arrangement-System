document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.querySelector('[data-sidebar-toggle]');
    const sidebar = document.querySelector('.sidebar');
    if (toggle && sidebar) {
        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });
    }

    const darkModeEnabled = localStorage.getItem('darkMode') === 'true';
    if (darkModeEnabled) {
        document.body.classList.add('dark-mode');
    }

    const userName = document.querySelector('[data-user-name]');
    if (userName) {
        const currentUser = getCurrentUser();
        userName.textContent = currentUser && currentUser.name ? currentUser.name : '';
    }
});

function applyRoleAccess(user) {
    const role = String(user.role || '').toUpperCase();
    const allowedPages = ROLE_PAGE_ACCESS[role] || [];

    document.querySelectorAll('.sidebar nav a').forEach((link) => {
        const path = new URL(link.href, window.location.origin).pathname;
        link.hidden = !allowedPages.includes(path);
        if (role === 'STUDENT') {
            const studentLabels = {
                '/students': 'My Profile',
                '/exams': 'My Exams',
                '/timetable': 'My Timetable',
                '/seating': 'My Seating',
            };
            if (studentLabels[path]) link.textContent = studentLabels[path];
        }
    });
    document.body.classList.add('role-access-ready');

    document.querySelectorAll('[data-admin-only]').forEach((element) => {
        element.hidden = role !== 'ADMIN';
    });
    document.querySelectorAll('[data-role-allow]').forEach((element) => {
        const allowedRoles = element.dataset.roleAllow.split(',').map((allowedRole) => allowedRole.trim());
        element.hidden = !allowedRoles.includes(role);
    });

    const userName = document.querySelector('[data-user-name]');
    if (userName) userName.textContent = user.name || '';

    const heading = document.querySelector('.topbar h2');
    if (role === 'STUDENT' && heading) {
        const studentHeadings = {
            '/dashboard': 'Student Dashboard',
            '/students': 'My Profile',
            '/exams': 'My Exam Details',
            '/timetable': 'My Timetable',
            '/seating': 'My Seating Details',
        };
        if (studentHeadings[window.location.pathname]) {
            heading.textContent = studentHeadings[window.location.pathname];
        }
    }
}

function setTheme(isDark) {
    document.body.classList.toggle('dark-mode', isDark);
    localStorage.setItem('darkMode', String(isDark));
}
