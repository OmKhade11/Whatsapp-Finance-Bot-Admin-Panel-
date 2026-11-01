import os

# Tests must never connect to or mutate the configured Supabase project.
os.environ['SUPABASE_DB_URL'] = ''
os.environ['DATABASE_URL'] = 'sqlite:///./test-techspot.db'
