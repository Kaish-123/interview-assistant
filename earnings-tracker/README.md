# 💰 Earnings Tracker

Track your interview earnings automatically from Google Calendar.

## Features

- 📅 **Google Calendar Sync** - Automatically fetch events
- 👥 **Client Management** - Set custom rates for each client
- 📊 **Dashboard** - View daily/monthly earnings with charts
- 💵 **Payment Tracking** - Mark payments as pending/paid
- 📱 **Mobile Friendly** - Works on phone and desktop
- 🔄 **Incremental Sync** - Only fetches new events

## Quick Start

### 1. Install Dependencies

```bash
cd earnings-tracker
npm install
```

### 2. Set Up Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Google Calendar API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: **Desktop app** (or Web application for Vercel)
   - Download the JSON file
5. Rename the downloaded file to `credentials.json` and place it in the project root

### 3. Run the App

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### 4. Connect Your Calendar

1. Click "Connect Google Calendar" on the dashboard
2. Authorize the app to read your calendar
3. Click "Sync Calendar" to fetch events

## How It Works

### Client Matching

The app extracts client names from your calendar event titles:

| Calendar Event | Detected Client |
|---------------|-----------------|
| "Ram call" | Ram |
| "Ram call (Day 1/2)" | Ram |
| "Shuvani call pmt ond" | Shuvani |
| "ravi(mit)" | Ravi |

### Pricing

1. **Custom Clients**: Add clients with their specific rates
2. **Default Rate**: ₹12,500 for unrecognized clients
3. **Per Slot**: Each calendar event = 1 charge (regardless of duration)

### Payment Status

Events with these patterns are auto-detected:
- `pmt pnd` or `pmt pending` → Pending
- `pmt ond` or `pmt done` or `paid` → Paid

## Deploy to Vercel

1. Push to GitHub
2. Import to Vercel
3. Add environment variables if needed
4. For OAuth, use Web Application type and set redirect URI to your Vercel URL

## Database

Uses SQLite for simplicity. The database file (`earnings.db`) is created automatically.

## Tech Stack

- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **SQLite** - Database
- **Google Calendar API** - Calendar integration
- **Recharts** - Charts

## Screenshots

Coming soon!

---

Made with ❤️ for interview consultants

