import { NextRequest, NextResponse } from 'next/server'
import { getAuthUrl, exchangeCodeForTokens, isAuthenticated } from '@/lib/calendar'

export async function GET() {
  try {
    const authenticated = await isAuthenticated()
    
    if (authenticated) {
      return NextResponse.json({ authenticated: true })
    }

    const authUrl = await getAuthUrl()
    return NextResponse.json({ 
      authenticated: false, 
      authUrl 
    })
  } catch (error) {
    console.error('Error checking auth status:', error)
    return NextResponse.json({ error: 'Failed to check auth status' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { code } = body

    if (!code) {
      return NextResponse.json({ error: 'Authorization code is required' }, { status: 400 })
    }

    const success = await exchangeCodeForTokens(code)
    
    if (success) {
      return NextResponse.json({ success: true })
    } else {
      return NextResponse.json({ error: 'Failed to exchange code for tokens' }, { status: 400 })
    }
  } catch (error) {
    console.error('Error exchanging code:', error)
    return NextResponse.json({ error: 'Authentication failed' }, { status: 500 })
  }
}

