/**
 * Simple API client for the Email CRM
 */
const API = {
    /**
     * Base URL for API calls
     */
    baseUrl: '',  // Empty string since our endpoints are already absolute

    /**
     * Get the CSRF token from cookie
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
     * Make an API request with proper headers
     */
    async request(endpoint, options = {}) {
        const url = endpoint.startsWith('/') ? endpoint : this.baseUrl + endpoint;
        
        // Set default headers
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        // Add CSRF token from cookie for POST/PUT/DELETE/PATCH requests
        if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method?.toUpperCase())) {
            const csrftoken = this.getCookie('csrftoken');
            if (csrftoken) {
                console.log('Adding CSRF token to request');
                headers['X-CSRFToken'] = csrftoken;
            } else {
                console.warn('No CSRF token found');
            }
        }
        
        try {
            console.log(`Making API request to: ${url}`);
            console.log('Request headers:', JSON.stringify(headers));
            
            const response = await fetch(url, {
                ...options,
                headers,
                credentials: 'include'  // Include cookies in the request (important for session auth)
            });
            
            console.log(`Response status: ${response.status} ${response.statusText}`);
            
            // Handle 401 Unauthorized or 403 Forbidden (not authenticated)
            if (response.status === 401 || response.status === 403) {
                console.error(`Authentication failed (${response.status}). Redirecting to login.`);
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
     * Auth methods
     */
    auth: {
        async login(username, password, csrfToken) {
            // We'll use the form-based login instead of API login
            // This is just a redirect method now
            window.location.href = '/accounts/login/';
            return { success: true };
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
            // Redirect to the logout URL - Django will handle the session cleanup
            window.location.href = '/accounts/logout/';
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
            try {
                console.log('API.emails.getAnalytics called');
                const result = await API.request('/emails/analytics/');
                console.log('Raw API result:', result);
                
                if (!result || result.error) {
                    console.error('Error fetching analytics:', result?.error);
                    return { 
                        error: true, 
                        message: 'Failed to fetch analytics data',
                        details: result?.data 
                    };
                }
                
                // If the result is directly the data (no data property)
                if (!result.data) {
                    console.log('API response has no data property, returning raw result');
                    return result;
                }
                
                // Process and return the formatted data for charts
                return {
                    data: {
                        total_sent: result.data.total_sent || 0,
                        total_opened: result.data.total_opened || 0,
                        total_clicked: result.data.total_clicked || 0,
                        open_rate: result.data.open_rate || 0,
                        click_rate: result.data.click_rate || 0,
                        template_stats: result.data.template_stats || [],
                        recent_emails: result.data.recent_emails || []
                    }
                };
            } catch (error) {
                console.error('Exception in getAnalytics:', error);
                return { error: true, message: error.message };
            }
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
    },
    
    /**
     * Campaigns methods
     */
    campaigns: {
        async getAll() {
            return await API.request('/campaigns/api/');
        },
        
        async get(id) {
            return await API.request(`/campaigns/api/${id}/`);
        },
        
        async create(campaignData) {
            return await API.request('/campaigns/api/', {
                method: 'POST',
                body: JSON.stringify(campaignData)
            });
        },
        
        async update(id, campaignData) {
            return await API.request(`/campaigns/api/${id}/`, {
                method: 'PUT',
                body: JSON.stringify(campaignData)
            });
        },
        
        async delete(id) {
            return await API.request(`/campaigns/api/${id}/`, {
                method: 'DELETE'
            });
        },
        
        async getRecent() {
            return await API.request('/campaigns/api/recent/');
        }
    }
};

// Export for use in other files
window.API = API; 