# PickRank – Claude Code Project Instructions
## Project Overview
PickRank is a SaaS platform that automatically analyzes finance podcasts and YouTube channels, extracts stock recommendations via NLP, tracks their historical performance against benchmarks, and ranks creators by measurable accuracy. Target market: retail investors in DACH.
**Vision:** The Bloomberg Terminal for retail financial content consumers.
---
## Tech Stack
| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, FastAPI |
| Database | PostgreSQL (Supabase) |
| Cache | Redis (optional, post-MVP) |
| Async Jobs | Celery or FastAPI BackgroundTasks |
| AI/NLP | OpenAI API (classification), spaCy (entity recognition) |
| Market Data | Polygon.io or Alpha Vantage API |
| Frontend | Next.js, Tailwind CSS |
| Hosting | Vercel (Frontend), Supabase or AWS (Backend + DB) |
| Email | SendGrid |
| Monitoring | Sentry (errors), structured logging |
---
## Project Structure
```
pickrank/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Environment & settings
│   │   ├── models/                 # SQLAlchemy / Pydantic models
│   │   │   ├── creator.py
│   │   │   ├── episode.py
│   │   │   ├── recommendation.py
│   │   │   ├── performance.py
│   │   │   └── creator_score.py
│   │   ├── api/                    # API route handlers
│   │   │   ├── creators.py
│   │   │   ├── recommendations.py
│   │   │   ├── ranking.py
│   │   │   └── subscriptions.py
│   │   ├── services/               # Business logic
│   │   │   ├── ingestion.py        # RSS + YouTube API fetching
│   │   │   ├── transcription.py    # Transcript retrieval + Whisper fallback
│   │   │   ├── nlp_extraction.py   # Ticker detection, classification
│   │   │   ├── market_data.py      # Price fetching + caching
│   │   │   ├── scoring.py          # Return calculation + scoring
│   │   │   └── email_alerts.py     # SendGrid integration
│   │   ├── tasks/                  # Background / scheduled jobs
│   │   │   └── cron.py             # 6-hour ingestion cycle
│   │   └── utils/
│   │       └── helpers.py
│   ├── tests/
│   │   ├── test_scoring.py
│   │   ├── test_ingestion.py
│   │   └── test_nlp.py
│   ├── alembic/                    # DB migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                    # Next.js App Router
│   │   │   ├── page.tsx            # Ranking overview
│   │   │   ├── creators/
│   │   │   │   └── [id]/page.tsx   # Creator detail
│   │   │   └── recommendations/
│   │   │       └── page.tsx        # Recent recommendations
│   │   ├── components/
│   │   └── lib/
│   ├── tailwind.config.ts
│   ├── package.json
│   └── next.config.js
├── claude.md                       # This file
├── docker-compose.yml
├── .env.example
└── README.md
```
---
## Data Model
### creators
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR | Creator name |
| platform | VARCHAR | youtube / podcast |
| rss_url | VARCHAR | RSS feed URL |
| youtube_channel_id | VARCHAR | YouTube channel ID |
| language | VARCHAR | de / en |
| created_at | TIMESTAMP | |
### episodes
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| creator_id | UUID | FK → creators |
| title | VARCHAR | Episode title |
| publish_date | DATE | Publication date |
| transcript | TEXT | Full transcript |
| source_url | VARCHAR | Original URL |
| processed | BOOLEAN | NLP processing done |
| created_at | TIMESTAMP | |
### recommendations
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| episode_id | UUID | FK → episodes |
| ticker | VARCHAR | Stock ticker (e.g. AAPL) |
| company_name | VARCHAR | Resolved company name |
| type | ENUM | BUY / HOLD / SELL |
| confidence | FLOAT | 0.0–1.0 |
| sentence | TEXT | Source sentence from transcript |
| recommendation_date | DATE | Date of the recommendation |
| created_at | TIMESTAMP | |
### performance
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| recommendation_id | UUID | FK → recommendations |
| price_at_recommendation | FLOAT | Price at t0 |
| return_1w | FLOAT | 1-week return |
| return_1m | FLOAT | 1-month return |
| return_3m | FLOAT | 3-month return |
| return_6m | FLOAT | 6-month return |
| return_12m | FLOAT | 12-month return |
| benchmark_return_1m | FLOAT | Benchmark return same period |
| benchmark_return_3m | FLOAT | |
| benchmark_return_6m | FLOAT | |
| benchmark_return_12m | FLOAT | |
| score | FLOAT | Calculated pick score |
| updated_at | TIMESTAMP | |
### creator_scores
| Column | Type | Description |
|--------|------|-------------|
| creator_id | UUID | FK → creators, PK |
| total_picks | INT | Total recommendations |
| hit_rate | FLOAT | % of positive relative returns |
| avg_outperformance | FLOAT | Average relative return |
| overall_score | FLOAT | Composite score |
| updated_at | TIMESTAMP | |
---
## Core Business Logic
### Performance Calculation
```
stock_return = (price_tX - price_t0) / price_t0
relative_return = stock_return - benchmark_return
```
Benchmarks: S&P 500 (international picks), DAX (German picks)
### Scoring Table
| Relative Return | Score |
|----------------|-------|
| > 10% | 1.0 |
| 5–10% | 0.8 |
| 0–5% | 0.6 |
| -5–0% | 0.4 |
| < -5% | 0.1 |
### Creator Aggregation
```
overall_score = (average_pick_score * 0.6) + (hit_rate * 0.4)
```
**Minimum 20 picks required** for public ranking display.
### NLP Extraction Rules
- Detect ticker symbols via regex + database validation
- Detect company names via spaCy NER
- Classify recommendation type (BUY/HOLD/SELL) via AI API
- **Confidence threshold: > 0.7** (discard below)
- Target: false positive rate < 20%
---
## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/creators | List all ranked creators |
| GET | /api/creators/{id} | Creator detail with all picks |
| GET | /api/recommendations | Recent recommendations (paginated) |
| GET | /api/ranking | Creator ranking (sorted by overall_score) |
| POST | /api/subscribe | Email subscription for alerts |
All endpoints return JSON. Use JWT authentication for protected routes.
---
## Development Phases
### Phase 1 – Infrastructure (2 weeks)
- Git repo, FastAPI scaffold, PostgreSQL setup
- Next.js frontend scaffold
- Environment config, Docker Compose
- Staging environment
### Phase 2 – NLP Extraction (3 weeks)
- YouTube API + RSS ingestion service
- Transcript retrieval + Whisper fallback
- Ticker/company detection pipeline
- AI classification integration
- Confidence filtering
### Phase 3 – Performance Engine (3 weeks)
- Market data API integration
- Return calculation across all timeframes
- Benchmark comparison logic
- Scoring engine
- Creator aggregation
### Phase 4 – Frontend (2 weeks)
- Ranking overview page
- Creator detail page
- Recent recommendations page
- Email subscription form
- Loading states, error handling
### Phase 5 – Testing & Launch (2 weeks)
- Unit tests (scoring engine)
- Integration tests (ingestion pipeline)
- Manual validation of 100 recommendations
- Load testing (dashboard < 2s)
- Legal disclaimer
- Monitoring setup (Sentry, structured logs)
- Production deployment
---
## Non-Functional Requirements
- **Performance:** Dashboard loads < 2s, episode processing < 15 min
- **Security:** HTTPS, JWT auth, bcrypt passwords, RBAC (admin/user), no financial account data stored
- **Compliance:** Clear legal disclaimer – "No investment advice"
- **Logging:** Structured JSON logs, Sentry error tracking
- **Cron:** Ingestion runs every 6 hours
---
## Business Model
**Freemium:**
- Free: Limited ranking access
- Paid (15–25 CHF/month): Full analytics, alerts, detailed performance data
**Future:** B2B API, white-label for banks, creator performance analytics
---
## MVP Launch Criteria
- [ ] 20+ creators live in system
- [ ] 1,000+ recommendations processed
- [ ] Stable ranking calculation
- [ ] Functional email alerts
- [ ] Legal disclaimer implemented
- [ ] Dashboard loads < 2 seconds
---
## Coding Conventions
- **Python:** Follow PEP 8, type hints everywhere, async where possible
- **Frontend:** TypeScript strict mode, functional components, Tailwind utility classes
- **Database:** Use Alembic for all migrations, never modify schema manually
- **API:** Pydantic models for request/response validation
- **Testing:** pytest for backend, meaningful test names, mock external APIs
- **Git:** Conventional commits (feat:, fix:, chore:, docs:)
- **Environment:** All secrets via .env, never commit credentials
- **Error handling:** Structured error responses, proper HTTP status codes
- **Language:** Code and comments in English, user-facing content in German (DACH market)
