/**
 * Simple API client for the Email CRM
 */
const API = {
    /**
     * Base URL for API calls
     */
    baseUrl: '',  // Empty string since our endpoints are already absolute

    /**
     * Get the stored token - check cookies first, then localStorage as fallback
     */
    getToken() {
        // Try to get from cookie first
        const token = this.getCookie('access_token');
        if (token) return token;
        
        // Fall back to localStorage
        return localStorage.getItem('token');
    },

    /**
     * Set the token in local storage
     */
    setToken(token) {
        localStorage.setItem('token', token);
    },

    /**
     * Clear the token (for logout)
     */
    clearToken() {
        localStorage.removeItem('token');
        // Also clear cookies by setting expiration in the past
        document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    },

    /**
     * Make an API request with proper headers
     */
    async request(endpoint, options = {}) {
        const url = endpoint.startsWith('/') ? endpoint : this.baseUrl + endpoint;
        
        // Set default headers
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        // Add auth token if available
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        // Add CSRF token from cookie if available
        const csrftoken = this.getCookie('csrftoken');
        if (csrftoken) {
            headers['X-CSRFToken'] = csrftoken;
        }
        
        try {
            console.log(`Making API request to: ${url}`);
            const response = await fetch(url, {
                ...options,
                headers,
                credentials: 'include'  // Include cookies in the request
            });
            
            // Handle 401 Unauthorized (token expired)
            if (response.status === 401) {
                console.error('Authentication failed (401). Redirecting to login.');
                this.clearToken();
                window.location.href = '/accounts/login/';
                return null;
            }
            
            // Handle other error statuses
            if (!response.ok) {
                console.error(`API error: ${response.status} ${response.statusText}`);
                const errorData = await response.json().catch(() => ({}));
                return { response, data: errorData, error: true };
            }
            
            // Parse JSON response
            const data = await response.json().catch(() => ({}));
            
            // Return both response and data
            return { response, data };
            
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },

    /**
     * Get CSRF token from cookie
     */
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },

    /**
     * Auth methods
     */
    auth: {
        async login(username, password, csrfToken) {
            const headers = {};
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken;
            }
            
            const { response, data } = await API.request('/api/token/', {
                method: 'POST',
                headers,
                body: JSON.stringify({ username, password })
            });
            
            if (response.ok) {
                API.setToken(data.access);
                localStorage.setItem('refresh_token', data.refresh);
            }
            
            return { success: response.ok, data };
        },
        
        async register(userData) {
            const headers = {};
            if (userData.csrfmiddlewaretoken) {
                headers['X-CSRFToken'] = userData.csrfmiddlewaretoken;
                delete userData.csrfmiddlewaretoken;
            }
            
            return await API.request('/accounts/register/', {
                method: 'POST',
                headers,
                body: JSON.stringify(userData)
            });
        },
        
        logout() {
            API.clearToken();
            localStorage.removeItem('refresh_token');
            window.location.href = '/';
        }
    },

    /**
     * Contacts methods
     */
    contacts: {
        async getAll() {
            return await API.request('/contacts/');
        },
        
        async get(id) {
            return await API.request(`/contacts/${id}/`);
        },
        
        async create(contactData) {
            return await API.request('/contacts/', {
                method: 'POST',
                body: JSON.stringify(contactData)
            });
        },
        
        async update(id, contactData) {
            return await API.request(`/contacts/${id}/`, {
                method: 'PUT',
                body: JSON.stringify(contactData)
            });
        },
        
        async delete(id) {
            return await API.request(`/contacts/${id}/`, {
                method: 'DELETE'
            });
        },
        
        async search(query) {
            return await API.request(`/contacts/search/?q=${encodeURIComponent(query)}`);
        }
    },

    /**
     * Email template methods
     */
    emailTemplates: {
        async getAll() {
            return await API.request('/emails/templates/');
        },
        
        async get(id) {
            return await API.request(`/emails/templates/${id}/`);
        },
        
        async create(templateData) {
            return await API.request('/emails/templates/', {
                method: 'POST',
                body: JSON.stringify(templateData)
            });
        },
        
        async update(id, templateData) {
            return await API.request(`/emails/templates/${id}/`, {
                method: 'PUT',
                body: JSON.stringify(templateData)
            });
        },
        
        async delete(id) {
            return await API.request(`/emails/templates/${id}/`, {
                method: 'DELETE'
            });
        }
    },

    /**
     * Email sending methods
     */
    emails: {
        async send(contactId, emailData) {
            return await API.request(`/emails/send/${contactId}/`, {
                method: 'POST',
                body: JSON.stringify(emailData)
            });
        },
        
        async bulkSend(contactIds, templateId) {
            return await API.request('/emails/bulk-send/', {
                method: 'POST',
                body: JSON.stringify({ contact_ids: contactIds, template_id: templateId })
            });
        },
        
        async getAnalytics() {
            return await API.request('/emails/analytics/');
        }
    },

    /**
     * Dashboard methods
     */
    dashboard: {
        async getSummary() {
            return await API.request('/dashboard/data/');
        },
        
        async getStats() {
            return await API.request('/dashboard/stats/');
        },
        
        async getRecentActivities() {
            return await API.request('/dashboard/recent-activities/');
        }
    }
};

// Export for use in other files
window.API = API; 