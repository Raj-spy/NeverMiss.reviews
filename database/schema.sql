-- ============================================================
-- AI Review Manager — Supabase Database Schema
-- Run this in the Supabase SQL editor to initialize the DB
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Users ───────────────────────────────────────────────────────────────────
-- Stores application users (tenants in the multi-tenant model)
CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email       TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name   TEXT DEFAULT '',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast email lookups during login
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);


-- ─── Businesses ───────────────────────────────────────────────────────────────
-- Each user can own multiple business profiles
CREATE TABLE IF NOT EXISTS businesses (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    business_name    TEXT NOT NULL,
    google_maps_url  TEXT NOT NULL,
    description      TEXT DEFAULT '',
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fetching businesses by user (multi-tenant isolation)
CREATE INDEX IF NOT EXISTS idx_businesses_user_id ON businesses(user_id);


-- ─── Reviews ─────────────────────────────────────────────────────────────────
-- Google reviews scraped via Apify
CREATE TABLE IF NOT EXISTS reviews (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id    UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    reviewer_name  TEXT,
    review_text    TEXT NOT NULL,
    rating         SMALLINT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_date    TEXT,      -- Raw date string from Apify
    processed      BOOLEAN DEFAULT FALSE,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_reviews_business_id   ON reviews(business_id);
CREATE INDEX IF NOT EXISTS idx_reviews_processed     ON reviews(processed);
CREATE INDEX IF NOT EXISTS idx_reviews_rating        ON reviews(rating);
CREATE INDEX IF NOT EXISTS idx_reviews_created_at    ON reviews(created_at DESC);


-- ─── AI Replies ───────────────────────────────────────────────────────────────
-- Claude-generated reply suggestions for each review
CREATE TABLE IF NOT EXISTS ai_replies (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    review_id   UUID NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    reply_text  TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ
);

-- Index for fetching replies by review
CREATE INDEX IF NOT EXISTS idx_ai_replies_review_id ON ai_replies(review_id);
CREATE INDEX IF NOT EXISTS idx_ai_replies_status    ON ai_replies(status);


-- ─── Row Level Security ───────────────────────────────────────────────────────
-- Enable RLS on all tables (backend uses service role key which bypasses RLS)
ALTER TABLE users      ENABLE ROW LEVEL SECURITY;
ALTER TABLE businesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews    ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_replies ENABLE ROW LEVEL SECURITY;

-- Service role policy — allows full access for our backend
CREATE POLICY "service_role_all" ON users      FOR ALL USING (true);
CREATE POLICY "service_role_all" ON businesses FOR ALL USING (true);
CREATE POLICY "service_role_all" ON reviews    FOR ALL USING (true);
CREATE POLICY "service_role_all" ON ai_replies FOR ALL USING (true);


-- ─── Sample Data (optional — remove for production) ──────────────────────────
/*
INSERT INTO users (id, email, password_hash, full_name)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'demo@example.com',
    '$2b$12$placeholderhashreplacewithrealhashedpassword',
    'Demo User'
);
*/
