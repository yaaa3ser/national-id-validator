-- Initialize the database with proper settings
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_keys_key ON authentication_apikey(key);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_keys_user_id ON authentication_apikey(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_call_logs_timestamp ON usage_tracking_apicalllog(timestamp);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_call_logs_api_key ON usage_tracking_apicalllog(api_key_id);

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE national_id_db TO postgres;
