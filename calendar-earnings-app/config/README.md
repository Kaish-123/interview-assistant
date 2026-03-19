# Config

1. **Get Google OAuth credentials**
   - Open: https://console.cloud.google.com/apis/credentials
   - Create project (or pick one) → **Enable API** → **Google Calendar API**
   - **Create credentials** → **OAuth client ID**
   - Application type: **Desktop app** (or Web application; if Web, add redirect URI `http://localhost:3000/`)
   - Download JSON

2. **Save as credentials.json**
   - Rename the downloaded file to **`credentials.json`**
   - Put it in this folder: `calendar-earnings-app/config/credentials.json`

3. **Dashboard**
   - Run `npm run dev` and open http://localhost:3000
   - Click **Connect Google (OAuth)** → sign in → done

`tokens.json` will be created automatically after you connect.
