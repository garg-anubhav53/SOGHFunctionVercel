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
