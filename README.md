# StudyZee - The Ultimate Student Hub 🎓

StudyZee is a **one-stop platform** designed to help students manage their coursework, track deadlines, collaborate with peers, and explore academic events—all in one place! Built at **Hacked 2025**, this project integrates powerful tools to enhance student productivity and networking.

## ✨ Features

### 📚 Course & Assignment Management
- Upload and organize **course materials** (eClass integration)
- Track **assignment deadlines** with AI-powered reminders (OpenAI-powered)
- Monitor **grade weightage and progress**

### 🏫 Smart Social Connections
- Connect with students based on **courses, academic goals, and year of study**
- Make friends and network like on **Discord**
- Join and create **study groups** for collaborative learning

### 💬 Real-Time Collaboration
- **Private chats & group messaging** for seamless discussions
- **WebSockets-powered real-time messaging**
- Automatic chat room creation upon accepted friend requests

### 📝 Smart Notes & Flashcards
- Upload your **notes and documents**
- AI-powered **flashcard generation** for easy revision

### 🎟️ Event Discovery
- Explore **university events** tailored to your academic and social interests
- Connect with like-minded students through shared events

## 🔧 Tech Stack
- **Frontend:** HTML, CSS
- **Backend:** Flask (Python)
- **Database:** Supabase (PostgreSQL)
- **Authentication:** Flask-Login with a custom SQL user table
- **File Storage:** Supabase Storage
- **Real-Time Features:** WebSockets for chat and notifications

## 🚀 Getting Started

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/studyzee.git
cd studyzee
```

### 2️⃣ Set Up a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   # On Windows use: venv\Scripts\activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Set Up Environment Variables
Create a `.env` file and add the necessary Supabase credentials:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_api_key
```

### 5️⃣ Run the Application
```bash
python3 app.py
```
Visit `http://127.0.0.1:5000/` in your browser.

## 🎯 Future Roadmap
- 📱 **Mobile App Version**
- 🤖 **AI-Powered Study Assistance** (personalized recommendations)
- 📞 **Video Call Functionality** for virtual study sessions
- 🎮 **Gamification & Productivity Tracking**
- 🏫 **Integration with Google Drive, Notion, and Canvas**

## 🙌 Contributors
- **Gunkirat Singh** 
- **Jashanveer Singh Arora** 
- **Gurmanpreet Singh Tiwana** 

## 💡 Acknowledgments
Special thanks to **Hacked 2025**, and our amazing teammates for making this project a reality! 🚀

---
**Made with ❤️ at Hacked 2025**
