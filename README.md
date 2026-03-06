<div align="center">

# 🤖 AI Review Manager

**Automatically monitor Google Maps reviews and respond with AI-generated replies — built for agencies and multi-location businesses.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com)
[![Groq](https://img.shields.io/badge/Groq-Llama_3-F55036?style=flat-square)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](./LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](./CONTRIBUTING.md)

[Live Demo](#) · [Report a Bug](../../issues) · [Request a Feature](../../issues)

</div>

---

## 📖 Project Overview

**AI Review Manager** is a production-ready, multi-tenant SaaS platform that helps business owners stay on top of their Google Maps reputation — without the manual effort.

Once a business is connected, the platform **automatically scrapes new Google reviews**, **generates professional reply suggestions** using Groq's Llama models, and presents them in a clean dashboard where owners can **approve, edit, or regenerate** any response before posting.

Built for agencies managing multiple clients, franchise owners, and any business that values its online reputation.

> **Why this project?** Responding to Google reviews improves local SEO rankings and builds customer trust — but most business owners don't have the time. AI Review Manager makes it effortless.

---

## ✨ Features

- 🏢 **Multi-tenant architecture** — each user manages their own set of businesses in full isolation
- 🔍 **Automated review scraping** — Apify fetches the latest Google Maps reviews on a schedule
- 🤖 **AI reply generation** — Groq (Llama 3) crafts contextual, professional replies tailored to each review's tone and rating
- ✅ **Reply approval workflow** — Approve, edit, reject, or regenerate any AI suggestion
- 📊 **Analytics dashboard** — rating distributions, weekly review trends, reply status breakdown
- 🔄 **Background scheduler** — APScheduler polls all businesses for new reviews every N hours automatically
- 🔐 **Secure authentication** — JWT-based auth with bcrypt password hashing
- 📋 **One-click copy** — copy approved replies to paste directly into Google Maps
- 🐳 **Docker-ready** — full `docker-compose` setup for instant local or cloud deployment

---

## 🏗 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│              Next.js 14 + TypeScript + Tailwind             │
│   Login │ Dashboard │ Businesses │ Reviews │ Analytics      │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API (JWT)
┌──────────────────────▼──────────────────────────────────────┐
│                        BACKEND                              │
│                    FastAPI (Python)                         │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Auth API   │  │ Business API │  │   Reviews API    │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Background Scheduler (APScheduler)      │   │
│  └──────────────────────────────────────────────────────┘   │
└───────┬─────────────────────┬───────────────────┬───────────┘
        │                     │                   │
┌───────▼──────┐   ┌──────────▼──────┐  ┌────────▼────────┐
│   Supabase   │   │     Apify       │  │   Groq API      │
│  PostgreSQL  │   │ Reviews Scraper │  │   Llama 3.x     │
│  (Database)  │   │ (Google Maps)   │  │ (AI Replies)    │
└──────────────┘   └─────────────────┘  └─────────────────┘
```

### Data Flow

1. **Scheduler triggers** → calls Apify scraper for each registered business
2. **Apify** fetches latest Google Maps reviews and returns structured JSON
3. **Backend deduplicates** reviews and stores only new ones in Supabase
4. **Groq (Llama 3)** generates a reply suggestion for each new review
5. **Reply stored** in `ai_replies` table with `pending` status
6. **Owner logs in** → sees pending replies in their dashboard
7. **Owner approves / edits** → reply is marked `approved` and can be copied to Google Maps

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Next.js 14, TypeScript | React framework with App Router |
| **Styling** | Tailwind CSS | Utility-first CSS |
| **Charts** | Recharts | Analytics visualizations |
| **Backend** | FastAPI (Python 3.11) | High-performance async API |
| **Database** | Supabase (PostgreSQL) | Multi-tenant data storage + Row Level Security |
| **Auth** | JWT + bcrypt | Secure stateless authentication |
| **Review Scraping** | Apify — Google Maps Scraper | Automated review collection |
| **AI Generation** | Groq API + Llama 3 | Fast, cost-effective reply generation |
| **Scheduler** | APScheduler | Periodic background jobs |
| **Containerization** | Docker + docker-compose | Reproducible deployments |

---

## 🔄 System Workflow

```
Business Owner
     │
     ▼
① Sign up & log in
     │
     ▼
② Add business (Google Maps URL)
     │
     ▼
③ Apify scrapes reviews ──────────────────────┐
     │                                         │ runs every N hours
     ▼                                         │ (background scheduler)
④ New reviews stored in Supabase ◄────────────┘
     │
     ▼
⑤ Groq generates AI reply for each new review
     │
     ▼
⑥ Reply saved as "pending" in database
     │
     ▼
⑦ Owner sees suggestion in dashboard
     │
     ├──► Approve → mark as approved, copy to clipboard
     ├──► Edit → modify text, then approve
     └──► Regenerate → request a new AI reply
```

---

## 📁 Folder Structure

```
ai-review-manager/
│
├── .env.example                  # Environment variable template
├── README.md
├── docker-compose.yml            # Orchestrates backend + frontend
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py               # FastAPI app entry point + lifecycle
│       │
│       ├── api/                  # Route handlers
│       │   ├── auth.py           # POST /auth/signup, /auth/login
│       │   ├── business.py       # CRUD + manual refresh trigger
│       │   ├── reviews.py        # List reviews + analytics
│       │   └── replies.py        # Approve / reject / regenerate
│       │
│       ├── core/
│       │   ├── config.py         # Pydantic settings (env vars)
│       │   ├── database.py       # Supabase client (cached)
│       │   ├── security.py       # JWT creation + bcrypt
│       │   └── deps.py           # Auth dependency injection
│       │
│       ├── models/
│       │   └── schemas.py        # All Pydantic request/response models
│       │
│       └── services/
│           ├── apify_service.py  # Google Maps review scraping
│           ├── ai_service.py     # Groq reply generation
│           └── scheduler.py      # APScheduler background job
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── src/
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── page.tsx          # Root redirect
│       │   ├── globals.css
│       │   ├── auth/
│       │   │   ├── login/        # Login page
│       │   │   └── signup/       # Signup page
│       │   └── dashboard/
│       │       ├── layout.tsx    # Sidebar + auth guard
│       │       ├── page.tsx      # Overview + stats
│       │       ├── business/     # Business management
│       │       ├── reviews/      # Review + reply workflow
│       │       └── analytics/    # Charts & metrics
│       │
│       ├── components/
│       │   ├── layout/
│       │   │   └── Sidebar.tsx
│       │   └── ui/
│       │       ├── StarRating.tsx
│       │       └── StatusBadge.tsx
│       │
│       ├── lib/
│       │   ├── api.ts            # Axios client with JWT injection
│       │   └── auth.ts           # Auth helpers (cookies + localStorage)
│       │
│       └── types/
│           └── index.ts          # Shared TypeScript interfaces
│
└── database/
    └── schema.sql                # Full Supabase schema with RLS policies
```

---

## ⚙️ Installation Guide

### Prerequisites

Make sure you have the following installed and configured:

| Tool | Version | Notes |
|---|---|---|
| Python | 3.11+ | Backend runtime |
| Node.js | 20+ | Frontend runtime |
| Docker | Latest | Optional, for containerized setup |
| Supabase account | — | [supabase.com](https://supabase.com) — free tier works |
| Apify account | — | [apify.com](https://apify.com) — free tier includes credits |
| Groq account | — | [console.groq.com](https://console.groq.com) — free tier available |

---

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-review-manager.git
cd ai-review-manager
```

---

### 2. Set Up the Database

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** in your Supabase dashboard
3. Paste and run the full contents of [`database/schema.sql`](./database/schema.sql)

This creates the `users`, `businesses`, `reviews`, and `ai_replies` tables with proper indexes and Row Level Security policies.

---

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in all required values (see [Environment Variables](#-environment-variables) below).

---

### 4. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Start the development server
uvicorn app.main:app --reload --port 8000
```

The API will be live at `http://localhost:8000`
Interactive docs available at `http://localhost:8000/docs`

---

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create local env file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start the development server
npm run dev
```

The frontend will be live at `http://localhost:3000`

---

## 🔐 Environment Variables

Create a `.env` file in the project root based on the template below:

```env
# ──────────────────────────────────────────
# Supabase
# ──────────────────────────────────────────
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-role-key
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# ──────────────────────────────────────────
# JWT Authentication
# ──────────────────────────────────────────
SECRET_KEY=your-super-secret-key-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ──────────────────────────────────────────
# Groq API (AI Reply Generation)
# ──────────────────────────────────────────
GROQ_API_KEY=gsk_your-groq-api-key

# ──────────────────────────────────────────
# Apify (Google Maps Review Scraping)
# ──────────────────────────────────────────
APIFY_API_TOKEN=apify_api_your-token

# ──────────────────────────────────────────
# Application
# ──────────────────────────────────────────
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development

# ──────────────────────────────────────────
# Scheduler
# ──────────────────────────────────────────
REVIEW_CHECK_INTERVAL_HOURS=6
```

| Variable | Where to get it |
|---|---|
| `SUPABASE_URL` | Supabase Dashboard → Project Settings → API |
| `SUPABASE_KEY` | Supabase Dashboard → Project Settings → API → `anon` key |
| `SUPABASE_SERVICE_KEY` | Supabase Dashboard → Project Settings → API → `service_role` key |
| `SECRET_KEY` | Generate with `openssl rand -hex 32` |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) → API Keys |
| `APIFY_API_TOKEN` | [apify.com](https://console.apify.com/account/integrations) → Integrations |

---

## 🚀 Running the Project

### Option A — Local Development

Run backend and frontend in separate terminals:

```bash
# Terminal 1 — Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

### Option B — Docker Compose

Run the entire stack with a single command:

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |

To stop:
```bash
docker-compose down
```

---

## 📡 API Overview

All protected routes require the `Authorization: Bearer <token>` header.

### Authentication

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/auth/signup` | Register a new user | ❌ |
| `POST` | `/auth/login` | Login and receive JWT token | ❌ |

**Login response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": "uuid",
  "email": "user@example.com"
}
```

---

### Businesses

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/business` | List all businesses for current user | ✅ |
| `POST` | `/business` | Add a new business | ✅ |
| `GET` | `/business/{id}` | Get a specific business | ✅ |
| `DELETE` | `/business/{id}` | Delete a business | ✅ |
| `POST` | `/business/{id}/refresh` | Manually trigger a review scrape | ✅ |

**Create business body:**
```json
{
  "business_name": "Acme Coffee Shop",
  "google_maps_url": "https://maps.google.com/...",
  "description": "Our downtown location"
}
```

---

### Reviews

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/reviews` | List reviews (filterable by business, rating) | ✅ |
| `GET` | `/reviews/analytics` | Aggregate stats and rating distribution | ✅ |

**Query parameters for `GET /reviews`:**

| Param | Type | Description |
|---|---|---|
| `business_id` | `string` | Filter by business |
| `rating` | `integer` | Filter by star rating (1–5) |
| `processed` | `boolean` | Filter by processed status |
| `limit` | `integer` | Max results (default: 50) |
| `offset` | `integer` | Pagination offset |

---

### Replies

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/reply/approve` | Approve a reply (optionally with edited text) | ✅ |
| `POST` | `/reply/reject` | Reject a reply suggestion | ✅ |
| `GET` | `/reply/{review_id}` | Get all reply versions for a review | ✅ |
| `POST` | `/reply/{review_id}/regenerate` | Generate a new AI reply | ✅ |

**Approve reply body:**
```json
{
  "reply_id": "uuid",
  "edited_text": "Optional edited version of the reply..."
}
```

---

## 📸 Screenshots

> _Screenshots and demo GIFs will be added after initial deployment._

| Screen | Description |
|---|---|
| ![Dashboard](#) | Main dashboard with stats cards and recent reviews |
| ![Reviews](#) | Review list with expandable AI reply cards |
| ![Analytics](#) | Rating distribution bar chart + reply status pie chart |
| ![Business](#) | Business management with Google Maps URL input |

---

## 🗄 Database Schema

```
users
  id · email · password_hash · full_name · created_at

businesses
  id · user_id (FK) · business_name · google_maps_url · description · created_at

reviews
  id · business_id (FK) · reviewer_name · review_text · rating
  review_date · processed · created_at

ai_replies
  id · review_id (FK) · reply_text · status [pending|approved|rejected]
  created_at · updated_at
```

Multi-tenancy is enforced by filtering every query through `user_id → business_id → reviews → ai_replies`. The Supabase service role key is used server-side only — all client-facing queries are scoped per user.

---

## 🔮 Future Improvements

- [ ] **Direct Google API integration** — post approved replies to Google Business Profile automatically via the Google My Business API
- [ ] **Email / Slack notifications** — alert owners when new reviews arrive or when a 1-star review is detected
- [ ] **Reply templates** — let users define tone and style guidelines that influence AI-generated replies
- [ ] **Sentiment analysis** — categorize reviews by topic (service, price, staff) for deeper insights
- [ ] **Multi-language support** — detect review language and reply in the same language
- [ ] **White-label mode** — agencies can rebrand the dashboard for their clients
- [ ] **Stripe billing integration** — per-business or per-review pricing tiers
- [ ] **Review response rate metrics** — track what percentage of reviews have received responses
- [ ] **Competitor benchmarking** — compare rating trends against nearby businesses
- [ ] **Mobile app** — React Native companion app for on-the-go approvals

---

## 🤝 Contributing

Contributions are welcome and appreciated!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m 'feat: add your feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a Pull Request

Please follow the [Conventional Commits](https://www.conventionalcommits.org/) standard for commit messages and ensure your code passes linting before submitting.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for full details.

```
MIT License

Copyright (c) 2025 AI Review Manager Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

<div align="center">

Built with ❤️ using FastAPI, Next.js, Supabase, Groq, and Apify.

⭐ **Star this repo** if you find it useful!

</div>