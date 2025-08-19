# Symplora Leave Management System

## Project Overview

This project is an **Symplora Leave Management System** that provides comprehensive functionality for managing employee information and leave requests in an organization.

### Key Features

- **Employee Management**: Adding employees with details (Name, Email, Department, Joining Date)
- **Job & Department Management**: Creating jobs and departments, and assigning them to employees
- **Leave Application**: Applying for leave with proper validation
- **Leave Approval Workflow**: Approving and rejecting leave requests
- **Leave Balance Tracking**: Real-time tracking of leave balance for each employee
- **API-First Approach**: RESTful APIs for all operations
- **Modern Frontend**: Interactive React-based user interface

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Django, Django REST Framework |
| **Database** | PostgreSQL |
| **Containerization** | Docker, Docker Compose |
| **Frontend** | React, Tailwind CSS |

## Setup Instructions

### Prerequisites

Ensure you have the following installed on your system:

- Docker & Docker Compose
- Node.js & npm (for frontend development)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/CaptainRedCodes/Symplora-Assignment
   ```

2. **Build and run Docker containers:**
   ```bash
   docker-compose up --build
   ```

3. **Access the API:**
   The backend API will be available at `http://localhost:8000/`

4. **Swagger API Documentation:**
   The swagger API will be available at `http://localhost:8000/api/schema/swagger-ui/`

5 **Create a .env file:**
   Create a .env file which is same as .env-example



## System Assumptions

- **Unique Email Addresses**: Each employee must have a unique email address
- **Predefined Leave Types**: Leave types are predefined (e.g., Sick Leave, Casual Leave, Annual Leave)
- **Annual Balance Reset**: Leave balances are tracked per type and reset annually
- **Valid Assignments**: Only valid departments and jobs can be assigned to employees
- **Post-Joining Leave**: Leave requests can only be applied for dates after the employee's joining date

## APIs & Core Features

### Employee APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/employees/` | Add a new employee |
| `GET` | `/api/employees/` | List all employees |

### Leave APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/leaves/apply/` | Apply for leave |
| `PATCH` | `/api/leaves/{id}/approve/` | Approve a leave request |
| `PATCH` | `/api/leaves/{id}/reject/` | Reject a leave request |
| `GET` | `/api/leaves/balance/{employee_id}/` | Get employee's leave balance |

and more ....

## Edge Cases Handled

### Validation & Business Logic

- **Pre-joining Leave Application**: Request rejected if applied before joining date
- **Insufficient Balance**: Request rejected when applying for more days than available
- **Overlapping Requests**: Prevents conflicting leave requests for the same period
- **Employee Verification**: Returns `404 Not Found` for non-existent employees
- **Date Validation**: Rejects requests with invalid date ranges (end date before start date)
- **Employee Deletion**: Restricts deletion of employees with pending leave requests
- **Dynamic Updates**: Ensures leave balance consistency when types/allocations are updated

### Future Considerations

- **Weekend/Holiday Handling**: Optional feature for future implementation
- **Advanced Leave Policies**: Support for complex organizational policies
- **Employee Viewing**: Employee can login and view their data
- **Authentication**: Authentication with role based system
- **Manager Approval for Loan**: Managers can approve the leave without the need of HR
- **Manager Control**: Manager having control for employement dashboard
- **Mail and Messaging system**: Having to send alerts through mails and message
- **Mobile Version**: Helps in geting information in Mobile

and more ...

## Potential Improvements

### Enhancement Roadmap

#### **Notifications & Communication**
- **Email/SMS Alerts**: Automated notifications for leave approval/rejection
- **Real-time Updates**: WebSocket integration for instant status updates

#### **User Interface Enhancements**
- **Calendar View**: Visual representation of leaves and holidays
- **Dashboard Analytics**: Leave trends and department-wise reports
- **Mobile Responsiveness**: Optimized mobile experience

#### **Access Control & Security**
- **Role-Based Access Control**: Admin, Manager, Employee permission levels
- **Authentication**: JWT-based secure authentication
- **Audit Trail**: Complete history of all leave-related actions

#### **Advanced Features**
- **Reporting & Analytics**: Export leave history and balances to CSV/PDF
- **Bulk Operations**: CSV upload for adding multiple employees
- **Leave Policies**: Encashment, carry forward, and advanced leave rules
- **Integration**: Calendar integration (Google Calendar, Outlook)

#### **Quality Assurance**
- **Automated Testing**: Comprehensive unit and integration tests
- **Performance Monitoring**: API performance tracking and optimization
- **Documentation**: Interactive API documentation with Swagger/OpenAPI

## Project Structure

```
symplora/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
├── docker-compose.yml
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
