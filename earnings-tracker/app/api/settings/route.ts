import { NextRequest, NextResponse } from 'next/server'
import { getSetting, setSetting, getDefaultRate, getExcludeKeywords } from '@/lib/db'

export async function GET() {
  try {
    const defaultRate = getDefaultRate()
    const excludeKeywords = getExcludeKeywords()
    
    return NextResponse.json({
      defaultRate,
      excludeKeywords
    })
  } catch (error) {
    console.error('Error fetching settings:', error)
    return NextResponse.json({ error: 'Failed to fetch settings' }, { status: 500 })
  }
}

export async function PUT(request: NextRequest) {
  try {
    const body = await request.json()
    const { defaultRate, excludeKeywords } = body

    if (defaultRate !== undefined) {
      setSetting('default_rate', String(defaultRate))
    }

    if (excludeKeywords !== undefined) {
      setSetting('exclude_keywords', JSON.stringify(excludeKeywords))
    }

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error updating settings:', error)
    return NextResponse.json({ error: 'Failed to update settings' }, { status: 500 })
  }
}

