import { NextResponse } from 'next/server'
import { fetchCalendarEvents } from '@/lib/calendar'
import { 
  getAllClients, 
  addEarning, 
  getDefaultRate, 
  getExcludeKeywords,
  getSyncToken,
  setSyncToken
} from '@/lib/db'
import { matchClient, shouldExcludeEvent, extractClientName } from '@/lib/matcher'

export async function POST() {
  try {
    const clients = getAllClients()
    const defaultRate = getDefaultRate()
    const excludeKeywords = getExcludeKeywords()
    const syncToken = getSyncToken()

    // Fetch events from Google Calendar
    const { events, nextSyncToken } = await fetchCalendarEvents(
      undefined,
      undefined,
      syncToken
    )

    let processedCount = 0
    let skippedCount = 0

    for (const event of events) {
      // Skip excluded events (internal meetings, etc.)
      if (shouldExcludeEvent(event.title, excludeKeywords)) {
        skippedCount++
        continue
      }

      // Match client and get rate
      const match = matchClient(event.title, clients, defaultRate)
      const clientName = match.client?.name || extractClientName(event.title, clients)

      // Add to earnings
      addEarning({
        event_id: event.id,
        event_title: event.title,
        client_name: clientName,
        date: event.date,
        start_time: event.startTime,
        end_time: event.endTime,
        duration_minutes: event.durationMinutes,
        rate: match.rate,
        is_custom_client: match.matched ? 1 : 0,
        payment_status: match.paymentStatus,
        notes: null
      })

      processedCount++
    }

    // Save sync token for incremental updates
    if (nextSyncToken) {
      setSyncToken(nextSyncToken)
    }

    return NextResponse.json({
      success: true,
      eventsProcessed: processedCount,
      eventsSkipped: skippedCount,
      totalEvents: events.length
    })
  } catch (error: any) {
    console.error('Error syncing calendar:', error)
    
    // Check if it's an auth error
    if (error.message?.includes('Not authenticated') || error.code === 401) {
      return NextResponse.json({ 
        error: 'Not authenticated. Please connect your Google Calendar first.',
        needsAuth: true 
      }, { status: 401 })
    }

    // Check if sync token is invalid (need full sync)
    if (error.code === 410) {
      // Clear sync token and retry
      setSyncToken('')
      return NextResponse.json({ 
        error: 'Sync token expired. Please try again.',
        retryNeeded: true 
      }, { status: 410 })
    }

    return NextResponse.json({ error: 'Failed to sync calendar' }, { status: 500 })
  }
}

