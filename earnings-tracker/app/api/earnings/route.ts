import { NextRequest, NextResponse } from 'next/server'
import { 
  getEarningsByDateRange, 
  getEarningsForDate, 
  getDashboardStats,
  updatePaymentStatus 
} from '@/lib/db'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const type = searchParams.get('type') || 'range'
    const date = searchParams.get('date')
    const startDate = searchParams.get('startDate')
    const endDate = searchParams.get('endDate')

    if (type === 'dashboard') {
      const stats = getDashboardStats()
      return NextResponse.json(stats)
    }

    if (type === 'date' && date) {
      const earnings = getEarningsForDate(date)
      return NextResponse.json({ earnings })
    }

    if (type === 'range' && startDate && endDate) {
      const earnings = getEarningsByDateRange(startDate, endDate)
      return NextResponse.json({ earnings })
    }

    // Default: get last 30 days
    const end = new Date()
    const start = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
    const earnings = getEarningsByDateRange(
      start.toISOString().split('T')[0],
      end.toISOString().split('T')[0]
    )
    return NextResponse.json({ earnings })
  } catch (error) {
    console.error('Error fetching earnings:', error)
    return NextResponse.json({ error: 'Failed to fetch earnings' }, { status: 500 })
  }
}

export async function PATCH(request: NextRequest) {
  try {
    const body = await request.json()
    const { id, paymentStatus } = body

    if (!id || !paymentStatus) {
      return NextResponse.json({ error: 'ID and payment status are required' }, { status: 400 })
    }

    updatePaymentStatus(id, paymentStatus)
    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error updating payment status:', error)
    return NextResponse.json({ error: 'Failed to update payment status' }, { status: 500 })
  }
}

