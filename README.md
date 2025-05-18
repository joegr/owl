# Email CRM MVP

A barebones Email Customer Relationship Management (CRM) system designed to help businesses manage contacts and email communications effectively.

## Tech Stack

- **Backend**: Python Django
- **Frontend**: Simple JavaScript
- **BDD Testing**: Gherkin/Cucumber

## Project Overview

This project implements a minimum viable product (MVP) for an email-based CRM system with the following core features:

- User authentication (login/logout)
- Contact management (add, view, edit, delete)
- Email template creation and management
- Individual and bulk email sending
- Basic email analytics
- Dashboard with key metrics

## Behavior-Driven Development

The `features/email_crm.feature` file contains the Gherkin specification for the system, defining the behavior of each core feature from a user perspective. These specifications serve as:

1. **Requirements documentation** - Clearly defining what the system should do
2. **Acceptance criteria** - Providing a way to verify that implementation meets requirements
3. **User story validation** - Ensuring the system delivers value to users

## Development Approach

1. Implement the Django backend with:
   - User authentication
   - RESTful API endpoints for contact and email management
   - Email sending functionality
   - Analytics tracking

2. Create a simple JavaScript frontend that:
   - Consumes the Django API
   - Provides an intuitive user interface
   - Implements responsive design for all device sizes

3. Write automated tests based on the Gherkin scenarios

## Getting Started

*Instructions for setting up the development environment will be added when implementation begins.*

## Real Email Sending Tests

The `email_crm/emails/tests/test_real_email_sending.py` file contains tests to verify that emails are actually sent through a configured SMTP server (e.g., Gmail). These tests require a real email account and its credentials.

**Configuration:**

1.  **Enable 2-Factor Authentication (2FA)** for your test email account (e.g., Gmail).
2.  **Generate an App Password** for the email account. This password will be used instead of your regular account password.
3.  Set the following environment variables:
    ```bash
    export TEST_EMAIL_USER="your-email@example.com"
    export TEST_EMAIL_PASSWORD="your-app-password"
    ```
    Replace `"your-email@example.com"` with your test email address and `"your-app-password"` with the generated app password.

**Running the Tests:**

To run these specific tests:

```bash
pytest email_crm/emails/tests/test_real_email_sending.py -v
```

**Note:** These tests will attempt to send real emails. Ensure your SMTP settings and credentials are correct. The tests are designed to skip if the `TEST_EMAIL_USER` or `TEST_EMAIL_PASSWORD` environment variables are not set.

## Contributing

This is an MVP project. Future enhancements might include:
- Advanced segmentation and targeting
- Email campaign scheduling
- Integration with other marketing tools
- Enhanced analytics and reporting 