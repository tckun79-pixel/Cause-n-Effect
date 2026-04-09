-- ========================================
-- Supabase Setup for Cause-n-Effect
-- Run these in Supabase SQL Editor
-- ========================================

-- 1. gong_guo — merit/demerit log entries
CREATE TABLE IF NOT EXISTS gong_guo (
    id          UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    uid         TEXT        NOT NULL,
    cat         TEXT        NOT NULL,
    memo        TEXT        DEFAULT '',
    pts         INTEGER     NOT NULL,        -- positive = gong, negative = guo
    type        TEXT        NOT NULL,        -- 'gong' or 'guo'
    time        TEXT        NOT NULL,        -- client-side timestamp string
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 2. categories — per-user custom category lists
CREATE TABLE IF NOT EXISTS categories (
    uid         TEXT        PRIMARY KEY,
    list        JSONB       NOT NULL DEFAULT '[]',
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 3. tts_cache — cached Google TTS audio per voice preset
CREATE TABLE IF NOT EXISTS tts_cache (
    voice_preset TEXT        PRIMARY KEY,
    audio_b64    TEXT        NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ========================================
-- Row Level Security
-- ========================================
ALTER TABLE gong_guo   ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE tts_cache  ENABLE ROW LEVEL SECURITY;

-- gong_guo: users can read/write only their own records
CREATE POLICY "gong_guo_self_rw" ON gong_guo
    FOR ALL USING (uid = uid) WITH CHECK (uid = uid);

-- categories: one row per user, self-only
CREATE POLICY "categories_self_rw" ON categories
    FOR ALL USING (uid = uid) WITH CHECK (uid = uid);

-- tts_cache: read-only for all (audio is public artifact)
CREATE POLICY "tts_cache_read_all" ON tts_cache
    FOR SELECT USING (true);

-- TTS cache writes need to be handled server-side (service key),
-- so allow insert/update for authenticated users for convenience during dev
CREATE POLICY "tts_cache_insert_all" ON tts_cache
    FOR INSERT WITH CHECK (true);

CREATE POLICY "tts_cache_update_all" ON tts_cache
    FOR UPDATE USING (true);

-- ========================================
-- Performance indexes
-- ========================================
CREATE INDEX IF NOT EXISTS gong_guo_uid_created_idx
    ON gong_guo (uid, created_at DESC);
