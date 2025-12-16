import { NextRequest, NextResponse } from 'next/server'
import { exchangeCodeForTokens } from '@/lib/calendar'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const code = searchParams.get('code')
  const error = searchParams.get('error')

  if (error) {
    return NextResponse.redirect(new URL('/?auth=error&message=' + encodeURIComponent(error), request.url))
  }

  if (!code) {
    return NextResponse.redirect(new URL('/?auth=error&message=No+code+provided', request.url))
  }

  try {
    const success = await exchangeCodeForTokens(code)
    
    if (success) {
      return NextResponse.redirect(new URL('/?auth=success', request.url))
    } else {
      return NextResponse.redirect(new URL('/?auth=error&message=Token+exchange+failed', request.url))
    }
  } catch (error: any) {
    console.error('Auth callback error:', error)
    return NextResponse.redirect(new URL('/?auth=error&message=' + encodeURIComponent(error.message || 'Unknown error'), request.url))
  }
}

