-- Migration to add known_participants column to bill_sessions table
-- Execute this in your Supabase SQL Editor

-- Add the known_participants column to store all participants ever added to a session
ALTER TABLE bill_sessions 
ADD COLUMN known_participants JSONB DEFAULT '[]'::jsonb;

-- Update existing records to have empty known_participants array
UPDATE bill_sessions 
SET known_participants = '[]'::jsonb 
WHERE known_participants IS NULL;

-- Add comment for documentation
COMMENT ON COLUMN bill_sessions.known_participants IS 'Array of all participants that have been added to this session across different bills';

-- Optional: Create an index for better performance if you plan to query known_participants frequently
-- CREATE INDEX idx_bill_sessions_known_participants ON bill_sessions USING GIN (known_participants);

