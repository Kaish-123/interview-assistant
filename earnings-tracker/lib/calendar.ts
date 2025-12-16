import { google, calendar_v3 } from 'googleapis'
import { OAuth2Client } from 'google-auth-library'
import fs from 'fs'
import path from 'path'

const CREDENTIALS_PATH = path.join(process.cwd(), 'credentials.json')
const TOKEN_PATH = path.join(process.cwd(), 'token.json')

const SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

export interface CalendarEvent {
  id: string
  title: string
  date: string
  startTime: string | null
  endTime: string | null
  durationMinutes: number | null
}

/**
 * Load or create OAuth2 client
 */
export async function getOAuth2Client(): Promise<OAuth2Client | null> {
  try {
    if (!fs.existsSync(CREDENTIALS_PATH)) {
      console.error('credentials.json not found')
      return null
    }

    const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf-8'))
    const { client_id, client_secret, redirect_uris } = credentials.installed || credentials.web

    const oauth2Client = new google.auth.OAuth2(
      client_id,
      client_secret,
      redirect_uris[0]
    )

    // Check if we have a saved token
    if (fs.existsSync(TOKEN_PATH)) {
      const token = JSON.parse(fs.readFileSync(TOKEN_PATH, 'utf-8'))
      oauth2Client.setCredentials(token)
      return oauth2Client
    }

    return oauth2Client
  } catch (error) {
    console.error('Error loading OAuth2 client:', error)
    return null
  }
}

/**
 * Check if user is authenticated
 */
export async function isAuthenticated(): Promise<boolean> {
  if (!fs.existsSync(TOKEN_PATH)) {
    return false
  }
  
  try {
    const token = JSON.parse(fs.readFileSync(TOKEN_PATH, 'utf-8'))
    return !!token.access_token
  } catch {
    return false
  }
}

/**
 * Get authentication URL for OAuth flow
 */
export async function getAuthUrl(): Promise<string | null> {
  const client = await getOAuth2Client()
  if (!client) return null

  return client.generateAuthUrl({
    access_type: 'offline',
    scope: SCOPES,
    prompt: 'consent'
  })
}

/**
 * Exchange auth code for tokens
 */
export async function exchangeCodeForTokens(code: string): Promise<boolean> {
  try {
    const client = await getOAuth2Client()
    if (!client) return false

    const { tokens } = await client.getToken(code)
    client.setCredentials(tokens)

    // Save tokens for future use
    fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokens))
    return true
  } catch (error) {
    console.error('Error exchanging code for tokens:', error)
    return false
  }
}

/**
 * Fetch calendar events
 */
export async function fetchCalendarEvents(
  timeMin?: Date,
  timeMax?: Date,
  syncToken?: string | null
): Promise<{ events: CalendarEvent[]; nextSyncToken: string | null }> {
  const client = await getOAuth2Client()
  if (!client) {
    throw new Error('Not authenticated')
  }

  const calendar = google.calendar({ version: 'v3', auth: client })

  const params: calendar_v3.Params$Resource$Events$List = {
    calendarId: 'primary',
    singleEvents: true,
    orderBy: 'startTime',
  }

  // Use sync token for incremental sync if available
  if (syncToken) {
    params.syncToken = syncToken
  } else {
    // Default to last 30 days if no sync token
    params.timeMin = timeMin?.toISOString() || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString()
    params.timeMax = timeMax?.toISOString() || new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
    params.maxResults = 500
  }

  const events: CalendarEvent[] = []
  let nextPageToken: string | undefined
  let nextSyncToken: string | null = null

  do {
    if (nextPageToken) {
      params.pageToken = nextPageToken
    }

    const response = await calendar.events.list(params)
    
    if (response.data.items) {
      for (const event of response.data.items) {
        if (event.status === 'cancelled') continue
        if (!event.summary) continue

        const startDateTime = event.start?.dateTime || event.start?.date
        const endDateTime = event.end?.dateTime || event.end?.date

        if (!startDateTime) continue

        let durationMinutes: number | null = null
        let startTime: string | null = null
        let endTime: string | null = null
        let date: string

        if (event.start?.dateTime) {
          const start = new Date(event.start.dateTime)
          const end = event.end?.dateTime ? new Date(event.end.dateTime) : null
          
          date = start.toISOString().split('T')[0]
          startTime = start.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
          
          if (end) {
            endTime = end.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
            durationMinutes = Math.round((end.getTime() - start.getTime()) / 60000)
          }
        } else {
          // All-day event
          date = event.start?.date || ''
        }

        events.push({
          id: event.id || '',
          title: event.summary || '',
          date,
          startTime,
          endTime,
          durationMinutes
        })
      }
    }

    nextPageToken = response.data.nextPageToken || undefined
    nextSyncToken = response.data.nextSyncToken || null

  } while (nextPageToken)

  return { events, nextSyncToken }
}

/**
 * Get events for a specific date range
 */
export async function getEventsForDateRange(startDate: Date, endDate: Date): Promise<CalendarEvent[]> {
  const { events } = await fetchCalendarEvents(startDate, endDate, null)
  return events
}

