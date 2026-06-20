<div align="center">

# AI Review Manager

**Google Maps reviews that go unanswered kill local SEO. This fixes that — automatically.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com)
[![Groq](https://img.shields.io/badge/Groq-Llama_3-F55036?style=flat-square)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](./LICENSE)

[Live Demo](#) · [API Docs](#) · [Report Bug](../../issues)

</div>

---

## The Problem

95% of business owners know they should respond to Google reviews. Almost none of them do — not because they don't care, but because it's tedious, repetitive, and falls to the bottom of every to-do list.

Unanswered reviews hurt local SEO. They signal to Google (and customers) that nobody's home.

## What This Does

AI Review Manager runs in the background and handles the entire loop:

1. **Scrapes** new Google Maps reviews on a schedule via Apify
2. **Generates** a contextual reply using Groq's Llama 3 — matching the review's tone, rating, and sentiment
3. **Surfaces** the draft in a clean dashboard for one-click approve, edit, or regenerate
4. **Copies** the approved reply to clipboard — ready to paste into Google Maps

No auto-posting (intentional). The owner stays in control of every word that goes public.

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│              Next.js 14 + Tailwind                │
│    Dashboard · Reviews · Analytics · Businesses   │
└───────────────────┬──────────────────────────────┘
                    │ REST (JWT)
┌───────────────────▼──────────────────────────────┐
│                  FastAPI                          │
│  Auth · Business · Reviews · Replies              │
│  APScheduler — polls every N hours                │
└──────┬──────────────────┬────────────┬────────────┘
       │                  │            │
  Supabase            Apify         Groq API
  PostgreSQL +     Google Maps    Llama 3.x
  RLS policies      Scraper      (reply gen)
```

**Multi-tenancy is enforced at the DB layer** — Supabase Row Level Security scopes every query through `user_id → business_id → reviews → ai_replies`. The service role key never leaves the server.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js 14 + TypeScript | App Router, strong typing, zero config |
| Backend | FastAPI (Python 3.11) | Async-native, auto Swagger docs, fast |
| Database | Supabase (PostgreSQL) | RLS for multi-tenancy out of the box |
| Auth | JWT + bcrypt | Stateless, simple, secure |
| Review Scraping | Apify — Google Maps Scraper | Reliable, maintained, handles anti-bot |
| AI Replies | Groq + Llama 3 | Sub-second inference, free tier generous |
| Scheduler | APScheduler | In-process, no infra overhead |
| Infra | Docker + docker-compose | One command to run the full stack |

---

## Getting Started

### Prerequisites

- Python 3.11+, Node.js 20+, Docker (optional)
- Free accounts: [Supabase](https://supabase.com), [Groq](https://console.groq.com), [Apify](https://apify.com)

### Setup

```bash
# 1. Clone
git clone https://github.com/yourusername/ai-review-manager.git
cd ai-review-manager

# 2. Configure
cp .env.example .env
# Fill in SUPABASE_URL, GROQ_API_KEY, APIFY_API_TOKEN, SECRET_KEY

# 3. Database — run database/schema.sql in your Supabase SQL editor

# 4a. Run with Docker (recommended)
docker-compose up --build

# 4b. Or run locally
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

| Service | URL |
|---|---|
| App | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |

### Environment Variables

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Auth
SECRET_KEY=         # openssl rand -hex 32
ACCESS_TOKEN_EXPIRE_MINUTES=60

# AI + Scraping
GROQ_API_KEY=gsk_...
APIFY_API_TOKEN=apify_api_...

# Scheduler
REVIEW_CHECK_INTERVAL_HOURS=6
```

---

## API

All protected routes require `Authorization: Bearer <token>`.

**Auth**
```
POST /auth/signup    — register
POST /auth/login     — returns JWT
```

**Businesses**
```
GET    /business              — list yours
POST   /business              — add new (name + Google Maps URL)
DELETE /business/{id}
POST   /business/{id}/refresh — trigger manual scrape
```

**Reviews**
```
GET /reviews           — filterable by business_id, rating, processed
GET /reviews/analytics — rating distribution + reply stats
```

**Replies**
```
GET  /reply/{review_id}           — all versions for a review
POST /reply/approve               — approve (optionally with edited text)
POST /reply/reject
POST /reply/{review_id}/regenerate
```

---

## Database Schema

```sql
users        — id, email, password_hash, full_name, created_at
businesses   — id, user_id FK, business_name, google_maps_url, description
reviews      — id, business_id FK, reviewer_name, review_text, rating, review_date, processed
ai_replies   — id, review_id FK, reply_text, status [pending|approved|rejected], created_at, updated_at
```

---

## Project Structure

```
ai-review-manager/
├── backend/app/
│   ├── api/          # auth · business · reviews · replies
│   ├── core/         # config · db · security · deps
│   ├── models/       # pydantic schemas
│   └── services/     # apify · groq · scheduler
├── frontend/src/
│   ├── app/          # auth/ · dashboard/
│   ├── components/   # Sidebar · StarRating · StatusBadge
│   ├── lib/          # axios client · auth helpers
│   └── types/
└── database/
    └── schema.sql    # tables + RLS policies
```

---

## Roadmap

- [ ] Google Business Profile API — post approved replies directly (no copy-paste)
- [ ] Slack / email alerts on new 1-star reviews
- [ ] Per-business tone and style templates
- [ ] Sentiment categorization by topic (service / price / staff)
- [ ] Multi-language detection + reply in reviewer's language
- [ ] White-label mode for agencies
- [ ] Stripe billing (per-business tiers)

---

## Contributing

```bash
git checkout -b feature/your-feature
git commit -m 'feat: your feature'
git push origin feature/your-feature
# open a PR
```

Follow [Conventional Commits](https://www.conventionalcommits.org/). PRs welcome.

---

## License

MIT © 2025 AI Review Manager Contributors

---

<div align="center">
Built with FastAPI · Next.js · Supabase · Groq · Apify
</div>
