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

## Contributing

This is an MVP project. Future enhancements might include:
- Advanced segmentation and targeting
- Email campaign scheduling
- Integration with other marketing tools
- Enhanced analytics and reporting 