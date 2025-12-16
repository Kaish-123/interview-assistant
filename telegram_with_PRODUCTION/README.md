# TechyEra Marketing - Production SaaS

A professional Telegram Marketing Automation SaaS platform with user authentication, subscription payments, and multi-tenant architecture.

## 🚀 Features

- **User Authentication** - JWT-based login/signup
- **Multi-tenant** - Each user has their own data
- **Subscription Plans** - Free, Starter, Pro, Business
- **Stripe Integration** - Payment processing
- **PostgreSQL Database** - Production-ready storage
- **Redis Caching** - Performance optimization
- **Docker Ready** - Easy deployment

## 📁 Project Structure

```
telegram_with_PRODUCTION/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── config.py         # Configuration settings
│   ├── models.py         # SQLAlchemy models
│   ├── database.py       # Database connection
│   ├── auth.py           # Authentication system
│   └── stripe_service.py # Stripe integration
├── templates/
│   ├── landing.html      # Landing page
│   ├── pricing.html      # Pricing page
│   ├── auth/
│   │   ├── login.html
│   │   └── signup.html
│   └── dashboard/
│       └── index.html
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── env.example
└── README.md
```

## 🛠 Quick Start

### Option 1: Docker (Recommended)

1. **Clone and configure:**
   ```bash
   cd telegram_with_PRODUCTION
   cp env.example .env
   # Edit .env with your configuration
   ```

2. **Start with Docker:**
   ```bash
   docker-compose up -d
   ```

3. **Access the app:**
   - http://localhost:8000

### Option 2: Local Development

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup PostgreSQL:**
   ```bash
   # Using Docker
   docker run -d --name postgres \
     -e POSTGRES_PASSWORD=password \
     -e POSTGRES_DB=techyera_db \
     -p 5432:5432 postgres:15-alpine
   ```

4. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env file
   ```

5. **Run the app:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | App secret key | `random-secret-key` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://user:pass@host/db` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `STRIPE_SECRET_KEY` | Stripe secret key | `sk_test_...` |
| `STRIPE_PUBLISHABLE_KEY` | Stripe public key | `pk_test_...` |
| `JWT_SECRET_KEY` | JWT signing key | `jwt-secret-key` |

### Stripe Setup

1. Create a Stripe account at https://stripe.com
2. Create Products and Prices for each plan:
   - Starter: $19/month
   - Pro: $49/month
   - Business: $99/month
3. Add the Price IDs to your `.env` file
4. Set up Stripe webhooks pointing to `/api/webhooks/stripe`

## 💳 Subscription Plans

| Plan | Price | Features |
|------|-------|----------|
| **Free** | $0/mo | 1 account, 5 groups, 10 msgs/day |
| **Starter** | $19/mo | 1 account, 50 groups, 100 msgs/day |
| **Pro** | $49/mo | 3 accounts, 200 groups, 500 msgs/day |
| **Business** | $99/mo | 10 accounts, unlimited |

## 🔒 Security

- Passwords hashed with bcrypt
- JWT token authentication
- CORS protection
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection

## 🚀 Deployment

### Railway / Render

1. Connect your GitHub repository
2. Set environment variables
3. Deploy!

### AWS / DigitalOcean

1. Build Docker image:
   ```bash
   docker build -t techyera-marketing .
   ```

2. Push to container registry:
   ```bash
   docker tag techyera-marketing your-registry/techyera-marketing
   docker push your-registry/techyera-marketing
   ```

3. Deploy with docker-compose or Kubernetes

## 📄 API Endpoints

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user
- `GET /api/auth/me` - Get current user

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics

### Billing
- `POST /api/billing/create-checkout` - Create Stripe checkout session
- `POST /api/billing/portal` - Get billing portal URL
- `POST /api/webhooks/stripe` - Stripe webhook handler

## 📞 Support

For support, email support@techyera.co or visit https://techyera.co

## 📜 License

Copyright © 2024 TechyEra. All rights reserved.

