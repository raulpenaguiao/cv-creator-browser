/**
 * Fetch wrapper with CSRF token and error handling.
 */
const Api = {
    getCSRFToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    },

    async request(url, options = {}) {
        const defaults = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
            },
            credentials: 'same-origin',
        };

        if (options.body instanceof FormData) {
            defaults.headers = { 'X-CSRFToken': this.getCSRFToken() };
        }

        const config = { ...defaults, ...options };
        if (options.headers) {
            config.headers = { ...defaults.headers, ...options.headers };
        }

        const response = await fetch(url, config);

        if (response.status === 401) {
            Alpine.store('auth').authenticated = false;
            Alpine.store('auth').showLogin = true;
            throw new Error('Unauthorized');
        }

        return response;
    },

    async get(url) {
        return this.request(url, { method: 'GET' });
    },

    async post(url, data) {
        const options = { method: 'POST' };
        if (data instanceof FormData) {
            options.body = data;
        } else {
            options.body = JSON.stringify(data);
        }
        return this.request(url, options);
    },

    async put(url, data) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    },
};
