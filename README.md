# CSH Predict - FTC Team Performance Analysis

## Setup Instructions

### Backend (Flask)

```bash
cd backend
pip install -r requirements.txt
gunicorn -w 4 -b 0.0.0.0:5005 app:app
```

The Flask backend will run on port **5005**.

### Frontend (React)

```bash
cd frontend
npm install
npm start
```

The development server will start on port **3000** and proxy API calls to the backend.

### Building for Production

```bash
cd frontend
npm run build
```

The `build` folder will be served by Flask in production.

## Configuration

- **Backend Port**: 5005
- **Frontend Dev Port**: 3000
- **Frontend Build**: `/frontend/build` (served by Flask)
- **HAProxy URL**: predict-csh.e-uvt.ro

## Features

- 📊 Analyze FTC team performance by event
- 🎯 View ranking scores, OPR, and match statistics
- 📈 Sort and filter team data
- 🌐 Real-time data from FTC Scout API

## API Endpoints

- `GET /api/health` - Server health check
- `GET /api/event/<event_code>?season=2025` - Get event data
- `POST /api/events` - Analyze multiple events

## Running in Production

```bash
cd backend
gunicorn -w 4 -b 0.0.0.0:5005 app:app
```

The application will serve both the API and the built React frontend.
