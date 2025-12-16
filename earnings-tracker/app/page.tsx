'use client'

import { useEffect, useState } from 'react'
import { 
  IndianRupee, 
  Calendar, 
  Clock, 
  TrendingUp,
  AlertCircle,
  CheckCircle2
} from 'lucide-react'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'

interface DashboardStats {
  today: { total: number; count: number }
  month: { total: number; count: number }
  pending: { total: number; count: number }
  dailyEarnings: { date: string; total: number; count: number }[]
  clientBreakdown: { client_name: string; total: number; count: number }[]
}

const COLORS = ['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e', '#f97316', '#eab308']

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(amount)
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [authStatus, setAuthStatus] = useState<{ authenticated: boolean; authUrl?: string } | null>(null)

  useEffect(() => {
    fetchAuthStatus()
    fetchStats()
  }, [])

  const fetchAuthStatus = async () => {
    try {
      const res = await fetch('/api/auth')
      const data = await res.json()
      setAuthStatus(data)
    } catch (error) {
      console.error('Error fetching auth status:', error)
    }
  }

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/earnings?type=dashboard')
      const data = await res.json()
      setStats(data)
    } catch (error) {
      console.error('Error fetching stats:', error)
    } finally {
      setLoading(false)
    }
  }

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
            Dashboard
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Track your interview earnings
          </p>
        </div>
        
        {authStatus && !authStatus.authenticated && authStatus.authUrl && (
          <a
            href={authStatus.authUrl}
            className="inline-flex items-center gap-2 bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors"
          >
            <AlertCircle size={18} />
            Connect Google Calendar
          </a>
        )}
        
        {authStatus?.authenticated && (
          <div className="inline-flex items-center gap-2 text-green-600 dark:text-green-400">
            <CheckCircle2 size={18} />
            Calendar Connected
          </div>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Today's Earnings"
          value={formatCurrency(stats?.today.total || 0)}
          subtitle={`${stats?.today.count || 0} interviews`}
          icon={<IndianRupee className="text-green-500" />}
          gradient="from-green-500/10 to-emerald-500/10"
        />
        <StatsCard
          title="This Month"
          value={formatCurrency(stats?.month.total || 0)}
          subtitle={`${stats?.month.count || 0} interviews`}
          icon={<Calendar className="text-blue-500" />}
          gradient="from-blue-500/10 to-cyan-500/10"
        />
        <StatsCard
          title="Pending Payments"
          value={formatCurrency(stats?.pending.total || 0)}
          subtitle={`${stats?.pending.count || 0} pending`}
          icon={<Clock className="text-orange-500" />}
          gradient="from-orange-500/10 to-amber-500/10"
        />
        <StatsCard
          title="Avg. Per Day"
          value={formatCurrency(
            stats?.dailyEarnings.length 
              ? stats.dailyEarnings.reduce((a, b) => a + b.total, 0) / stats.dailyEarnings.length 
              : 0
          )}
          subtitle="Last 7 days"
          icon={<TrendingUp className="text-purple-500" />}
          gradient="from-purple-500/10 to-pink-500/10"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Earnings Bar Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Last 7 Days
          </h2>
          <div className="h-64">
            {stats?.dailyEarnings && stats.dailyEarnings.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats.dailyEarnings}>
                  <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={formatDate}
                    fontSize={12}
                  />
                  <YAxis 
                    tickFormatter={(value) => `₹${(value/1000).toFixed(0)}k`}
                    fontSize={12}
                  />
                  <Tooltip 
                    formatter={(value: number) => [formatCurrency(value), 'Earnings']}
                    labelFormatter={(label) => formatDate(label)}
                  />
                  <Bar 
                    dataKey="total" 
                    fill="#6366f1" 
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                No data available. Sync your calendar!
              </div>
            )}
          </div>
        </div>

        {/* Client Breakdown Pie Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Client Breakdown (This Month)
          </h2>
          <div className="h-64">
            {stats?.clientBreakdown && stats.clientBreakdown.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats.clientBreakdown}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="total"
                    nameKey="client_name"
                    label={({ client_name, percent }) => 
                      `${client_name} (${(percent * 100).toFixed(0)}%)`
                    }
                    labelLine={false}
                  >
                    {stats.clientBreakdown.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value: number) => [formatCurrency(value), 'Earnings']}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                No data available. Sync your calendar!
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Client Breakdown Table */}
      {stats?.clientBreakdown && stats.clientBreakdown.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Client Summary (This Month)
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b dark:border-gray-700">
                  <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Client</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Interviews</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Earnings</th>
                </tr>
              </thead>
              <tbody>
                {stats.clientBreakdown.map((client, index) => (
                  <tr key={index} className="border-b dark:border-gray-700 last:border-0">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        />
                        <span className="font-medium text-gray-900 dark:text-white">
                          {client.client_name}
                        </span>
                      </div>
                    </td>
                    <td className="text-right py-3 px-4 text-gray-600 dark:text-gray-300">
                      {client.count}
                    </td>
                    <td className="text-right py-3 px-4 font-semibold text-gray-900 dark:text-white">
                      {formatCurrency(client.total)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

function StatsCard({ 
  title, 
  value, 
  subtitle, 
  icon, 
  gradient 
}: { 
  title: string
  value: string
  subtitle: string
  icon: React.ReactNode
  gradient: string
}) {
  return (
    <div className={`bg-gradient-to-br ${gradient} bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm card-hover`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{value}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>
        </div>
        <div className="p-3 rounded-lg bg-white/50 dark:bg-gray-900/50">
          {icon}
        </div>
      </div>
    </div>
  )
}

