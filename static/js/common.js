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

    const navigation = document.querySelector('.sidebar nav');
    const teacherPages = [
        ['/dashboard', 'Dashboard'],
        ['/exams', 'Assigned Exams'],
        ['/timetable', 'My Timetable'],
        ['/students', 'Assigned Students'],
        ['/attendance', 'Attendance'],
        ['/seating', 'Seating Details'],
        ['/reports', 'Relevant Reports'],
        ['/notifications', 'Notifications'],
    ];

    if (role === 'TEACHER' && navigation) {
        const linksByPath = new Map(
            Array.from(navigation.querySelectorAll('a'))
                .filter((link) => !link.hasAttribute('data-role-logout'))
                .map((link) => [
                    new URL(link.href, window.location.origin).pathname,
                    link,
                ]),
        );
        navigation.replaceChildren();
        teacherPages.forEach(([path, label]) => {
            const link = linksByPath.get(path);
            if (!link) return;
            link.textContent = label;
            link.hidden = false;
            navigation.appendChild(link);
        });

        const logoutLink = document.createElement('a');
        logoutLink.href = '#logout';
        logoutLink.textContent = 'Logout';
        logoutLink.dataset.roleLogout = 'true';
        logoutLink.addEventListener('click', (event) => {
            event.preventDefault();
            if (typeof window.logoutUser === 'function') window.logoutUser();
        });
        navigation.appendChild(logoutLink);
    }

    document.querySelectorAll('.sidebar nav a').forEach((link) => {
        const path = new URL(link.href, window.location.origin).pathname;
        link.hidden = !link.hasAttribute('data-role-logout') && !allowedPages.includes(path);
        if (role === 'STUDENT') {
            const studentLabels = {
                '/students': 'My Profile',
                '/exams': 'My Exams',
                '/timetable': 'My Timetable',
                '/seating': 'My Seating',
                '/notifications': 'My Notifications',
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
    if (!heading) return;

    if (window.location.pathname === '/dashboard') {
        heading.textContent = `${role.charAt(0)}${role.slice(1).toLowerCase()} Dashboard`;
    } else if (role === 'TEACHER') {
        const teacherHeadings = {
            '/students': 'Assigned Students',
            '/exams': 'Assigned Exams',
            '/timetable': 'My Timetable',
            '/seating': 'Seating Details',
            '/attendance': 'Attendance',
            '/reports': 'Relevant Reports',
            '/notifications': 'Notifications',
        };
        if (teacherHeadings[window.location.pathname]) {
            heading.textContent = teacherHeadings[window.location.pathname];
        }
    } else if (role === 'STUDENT') {
        const studentHeadings = {
            '/students': 'My Profile',
            '/exams': 'My Exam Details',
            '/timetable': 'My Timetable',
            '/seating': 'My Seating Details',
            '/notifications': 'My Notifications',
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
