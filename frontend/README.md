# NYC Transit Hub Common Frontend

This is a React + Vite application that serves as the visual interface for the NYC Transit Hub.

## Features
- **Dashboard**: Real-time service status tiles.
- **Interactive Map**: Visualize all stations and lines. Save favorites.
- **Accessibility Hub**: Check elevator/escalator status for major hubs.
- **AI Assistant**: Chat with the Transit Bot (integrated with backend).
- **Multilingual**: English and Spanish support.
- **Authentication**: Firebase Login/Signup to save favorites.

## Setup

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Environment Variables**
   Create a `.env.local` file with your Firebase config:
   ```
   VITE_FIREBASE_API_KEY=your_key
   VITE_FIREBASE_AUTH_DOMAIN=your_domain
   VITE_FIREBASE_PROJECT_ID=your_id
   ...
   ```

3. **Run Development Server**
   ```bash
   npm run dev
   ```
   The app will proxy API requests (like `/api/chat`) to `http://localhost:5000`. Ensure the Python backend is running.

## Backend
The Python Flask app in the root directory serves as the API.
Run it with:
```bash
python app.py
```
