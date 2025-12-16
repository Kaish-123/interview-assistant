'use client'

import { useEffect, useState } from 'react'
import { Calendar, ChevronLeft, ChevronRight, CheckCircle2, Clock, Filter } from 'lucide-react'

interface Earning {
  id: number
  event_id: string
  event_title: string
  client_name: string | null
  date: string
  start_time: string | null
  end_time: string | null
  duration_minutes: number | null
  rate: number
  is_custom_client: number
  payment_status: string
  notes: string | null
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(amount)
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-IN', { 
    weekday: 'short',
    day: 'numeric', 
    month: 'short',
    year: 'numeric'
  })
}

export default function EarningsPage() {
  const [earnings, setEarnings] = useState<Earning[]>([])
  const [loading, setLoading] = useState(true)
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [filter, setFilter] = useState<'all' | 'pending' | 'paid'>('all')
  const [selectedDate, setSelectedDate] = useState<string | null>(null)

  useEffect(() => {
    fetchEarnings()
  }, [currentMonth])

  const fetchEarnings = async () => {
    setLoading(true)
    try {
      const year = currentMonth.getFullYear()
      const month = currentMonth.getMonth() + 1
      const startDate = `${year}-${String(month).padStart(2, '0')}-01`
      const endDate = `${year}-${String(month).padStart(2, '0')}-31`
      
      const res = await fetch(`/api/earnings?type=range&startDate=${startDate}&endDate=${endDate}`)
      const data = await res.json()
      setEarnings(data.earnings || [])
    } catch (error) {
      console.error('Error fetching earnings:', error)
    } finally {
      setLoading(false)
    }
  }

  const updatePaymentStatus = async (id: number, status: string) => {
    try {
      await fetch('/api/earnings', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, paymentStatus: status })
      })
      fetchEarnings()
    } catch (error) {
      console.error('Error updating payment status:', error)
    }
  }

  const prevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))
  }

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))
  }

  const filteredEarnings = earnings.filter(e => {
    if (filter === 'pending') return e.payment_status === 'pending'
    if (filter === 'paid') return e.payment_status === 'paid'
    if (selectedDate) return e.date === selectedDate
    return true
  })

  const totalAmount = filteredEarnings.reduce((sum, e) => sum + e.rate, 0)
  const pendingAmount = filteredEarnings
    .filter(e => e.payment_status === 'pending')
    .reduce((sum, e) => sum + e.rate, 0)

  // Group earnings by date
  const earningsByDate = filteredEarnings.reduce((acc, earning) => {
    if (!acc[earning.date]) {
      acc[earning.date] = []
    }
    acc[earning.date].push(earning)
    return acc
  }, {} as Record<string, Earning[]>)

  const sortedDates = Object.keys(earningsByDate).sort((a, b) => 
    new Date(b).getTime() - new Date(a).getTime()
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-8">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
            Earnings Log
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Detailed record of all interviews
          </p>
        </div>
      </div>

      {/* Month Selector & Summary */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <button 
              onClick={prevMonth}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              <ChevronLeft size={20} />
            </button>
            <div className="flex items-center gap-2">
              <Calendar size={20} className="text-primary" />
              <span className="text-lg font-semibold text-gray-900 dark:text-white">
                {currentMonth.toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })}
              </span>
            </div>
            <button 
              onClick={nextMonth}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              <ChevronRight size={20} />
            </button>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm text-gray-500 dark:text-gray-400">Total</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">
                {formatCurrency(totalAmount)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500 dark:text-gray-400">Pending</p>
              <p className="text-xl font-bold text-orange-500">
                {formatCurrency(pendingAmount)}
              </p>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 mt-4 pt-4 border-t dark:border-gray-700">
          <Filter size={16} className="text-gray-400" />
          <div className="flex gap-2">
            {(['all', 'pending', 'paid'] as const).map((f) => (
              <button
                key={f}
                onClick={() => { setFilter(f); setSelectedDate(null); }}
                className={`px-3 py-1 rounded-full text-sm capitalize transition-colors ${
                  filter === f
                    ? 'bg-primary text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
          {selectedDate && (
            <button
              onClick={() => setSelectedDate(null)}
              className="ml-2 px-3 py-1 rounded-full text-sm bg-red-100 text-red-600 hover:bg-red-200"
            >
              Clear date filter
            </button>
          )}
        </div>
      </div>

      {/* Earnings Table */}
      {sortedDates.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-sm text-center text-gray-500">
          <p className="text-lg">No earnings found for this month</p>
          <p className="text-sm mt-1">Sync your calendar to see earnings</p>
        </div>
      ) : (
        <div className="space-y-4">
          {sortedDates.map((date) => {
            const dayEarnings = earningsByDate[date]
            const dayTotal = dayEarnings.reduce((sum, e) => sum + e.rate, 0)
            
            return (
              <div key={date} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden">
                {/* Date Header */}
                <div 
                  className="bg-gray-50 dark:bg-gray-900 px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                  onClick={() => setSelectedDate(selectedDate === date ? null : date)}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <span className="text-primary font-bold">
                        {new Date(date).getDate()}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {formatDate(date)}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {dayEarnings.length} interview{dayEarnings.length > 1 ? 's' : ''}
                      </p>
                    </div>
                  </div>
                  <span className="font-bold text-lg text-green-600 dark:text-green-400">
                    {formatCurrency(dayTotal)}
                  </span>
                </div>

                {/* Day's Earnings */}
                <div className="divide-y dark:divide-gray-700">
                  {dayEarnings.map((earning) => (
                    <div 
                      key={earning.id}
                      className="px-4 py-3 flex flex-col md:flex-row md:items-center justify-between gap-2"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900 dark:text-white">
                            {earning.client_name || 'Unknown'}
                          </span>
                          {earning.is_custom_client === 1 && (
                            <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded-full">
                              Custom
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {earning.event_title}
                        </p>
                        {earning.start_time && (
                          <p className="text-xs text-gray-400 mt-1">
                            {earning.start_time} - {earning.end_time}
                            {earning.duration_minutes && ` (${earning.duration_minutes} min)`}
                          </p>
                        )}
                      </div>

                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => updatePaymentStatus(
                            earning.id, 
                            earning.payment_status === 'paid' ? 'pending' : 'paid'
                          )}
                          className={`flex items-center gap-1 px-3 py-1 rounded-full text-sm transition-colors ${
                            earning.payment_status === 'paid'
                              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                              : 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'
                          }`}
                        >
                          {earning.payment_status === 'paid' ? (
                            <>
                              <CheckCircle2 size={14} />
                              Paid
                            </>
                          ) : (
                            <>
                              <Clock size={14} />
                              Pending
                            </>
                          )}
                        </button>
                        <span className="font-semibold text-gray-900 dark:text-white min-w-[80px] text-right">
                          {formatCurrency(earning.rate)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

