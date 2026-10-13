document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const toggleButton = document.querySelector('.sidebar-toggle');

    function enhanceSelect(select, index) {
        const wrapper = document.createElement('div');
        wrapper.className = 'admin-select-wrap';
        select.parentNode.insertBefore(wrapper, select);
        wrapper.append(select);

        const trigger = document.createElement('button');
        trigger.className = 'admin-select-trigger';
        trigger.type = 'button';
        trigger.id = `admin-select-trigger-${index}`;
        trigger.setAttribute('role', 'combobox');
        trigger.setAttribute('aria-haspopup', 'listbox');
        trigger.setAttribute('aria-expanded', 'false');
        trigger.setAttribute('aria-controls', `admin-select-list-${index}`);
        trigger.setAttribute('aria-label', Array.from(select.labels || [])
            .map((label) => label.textContent.trim())
            .filter(Boolean)
            .join(' ') || select.getAttribute('aria-label') || select.name);
        trigger.setAttribute('aria-required', String(select.required));
        trigger.disabled = select.disabled;

        const value = document.createElement('span');
        value.className = 'admin-select-value';
        const arrow = document.createElement('span');
        arrow.className = 'admin-select-arrow';
        arrow.setAttribute('aria-hidden', 'true');
        trigger.append(value, arrow);

        const listbox = document.createElement('div');
        listbox.className = 'admin-select-list';
        listbox.id = `admin-select-list-${index}`;
        listbox.setAttribute('role', 'listbox');
        listbox.setAttribute('aria-label', trigger.getAttribute('aria-label'));

        const options = Array.from(select.options).map((option, optionIndex) => {
            const item = document.createElement('div');
            item.className = 'admin-select-option';
            item.id = `admin-select-option-${index}-${optionIndex}`;
            item.setAttribute('role', 'option');
            item.dataset.value = option.value;
            item.textContent = option.textContent;
            item.setAttribute('aria-disabled', String(option.disabled));
            if (option.disabled) item.classList.add('is-disabled');
            listbox.append(item);
            return item;
        });

        const originalRequired = select.required;
        select.required = false;
        select.tabIndex = -1;
        select.setAttribute('aria-hidden', 'true');
        select.classList.add('admin-select-native');
        wrapper.append(trigger);
        document.body.append(listbox);
        Array.from(select.labels || []).forEach((label) => {
            label.htmlFor = trigger.id;
        });

        let activeIndex = -1;

        function syncValue() {
            const selectedIndex = select.selectedIndex;
            value.textContent = selectedIndex >= 0
                ? select.options[selectedIndex].textContent
                : '';
            options.forEach((option, optionIndex) => {
                const selected = optionIndex === selectedIndex;
                option.setAttribute('aria-selected', String(selected));
                if (selected) activeIndex = optionIndex;
            });
            trigger.disabled = select.disabled;
            trigger.setAttribute('aria-invalid', String(trigger.dataset.invalid === 'true'));
        }

        function openList() {
            if (trigger.disabled) return;
            wrapper.classList.add('is-open');
            listbox.classList.add('is-visible');
            trigger.setAttribute('aria-expanded', 'true');
            if (activeIndex < 0 || options[activeIndex].getAttribute('aria-disabled') === 'true') {
                activeIndex = options.findIndex((option) => option.getAttribute('aria-disabled') !== 'true');
            }
            positionListbox();
            syncActiveOption();
        }

        function closeList() {
            wrapper.classList.remove('is-open');
            listbox.classList.remove('is-visible');
            trigger.setAttribute('aria-expanded', 'false');
            trigger.removeAttribute('aria-activedescendant');
        }

        function positionListbox() {
            const rect = trigger.getBoundingClientRect();
            const maxHeight = Math.min(256, window.innerHeight * 0.45);
            const menuHeight = Math.min(options.length * 42 + 8, maxHeight);
            const openAbove = window.innerHeight - rect.bottom < menuHeight + 8
                && rect.top > menuHeight + 8;
            const top = openAbove
                ? rect.top - menuHeight - 6
                : Math.min(rect.bottom + 6, window.innerHeight - menuHeight - 8);
            const width = Math.min(rect.width, window.innerWidth - 16);
            const left = Math.max(8, Math.min(rect.left, window.innerWidth - width - 8));

            listbox.style.top = `${top}px`;
            listbox.style.left = `${left}px`;
            listbox.style.width = `${width}px`;
            listbox.style.maxHeight = `${maxHeight}px`;
        }

        function syncActiveOption() {
            if (activeIndex < 0 || !options[activeIndex]) return;
            trigger.setAttribute('aria-activedescendant', options[activeIndex].id);
            options[activeIndex].scrollIntoView({ block: 'nearest' });
        }

        function moveActive(direction) {
            const step = direction > 0 ? 1 : -1;
            let nextIndex = activeIndex;
            do {
                nextIndex += step;
            } while (
                nextIndex >= 0
                && nextIndex < options.length
                && options[nextIndex].getAttribute('aria-disabled') === 'true'
            );
            if (nextIndex >= 0 && nextIndex < options.length) {
                activeIndex = nextIndex;
                syncActiveOption();
            }
        }

        function chooseOption(option) {
            if (!option || option.getAttribute('aria-disabled') === 'true') return;
            select.value = option.dataset.value;
            trigger.dataset.invalid = 'false';
            select.dispatchEvent(new Event('change', { bubbles: true }));
            syncValue();
            closeList();
        }

        trigger.addEventListener('click', () => {
            if (trigger.getAttribute('aria-expanded') === 'true') closeList();
            else openList();
        });

        trigger.addEventListener('keydown', (event) => {
            if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                event.preventDefault();
                if (trigger.getAttribute('aria-expanded') !== 'true') {
                    openList();
                } else {
                    moveActive(event.key === 'ArrowDown' ? 1 : -1);
                }
            } else if (event.key === 'Home' || event.key === 'End') {
                event.preventDefault();
                openList();
                if (event.key === 'Home') {
                    activeIndex = options.findIndex((option) => option.getAttribute('aria-disabled') !== 'true');
                } else {
                    activeIndex = options.reduce((lastEnabled, option, optionIndex) =>
                        option.getAttribute('aria-disabled') === 'true' ? lastEnabled : optionIndex, -1);
                }
                syncActiveOption();
            } else if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                if (trigger.getAttribute('aria-expanded') !== 'true') {
                    openList();
                } else {
                    chooseOption(options[activeIndex]);
                }
            } else if (event.key === 'Escape') {
                closeList();
            } else if (event.key === 'Tab') {
                closeList();
            }
        });

        listbox.addEventListener('click', (event) => {
            const option = event.target.closest('.admin-select-option');
            chooseOption(option);
            trigger.focus();
        });

        select.addEventListener('change', () => {
            trigger.dataset.invalid = 'false';
            syncValue();
        });

        const form = select.closest('form');
        if (form) {
            form.addEventListener('submit', (event) => {
                if (originalRequired && !select.value) {
                    event.preventDefault();
                    trigger.dataset.invalid = 'true';
                    syncValue();
                    trigger.focus();
                    openList();
                }
            });
            form.addEventListener('reset', () => {
                window.setTimeout(syncValue, 0);
            });
        }

        document.addEventListener('click', (event) => {
            if (!wrapper.contains(event.target) && !listbox.contains(event.target)) closeList();
        });

        window.addEventListener('resize', () => {
            if (wrapper.classList.contains('is-open')) positionListbox();
        });
        window.addEventListener('scroll', () => {
            if (wrapper.classList.contains('is-open')) positionListbox();
        }, true);

        syncValue();
    }

    document.querySelectorAll('select').forEach(enhanceSelect);

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
