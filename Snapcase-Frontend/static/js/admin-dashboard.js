document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const toggleButton = document.querySelector('.sidebar-toggle');

    if (toggleButton && sidebar) {
        toggleButton.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    const deleteForms = document.querySelectorAll('[data-confirm-delete="true"]');
    deleteForms.forEach((form) => {
        form.addEventListener('submit', (event) => {
            const message = form.dataset.confirmMessage || 'This action cannot be undone. Continue?';
            if (!window.confirm(message)) {
                event.preventDefault();
            }
        });
    });
});
