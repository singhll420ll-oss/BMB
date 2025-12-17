# Bite Me Buddy - Food Ordering System

A production-ready, high-performance food ordering web application with admin, team member, and customer portals.

## Features

### 🎯 Core Features
- **Customer Portal**: Registration, service browsing, menu viewing, cart management, order placement
- **Team Member Portal**: Assigned orders view, delivery confirmation with OTP, daily plans
- **Admin Portal**: Full system management, analytics, reporting
- **Real-time IST Clock**: With hidden admin access trigger
- **OTP Delivery Verification**: Twilio SMS integration
- **Online Time Tracking**: User session monitoring

### 🔐 Security Features
- Role-based access control (Customer, Team Member, Admin)
- Secure password hashing (bcrypt)
- JWT token authentication with HTTP-only cookies
- Session tracking with login/logout times
- SQL injection protection (SQLAlchemy)
- XSS protection (Jinja2 auto-escaping)

### 📱 Mobile-First Design
- Fully responsive Bootstrap 5 interface
- Touch-friendly buttons and controls
- Mobile-optimized layouts
- Smooth HTMX-powered updates

### 🚀 Performance
- Full async/await architecture
- PostgreSQL with optimized queries
- HTMX for partial page updates
- Efficient file upload handling

## Technology Stack

- **Backend**: Python 3.11 + FastAPI (async)
- **Database**: PostgreSQL + SQLAlchemy 2.0 + Alembic
- **Validation**: Pydantic v2 (strict mode)
- **Frontend**: Jinja2 templates + Bootstrap 5 + HTMX
- **Security**: passlib (bcrypt), JWT tokens
- **SMS**: Twilio integration for OTP
- **File Upload**: python-multipart
- **Logging**: Structured logging with structlog

## Installation & Setup

### Prerequisites
- Python 3.11 or higher
- PostgreSQL 12 or higher
- Twilio account (for SMS OTP)

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd bite-me-buddy

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt