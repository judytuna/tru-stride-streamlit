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
- **Secure Authentication**: Username/password login system with password hashing
- **User Registration**: Easy signup with email
- **Admin Dashboard**: User management and analytics for administrators
- **Personal History**: Individual user video analysis history

### 📊 Analytics & Visualization
- **Interactive Charts**: Plotly-powered visualizations
- **Performance Metrics**: Detailed stride quality scoring (1-10 scale)
- **Historical Tracking**: Analysis history and trends
- **Admin Analytics**: User activity and upload statistics

### 🗄️ Data Management
- **SQLite Database**: Lightweight, reliable data storage
- **Automatic Migrations**: Seamless database updates
- **Video Metadata**: Comprehensive analysis result storage

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Streamlit
- Access to HuggingFace Gradio Space (judytuna/tru-stride-analyzer)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tru-stride-streamlit
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Access the app**
   - Open your browser to `http://localhost:8501`
   - Sign up for a new account or login with existing credentials

## 🔧 Configuration

### Environment Variables
You can customize the admin account using environment variables:

```bash
export ADMIN_USERNAME="your_admin"
export ADMIN_PASSWORD="your_secure_password"
```

### Database
The application uses SQLite database (`horse_gait.db`) which is created automatically on first run.

## 📋 Usage

### For Regular Users
1. **Sign Up**: Create an account with username, email, and password
2. **Upload Video**: Select a clear video showing your horse's gait
3. **Analyze**: Click "Analyze Gait" to process the video
4. **Review Results**: View detailed analysis including:
   - Stride classification and confidence
   - Quality metrics and scores
   - Historical comparisons

### For Administrators
- **User Management**: Promote/demote admin privileges
- **Analytics Dashboard**: View platform usage statistics
- **System Overview**: Monitor total users, videos, and trends

## 🔬 Technical Details

### Architecture
- **Frontend**: Streamlit web application
- **Backend**: Python with SQLite database
- **AI Model**: HuggingFace Gradio Space integration
- **Visualization**: Plotly for interactive charts
- **Authentication**: SHA-256 password hashing

### AI Integration
The application connects to a HuggingFace Gradio Space (`judytuna/tru-stride-analyzer`) that provides:
- Video processing capabilities
- Stride analysis algorithms
- Classification models (Normal/Abnormal gait patterns)
- Detailed metric extraction

### Database Schema
- **Users**: id, username, email, created_at, is_admin, password_hash
- **Videos**: id, user_id, filename, upload_date, analysis_results

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
```

## 📈 Roadmap

- [ ] Advanced filtering and search capabilities
- [ ] Export analysis reports (PDF/CSV)
- [ ] Video comparison features
- [ ] Mobile application support
- [ ] Integration with additional AI models

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

TBD

## 📞 Support

For questions or support, please contact the development team or open an issue in the repository.

---

**Tru-Stride** - Advancing equine health through AI-powered gait analysis.
