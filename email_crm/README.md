# Email CRM

A simple, barebones Email Customer Relationship Management (CRM) system built with Django and JavaScript.

## Features

- **User Authentication**: Secure login and registration
- **Contact Management**: Add, view, edit, and delete contacts
- **Email Templates**: Create and manage reusable email templates
- **Email Sending**: Send personalized emails to individual contacts or in bulk
- **Email Analytics**: Track open rates and engagement metrics
- **Dashboard**: View key metrics and recent activities

## Technology Stack

- **Backend**: Django 5.0.2, Django REST Framework
- **Frontend**: Vanilla JavaScript
- **Authentication**: JWT (JSON Web Tokens)
- **Database**: SQLite (development), PostgreSQL (production)

## Project Structure

```
email_crm/
├── accounts/         # User authentication and profiles
├── contacts/         # Contact management
├── dashboard/        # Dashboard and analytics
├── emails/           # Email templates and sending
├── email_crm/        # Project settings
├── static/           # Static assets (JS, CSS)
│   └── js/
│       └── api.js    # JavaScript API client
├── templates/        # HTML templates
│   └── home/
│       └── index.html  # Homepage
├── manage.py         # Django management script
└── requirements.txt  # Python dependencies
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd email_crm
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Apply migrations:
   ```
   python manage.py migrate
   ```

5. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```
   python manage.py runserver
   ```

7. Access the application at http://127.0.0.1:8000/

## API Endpoints

### Authentication
- `POST /api/token/` - Obtain JWT token
- `POST /api/token/refresh/` - Refresh JWT token
- `POST /api/accounts/register/` - Register a new user

### Contacts
- `GET /api/contacts/` - List all contacts
- `POST /api/contacts/` - Create a new contact
- `GET /api/contacts/<id>/` - Retrieve a contact
- `PUT /api/contacts/<id>/` - Update a contact
- `DELETE /api/contacts/<id>/` - Delete a contact
- `GET /api/contacts/search/?q=<query>` - Search contacts

### Email Templates
- `GET /api/emails/templates/` - List all templates
- `POST /api/emails/templates/` - Create a new template
- `GET /api/emails/templates/<id>/` - Retrieve a template
- `PUT /api/emails/templates/<id>/` - Update a template
- `DELETE /api/emails/templates/<id>/` - Delete a template

### Emails
- `POST /api/emails/send/<contact_id>/` - Send email to a contact
- `POST /api/emails/bulk-send/` - Send emails to multiple contacts
- `GET /api/emails/analytics/` - Get email analytics

### Dashboard
- `GET /api/dashboard/` - Get dashboard summary
- `GET /api/dashboard/stats/` - Get detailed statistics
- `GET /api/dashboard/recent-activities/` - Get recent activities

## JavaScript Client Usage

The `api.js` file provides a simple client for interacting with the API:

```javascript
// Authentication
await API.auth.login(username, password);
await API.auth.register(userData);
API.auth.logout();

// Contacts
const { data } = await API.contacts.getAll();
await API.contacts.create(contactData);
await API.contacts.update(id, contactData);
await API.contacts.delete(id);
await API.contacts.search(query);

// Email Templates
const { data } = await API.emailTemplates.getAll();
await API.emailTemplates.create(templateData);

// Emails
await API.emails.send(contactId, emailData);
await API.emails.bulkSend(contactIds, templateId);
await API.emails.getAnalytics();

// Dashboard
const { data } = await API.dashboard.getSummary();
```

## Development

### Running Migrations

```
python manage.py makemigrations
python manage.py migrate
```

### Running Tests

```
python manage.py test
```

## Production Deployment

For production, make sure to:

1. Set `DEBUG = False` in settings.py
2. Configure a production database (PostgreSQL recommended)
3. Set a secure `SECRET_KEY`
4. Configure proper email backend settings
5. Set up static files serving with a proper web server

## License

MIT

## Acknowledgments

- Django and Django REST Framework
- All the open-source libraries used in this project 