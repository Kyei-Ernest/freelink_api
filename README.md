# 🔗 FREELINK API

A powerful REST API for building freelance marketplaces, built with **Django REST Framework**.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.16-red.svg)](https://django-rest-framework.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Overview

FREELINK is a complete backend system for freelance job marketplaces like Upwork and Fiverr. It provides everything you need to connect clients with freelancers:

- **Clients** can post jobs, create contracts, and manage milestones
- **Freelancers** can apply for jobs, earn skill badges, and get paid securely
- Built-in **escrow system**, **dispute resolution**, and **referral program**

> 🚀 Ready to integrate with any frontend framework (React, Vue, Next.js, Flutter, etc.)

---

## ✨ Features

### Core Features
| Feature | Description |
|---------|-------------|
| 🔐 **Authentication** | Token-based auth with email verification |
| 👤 **User Profiles** | Separate flows for clients and freelancers |
| 💼 **Job Management** | Post, search, filter, and apply for jobs |
| 📝 **Proposals** | Freelancers submit bids with cover letters |
| 📄 **Contracts** | Milestone-based contracts with escrow |
| 💬 **Messaging** | Real-time chat between users |
| 💰 **Payments** | Paystack integration for deposits & payouts |
| ⭐ **Ratings** | 1-5 star reviews after job completion |

### Differentiating Features
| Feature | Description |
|---------|-------------|
| 🏅 **Skill Badges** | Verified skill certifications (Beginner → Expert) |
| ⏱️ **Response Time** | Track and display average response times |
| 🔗 **Referral System** | Invite friends, earn rewards |
| 📋 **Project Templates** | Quick job creation from templates |
| ⚖️ **Dispute Resolution** | Built-in dispute management |

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| Django 5.2 | Web framework |
| Django REST Framework | API layer |
| PostgreSQL / SQLite | Database |
| Paystack | Payment processing |
| Redis | Caching (optional) |
| Celery | Background tasks (optional) |
| drf-spectacular | Auto-generated API docs |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip
- Virtual environment (recommended)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/freelink-api.git
cd freelink-api

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your settings

# 5. Run migrations
python manage.py migrate

# 6. Create superuser (optional)
python manage.py createsuperuser

# 7. Start the server
python manage.py runserver
```

### 🐳 Docker Quick Start (Recommended)

```bash
# One command to run everything
docker-compose up

# Or run in background
docker-compose up -d

# Stop services
docker-compose down
```

**Services included:**
| Service | Port | Description |
|---------|------|-------------|
| API | 8000 | Django REST API |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache |
| PgAdmin | 5050 | DB Management |

### Load Sample Data

```bash
# Load demo skills, badges, and templates
python manage.py loaddata fixtures/seed_data.json
```

### Environment Variables

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (optional - defaults to SQLite)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=freelink
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Paystack
PAYSTACK_SECRET_KEY=sk_test_xxx
PAYSTACK_PUBLIC_KEY=pk_test_xxx

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Cache (optional - for production)
CACHE_BACKEND=django.core.cache.backends.redis.RedisCache
CACHE_LOCATION=redis://127.0.0.1:6379/1
```

---

## 📚 API Documentation

Interactive API documentation is available at:

| Docs | URL |
|------|-----|
| **Swagger UI** | `http://localhost:8000/api/schema/swagger-ui/` |
| **ReDoc** | `http://localhost:8000/api/schema/redoc/` |
| **OpenAPI Schema** | `http://localhost:8000/api/schema/` |

### API Endpoints Overview

```
/api/users/          → Authentication & user management
/api/profiles/       → User profiles & referrals
/api/jobs/           → Job listings & skill badges
/api/proposals/      → Job applications
/api/contracts/      → Contracts, milestones & templates
/api/disputes/       → Dispute management
/api/chat/           → Messaging
/api/notifications/  → User notifications
/api/wallet/         → Wallet balance & transactions
/api/payments/       → Paystack payments
/api/ratings/        → Reviews & ratings
```

---

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test users jobs ratings

# Run with verbosity
python manage.py test --verbosity=2
```

---

## 📁 Project Structure

```
FREELINK/
├── FREELINK_root/        # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/                # Authentication & user model
├── profiles/             # User profiles, stats & referrals
├── jobs/                 # Jobs & skill badges
├── proposals/            # Job applications
├── contracts/            # Contracts, milestones & templates
├── disputes/             # Dispute resolution
├── chat/                 # Messaging system
├── notifications/        # User notifications
├── wallet/               # Wallet management
├── payments/             # Paystack integration
├── ratings/              # Reviews & ratings
└── dashboard/            # User dashboards
```

---

## 🔒 Security Features

- ✅ Token-based authentication
- ✅ Password hashing with Django's PBKDF2
- ✅ CORS protection
- ✅ Rate limiting (throttling)
- ✅ Environment variables for secrets
- ✅ Input validation on all endpoints
- ✅ Permission-based access control

---

## 🚀 Performance Optimizations

- **Database Indexes**: On frequently queried fields
- **Query Optimization**: `select_related` and `prefetch_related`
- **Pagination**: 20 items per page default
- **Caching**: Ready for Redis in production
- **JSON Renderer**: Optimized response serialization

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

- 📧 Email: ernestkyei101@gmail.com
- 📚 Documentation: [API Docs](http://localhost:8000/api/schema/swagger-ui/)
- 🐛 Issues: [GitHub Issues](https://github.com/your-username/freelink-api/issues)

---

<p align="center">
  Built with ❤️ using Django REST Framework
</p>

