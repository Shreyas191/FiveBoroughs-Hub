# 🚅 FiveBoroughs-Hub

**The smartest way to navigate the NYC Subway.**

FiveBoroughs-Hub serves as your intelligent companion for the New York City transit system. Merging real-time data with AI-powered assistance, it provides a seamless, modern, and accessible experience for daily commuters and tourists alike.

## ✨ Features

- **🤖 AI Transit Assistant**: Ask questions like *"How do I get from Times Square to Brooklyn?"* or *"Are there delays on the Q line?"* and get instant, context-aware answers.
- **📍 Live Tracker**: Real-time visualization of train locations. Track your specific line (e.g., "N" train) or view all upcoming arrivals for a station.
- **⚡ Real-Time Service Alerts**: Instant updates on delays, planned work, and service changes directly from the MTA feed.
- **♿ Accessibility Hub**: Live status of elevators and escalators across the network to ensure a smooth journey for everyone.
- **🗺️ Interactive Map**: Detailed station map with satellite/dark mode and quick favorites.
- **🌍 Multi-Language Support**: Seamlessly toggle between English and Spanish.

## 🛠️ Tech Stack

### **Backend**
- **Python (Flask)**: Core API server.
- **MTA GTFS-Realtime**: Consumes standard Protobuf feeds for live train data.
- **LangChain**: AI orchestration for the chatbot assistant.
- **RapidFuzz**: Fuzzy matching for resilient station searching.

### **Frontend**
- **React (Vite)**: High-performance UI.
- **TailwindCSS**: Modern, responsive styling with a custom dark-mode aesthetic.
- **Leaflet (React-Leaflet)**: Interactive maps.
- **Framer Motion**: Smooth, native-feeling animations.
- **Lucide React**: Beautiful iconography.
- **Firebase**: User authentication (Login/Sign up) and favorites storage.

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 16+
- An MTA API Key (Optional for some feeds, but recommended)
- Firebase Project Credentials

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/your-username/transit-hub-ai.git
cd transit-hub-ai

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file for configuration (if using AI features)
echo "OPENAI_API_KEY=your_key_here" > .env

# Run the Flask server
python app.py
```
*Server will run at `http://localhost:5000`*

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```
*Client will run at `http://localhost:5173`*

## 📁 Project Structure

```
transit-hub-ai/
├── app.py                 # Main Flask application entry point
├── services/              # Business logic (MTA, Elevator, AI services)
├── data/                  # Static station/route JSON data
├── frontend/              # React frontend application
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Application views (Dashboard, Map, etc.)
│   │   └── services/      # API integration
└── logs/                  # Application logs
```

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---
*Built with ❤️ for NYC Commuters.*
