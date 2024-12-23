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

-- Add hashed index for faster lookups
CREATE INDEX idx_stackoverflow_url_hash ON processed_urls USING hash (stackoverflow_url);
CREATE INDEX idx_stackoverflow_profiles_url_hash ON stackoverflow_profiles USING hash (url);

-- Add a materialized view for unprocessed URLs
CREATE MATERIALIZED VIEW unprocessed_urls AS
SELECT sp.url
FROM stackoverflow_profiles sp
LEFT JOIN processed_urls pu ON sp.url = pu.stackoverflow_url
WHERE pu.stackoverflow_url IS NULL;

-- Function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_unprocessed_urls()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY unprocessed_urls;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to refresh view when processed_urls changes
CREATE TRIGGER refresh_unprocessed_urls_trigger
AFTER INSERT OR DELETE ON processed_urls
FOR EACH STATEMENT
EXECUTE FUNCTION refresh_unprocessed_urls();
