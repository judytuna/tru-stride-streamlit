# 🐎 Tru-Stride

## Using data to give your horse a voice

**AI-Powered Horse Gait Analysis Platform**

Tru-Stride is a comprehensive web application that uses artificial intelligence to analyze horse gaits from video uploads. The platform provides detailed stride analysis, quality scoring, and user management features for equestrians, veterinarians, and horse trainers.

## ✨ Features

### 🔍 AI-Powered Gait Analysis
- **Video Upload & Processing**: Support for MP4, AVI, MOV, and MKV video formats
- **Real-time Analysis**: Powered by HuggingFace Gradio integration
- **Comprehensive Metrics**:
  - Stride classification (Normal/Abnormal)
  - Confidence scoring
  - Stride variability measurement
  - Mean knee angle analysis
  - Body length variation assessment
  - Quality scores for rhythm and symmetry

### 👥 User Management
- **Supabase Authentication**: Secure email/password authentication with built-in email verification
- **User Registration**: Easy signup with automatic profile creation
- **Admin Dashboard**: User management and analytics for administrators
- **Session Persistence**: Stay logged in across page refreshes

### 📊 Analytics & Visualization
- **Interactive Charts**: Plotly-powered visualizations
- **Performance Metrics**: Detailed stride quality scoring (1-10 scale)
- **Historical Tracking**: Analysis history and trends
- **Admin Analytics**: User activity and upload statistics

### 🗄️ Data Management
- **Supabase Database**: PostgreSQL cloud database with Row Level Security (RLS)
- **Video Storage**: Supabase Storage for secure video file management
- **Video Playback**: Built-in video player with signed URL security
- **Persistent Storage**: Data and videos survive app restarts and deployments
- **Real-time Sync**: Instant updates across user sessions
- **Automatic Backups**: Built-in backup and recovery via Supabase

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Streamlit
- Supabase account (free tier available)
- Access to HuggingFace Gradio Space (judytuna/tru-stride-analyzer)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tru-stride-streamlit
   ```

2. **Set up Supabase**
   - Follow the detailed setup guide in `SUPABASE_SETUP.md`
   - Create your Supabase project and database tables
   - Configure video storage bucket and RLS policies
   - Get your project URL and API keys

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   export SUPABASE_URL="https://your-project.supabase.co"
   export SUPABASE_ANON_KEY="your-anon-key-here"
   ```

5. **Run the application**
   ```bash
   streamlit run streamlit_app.py
   ```

6. **Access the app**
   - Open your browser to `http://localhost:8501`
   - Sign up for a new user account to get started

## 🔧 Configuration

### Environment Variables
Required for Supabase integration:

```bash
# Supabase credentials (required)
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key-here"
```

### Database
The application uses Supabase PostgreSQL with:
- **Row Level Security (RLS)**: Users can only access their own data
- **Admin privileges**: Admins can view all user data and analytics
- **Automatic profile creation**: User profiles created on signup via database triggers

### Streamlit Cloud
Active at https://tru-stride.streamlit.app/

## 📋 Usage

### For Regular Users
1. **Sign Up**: Create an account with username, email, and password
2. **Upload Video**: Select a clear video showing your horse's gait
3. **Analyze**: Click "Analyze Gait" to process the video and store it securely
4. **Review Results**: View detailed analysis including:
   - Stride classification and confidence
   - Quality metrics and scores
   - Historical comparisons
5. **Video Library**: Access your uploaded videos anytime in "My Videos" with playback capability

### For Administrators
- **User Management**: Promote/demote admin privileges
- **Analytics Dashboard**: View platform usage statistics
- **System Overview**: Monitor total users, videos, and trends

## 🔬 Technical Details

### Architecture
- **Frontend**: Streamlit web application with custom theming
- **Backend**: Python with Supabase PostgreSQL database
- **Video Storage**: Supabase Storage with secure file management
- **Authentication**: Supabase Auth with email verification
- **AI Model**: HuggingFace Gradio Space integration
- **Visualization**: Plotly for interactive charts and analytics
- **Security**: Row Level Security (RLS) policies for data and video isolation

### AI Integration
The application connects to a HuggingFace Gradio Space (`judytuna/tru-stride-analyzer`) that provides:
- Video processing capabilities
- Stride analysis algorithms
- Classification models (Normal/Abnormal gait patterns)
- Detailed metric extraction

### Database Schema

#### Supabase Tables
- **profiles**: id (UUID), username, is_admin, created_at
  - Extends Supabase's built-in `auth.users` table
  - Automatic creation via database triggers
- **videos**: id, user_id (UUID), filename, upload_date, analysis_results (JSONB), file_path (TEXT)
  - file_path stores Supabase Storage location for video playback

#### Supabase Storage
- **videos bucket**: Secure video file storage with user-specific folders
- **File organization**: `{user_id}/{filename.mp4}` structure
- **Signed URLs**: Time-limited (1 hour) secure video access for playback

#### Security Policies
- Users can only access their own profiles and videos (database and storage)
- Video storage RLS ensures users can only access files in their own folders
- Admins have read access to all data for analytics
- Email verification required for new accounts

## 📊 Metrics Explained

### Quality Scores
- **Rhythm Score (0-10)**: Based on stride variability (lower variability = higher score)
- **Symmetry Score (0-10)**: Based on body length variation (lower variation = higher score)
- **Overall Score**: Average of rhythm and symmetry scores

### Analysis Parameters
- **Stride Variability**: Consistency of stride patterns
- **Mean Knee Angle**: Average knee flexion during movement
- **Body Length Variation**: Changes in body posture during stride
- **Processing Time**: AI model analysis duration

## 🛠️ Dependencies

```
streamlit          # Web application framework
pandas             # Data manipulation and analysis
plotly             # Interactive visualizations
gradio_client      # HuggingFace Gradio integration
supabase>=1.0.0    # Database, authentication, and video storage
```

## 🎨 Features Added

### Professional Branding
- Custom logo integration (Tru-Stride logo)
- Themed color scheme (gold accents, neutral background)
- Favicon support
- Open Graph meta tags for social media previews

### Enhanced UI/UX
- Upload trends analytics with daily breakdowns
- Improved chart visibility with markers for single data points
- Integer-only axes for count-based metrics
- Session persistence across page refreshes
- Streamlined logout functionality

### Video Management
- **Persistent Video Storage**: Videos automatically saved to Supabase Storage during analysis
- **Secure Video Playback**: Built-in HTML5 video player with time-limited signed URLs
- **User-specific Storage**: Videos organized in user folders with RLS security
- **Video Library**: "My Videos" dashboard for accessing all uploaded videos with analysis results

## 📈 Roadmap

- [ ] Advanced filtering and search capabilities
- [ ] Export analysis reports (PDF/CSV)
- [ ] Video comparison features
- [ ] Mobile application support
- [ ] Integration with additional AI models

## 📄 License

TBD

## 📞 Support

For questions or support, please contact the development team or open an issue in the repository.

---

**Tru-Stride** - Advancing equine health through AI-powered gait analysis.
