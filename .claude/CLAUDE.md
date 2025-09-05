# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
streamlit run streamlit_app.py
```

### Dependencies
```bash
pip install -r requirements.txt
```

### Key Dependencies
- `streamlit` - Web application framework
- `supabase>=1.0.0` - Database, authentication, and video storage
- `pandas` - Data manipulation
- `plotly` - Interactive visualizations
- `gradio_client` - HuggingFace Gradio integration for AI analysis

## Architecture Overview

### Application Structure
This is a single-file Streamlit application (`streamlit_app.py`) that provides AI-powered horse gait analysis with user management and video storage capabilities.

### Core Components

**Authentication & Session Management**
- Uses Supabase Auth with email verification
- Session tokens stored in `st.session_state` (not persistent across page refreshes - known Streamlit limitation)
- Row Level Security (RLS) enforced for data isolation
- Admin users bypass RLS using service role key for dashboard functions

**Database Architecture (Supabase PostgreSQL)**
- `profiles` table: User profiles extending Supabase auth.users
- `videos` table: Analysis results with `file_path` for video storage reference
- RLS policies ensure users only access their own data
- Service role key used for admin functions to bypass RLS

**Video Storage (Supabase Storage)**
- Videos stored in `videos` bucket with structure: `{user_id}/{filename}`
- Secure playback via signed URLs (1-hour expiration)
- RLS policies on storage objects match user folders
- Integration with analysis workflow - videos uploaded during gait analysis

**AI Integration**
- Connects to HuggingFace Gradio Space: `judytuna/tru-stride-analyzer`
- Processes uploaded videos for gait analysis
- Returns classification, confidence scores, and quality metrics

### Key Functions

**Video Storage Functions (lines 13-68)**
- `upload_video_to_storage()` - Uploads videos to Supabase Storage
- `get_video_url()` - Creates signed URLs for secure video playback
- `delete_video_from_storage()` - Removes videos from storage

**Authentication Functions**
- `init_supabase()` - Creates Supabase client, restores session tokens for RLS
- `authenticate_user()` - Handles login with detailed error messages
- `create_user()` - User registration with profile creation

**Database Functions**
- `get_user_videos()` - Retrieves user's videos (RLS enforced)
- `save_analysis()` - Stores analysis results with optional video file path
- Admin functions use service role client to bypass RLS

### Security Implementation

**Row Level Security (RLS)**
- Enabled on `profiles` and `videos` tables
- Users can only access their own data via `auth.uid()` policies
- Admin policies removed to prevent infinite recursion issues
- Admin dashboard uses service role key to bypass RLS entirely

**Authentication Flow**
- Email verification required for new accounts
- Tokens stored in session state for RLS functionality
- Sessions don't persist across page refreshes (Streamlit limitation)
- Cross-browser session isolation (no shared authentication state)

### Configuration Requirements

**Environment Variables (Streamlit Secrets)**
```
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key"
SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"  # Required for admin functions
```

**Database Setup**
- Follow `SUPABASE_SETUP.md` for complete database and storage configuration
- Requires both database tables and storage bucket setup
- RLS policies must be configured correctly to avoid infinite recursion

### Known Limitations

**Session Persistence**
- Sessions don't survive page refreshes due to Streamlit's session state limitations
- This is an accepted limitation - users need to re-login after refresh
- All functionality works normally within a single session

**Admin Access**
- Admin dashboard requires service role key to bypass RLS
- Regular admin users see only their own data in normal operations
- Admin functions explicitly use service role client for full data access

### Common Development Tasks

**Adding New Database Operations**
- Regular user operations: Use `init_supabase()` for RLS-enforced access
- Admin operations: Use service role client to bypass RLS
- Always handle RLS blocking as normal behavior, not errors

**Video Storage Operations**
- Videos automatically uploaded during gait analysis
- File paths stored in database `file_path` column
- Use signed URLs for secure playback (temporary access)

**Authentication Debugging**
- Session token presence indicates successful authentication
- RLS blocking regular users from admin data is normal behavior
- Admin functions should explicitly use service role key

This application successfully migrated from SQLite to Supabase, implementing full authentication, RLS security, video storage, and persistent data management while maintaining all original gait analysis functionality.