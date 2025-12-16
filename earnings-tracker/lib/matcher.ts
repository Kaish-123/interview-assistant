import { Client } from './db'

export interface MatchResult {
  matched: boolean
  client: Client | null
  rate: number
  paymentStatus: string
}

/**
 * Extract payment status from event title
 * "pmt pnd" or "pmt pending" = pending
 * "pmt ond" or "pmt done" or "paid" = paid
 */
export function extractPaymentStatus(title: string): string {
  const lowerTitle = title.toLowerCase()
  
  if (lowerTitle.includes('pmt ond') || lowerTitle.includes('pmt done') || lowerTitle.includes('paid')) {
    return 'paid'
  }
  if (lowerTitle.includes('pmt pnd') || lowerTitle.includes('pmt pending')) {
    return 'pending'
  }
  
  return 'pending' // default
}

/**
 * Clean event title for display
 * Remove patterns like (Day 1/2), pmt pnd, etc.
 */
export function cleanEventTitle(title: string): string {
  return title
    .replace(/\s*\(Day \d+\/\d+\)/gi, '')
    .replace(/\s*pmt\s*(pnd|ond|pending|done)/gi, '')
    .replace(/\s*\d+\s*min/gi, '')
    .replace(/\s+call$/gi, '')
    .trim()
}

/**
 * Match event title to a client
 */
export function matchClient(
  eventTitle: string,
  clients: Client[],
  defaultRate: number
): MatchResult {
  const cleanedTitle = cleanEventTitle(eventTitle).toLowerCase()
  const paymentStatus = extractPaymentStatus(eventTitle)
  
  // Try to find a matching client
  for (const client of clients) {
    const clientNameLower = client.name.toLowerCase()
    
    // Direct name match in title
    if (cleanedTitle.includes(clientNameLower) || 
        eventTitle.toLowerCase().includes(clientNameLower)) {
      return {
        matched: true,
        client,
        rate: client.rate,
        paymentStatus
      }
    }
    
    // Check additional keywords
    if (client.keywords) {
      const keywords = client.keywords.split(',').map(k => k.trim().toLowerCase())
      for (const keyword of keywords) {
        if (keyword && (cleanedTitle.includes(keyword) || eventTitle.toLowerCase().includes(keyword))) {
          return {
            matched: true,
            client,
            rate: client.rate,
            paymentStatus
          }
        }
      }
    }
  }
  
  // No match found - use default rate
  return {
    matched: false,
    client: null,
    rate: defaultRate,
    paymentStatus
  }
}

/**
 * Check if event should be excluded from billing
 */
export function shouldExcludeEvent(eventTitle: string, excludeKeywords: string[]): boolean {
  const lowerTitle = eventTitle.toLowerCase()
  
  for (const keyword of excludeKeywords) {
    if (lowerTitle.includes(keyword.toLowerCase())) {
      return true
    }
  }
  
  return false
}

/**
 * Extract client name from event title for display
 */
export function extractClientName(eventTitle: string, clients: Client[]): string | null {
  const match = matchClient(eventTitle, clients, 0)
  if (match.matched && match.client) {
    return match.client.name
  }
  
  // Try to extract name from title pattern like "Name call" or "Name"
  const cleanedTitle = cleanEventTitle(eventTitle)
  const words = cleanedTitle.split(' ')
  
  if (words.length > 0) {
    // Capitalize first letter
    return words[0].charAt(0).toUpperCase() + words[0].slice(1).toLowerCase()
  }
  
  return null
}

