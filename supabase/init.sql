-- Table to store Stack Overflow profile URLs
CREATE TABLE stackoverflow_profiles (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Table to track scraping progress
CREATE TABLE scraping_progress (
    id SERIAL PRIMARY KEY,
    current_index INTEGER DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Table to store processed URLs for tracking
CREATE TABLE processed_urls (
    id SERIAL PRIMARY KEY,
    stackoverflow_url TEXT NOT NULL,
    batch_index INTEGER NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    UNIQUE(stackoverflow_url)
);

-- Table to store GitHub profile data
CREATE TABLE github_profiles (
    id SERIAL PRIMARY KEY,
    stackoverflow_url TEXT NOT NULL,
    github_url TEXT NOT NULL,
    stackoverflow_description TEXT,
    stackoverflow_profile_text TEXT,
    twitter_url TEXT,
    email TEXT,
    name TEXT,
    username TEXT,
    location TEXT,
    company TEXT,
    website TEXT,
    followers TEXT,
    following TEXT,
    bio TEXT,
    contributions TEXT,
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    UNIQUE(stackoverflow_url)
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_processed_urls_url ON processed_urls (stackoverflow_url);
CREATE INDEX IF NOT EXISTS idx_stackoverflow_profiles_url ON stackoverflow_profiles (url);

-- Function to get unprocessed URLs
CREATE OR REPLACE FUNCTION get_unprocessed_urls()
RETURNS TABLE (url TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT sp.url
    FROM stackoverflow_profiles sp
    WHERE NOT EXISTS (
        SELECT 1
        FROM processed_urls pu
        WHERE pu.stackoverflow_url = sp.url
    );
END;
$$ LANGUAGE plpgsql;

-- Update processed_urls table to handle duplicates
ALTER TABLE processed_urls DROP CONSTRAINT IF EXISTS processed_urls_stackoverflow_url_key;
ALTER TABLE processed_urls ADD CONSTRAINT processed_urls_stackoverflow_url_key UNIQUE (stackoverflow_url) ON CONFLICT DO NOTHING;
