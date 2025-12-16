'use client'

import { useEffect, useState } from 'react'
import { Plus, Pencil, Trash2, X, Save, IndianRupee } from 'lucide-react'

interface Client {
  id: number
  name: string
  rate: number
  keywords: string | null
}

interface Settings {
  defaultRate: number
  excludeKeywords: string[]
}

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([])
  const [settings, setSettings] = useState<Settings>({ defaultRate: 12500, excludeKeywords: [] })
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingClient, setEditingClient] = useState<Client | null>(null)
  const [formData, setFormData] = useState({ name: '', rate: '', keywords: '' })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchClients()
    fetchSettings()
  }, [])

  const fetchClients = async () => {
    try {
      const res = await fetch('/api/clients')
      const data = await res.json()
      setClients(data.clients || [])
    } catch (error) {
      console.error('Error fetching clients:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchSettings = async () => {
    try {
      const res = await fetch('/api/settings')
      const data = await res.json()
      setSettings(data)
    } catch (error) {
      console.error('Error fetching settings:', error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)

    try {
      const method = editingClient ? 'PUT' : 'POST'
      const body = editingClient 
        ? { ...formData, id: editingClient.id, rate: parseInt(formData.rate, 10) }
        : { ...formData, rate: parseInt(formData.rate, 10) }

      const res = await fetch('/api/clients', {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      if (res.ok) {
        fetchClients()
        resetForm()
      } else {
        const data = await res.json()
        alert(data.error || 'Failed to save client')
      }
    } catch (error) {
      console.error('Error saving client:', error)
      alert('Failed to save client')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this client?')) return

    try {
      const res = await fetch(`/api/clients?id=${id}`, { method: 'DELETE' })
      if (res.ok) {
        fetchClients()
      }
    } catch (error) {
      console.error('Error deleting client:', error)
    }
  }

  const handleEdit = (client: Client) => {
    setEditingClient(client)
    setFormData({
      name: client.name,
      rate: String(client.rate),
      keywords: client.keywords || ''
    })
    setShowForm(true)
  }

  const resetForm = () => {
    setShowForm(false)
    setEditingClient(null)
    setFormData({ name: '', rate: '', keywords: '' })
  }

  const updateDefaultRate = async () => {
    const newRate = prompt('Enter new default rate:', String(settings.defaultRate))
    if (!newRate) return

    try {
      await fetch('/api/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ defaultRate: parseInt(newRate, 10) })
      })
      fetchSettings()
    } catch (error) {
      console.error('Error updating default rate:', error)
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
            Clients
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Manage your client rates
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="inline-flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors"
        >
          <Plus size={18} />
          Add Client
        </button>
      </div>

      {/* Default Rate Card */}
      <div className="bg-gradient-to-r from-orange-500/10 to-amber-500/10 rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-medium text-gray-700 dark:text-gray-300">Default Rate</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Applied to clients not in your list
            </p>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-2xl font-bold text-gray-900 dark:text-white">
              ₹{settings.defaultRate.toLocaleString('en-IN')}
            </span>
            <button
              onClick={updateDefaultRate}
              className="text-primary hover:text-primary/80"
            >
              <Pencil size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* Add/Edit Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between p-4 border-b dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {editingClient ? 'Edit Client' : 'Add New Client'}
              </h2>
              <button onClick={resetForm} className="text-gray-500 hover:text-gray-700">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Client Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Ram"
                  required
                  className="w-full px-4 py-2 rounded-lg border dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Rate per Interview (₹)
                </label>
                <div className="relative">
                  <IndianRupee size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="number"
                    value={formData.rate}
                    onChange={(e) => setFormData({ ...formData, rate: e.target.value })}
                    placeholder="e.g., 10000"
                    required
                    className="w-full pl-10 pr-4 py-2 rounded-lg border dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Keywords (optional)
                </label>
                <input
                  type="text"
                  value={formData.keywords}
                  onChange={(e) => setFormData({ ...formData, keywords: e.target.value })}
                  placeholder="e.g., ram, ramesh (comma separated)"
                  className="w-full px-4 py-2 rounded-lg border dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Alternative names to match in calendar events
                </p>
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={resetForm}
                  className="flex-1 px-4 py-2 rounded-lg border dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 inline-flex items-center justify-center gap-2 bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 disabled:opacity-50"
                >
                  <Save size={18} />
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Clients List */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden">
        {clients.length === 0 ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">
            <p className="text-lg">No clients added yet</p>
            <p className="text-sm mt-1">Add your first client to get started</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Client Name</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Keywords</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Rate</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Actions</th>
                </tr>
              </thead>
              <tbody>
                {clients.map((client) => (
                  <tr key={client.id} className="border-t dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="py-3 px-4">
                      <span className="font-medium text-gray-900 dark:text-white">{client.name}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-gray-500 dark:text-gray-400 text-sm">
                        {client.keywords || '-'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="font-semibold text-green-600 dark:text-green-400">
                        ₹{client.rate.toLocaleString('en-IN')}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleEdit(client)}
                          className="p-2 text-gray-500 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors"
                        >
                          <Pencil size={16} />
                        </button>
                        <button
                          onClick={() => handleDelete(client.id)}
                          className="p-2 text-gray-500 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Info Card */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4">
        <h3 className="font-medium text-blue-800 dark:text-blue-300">How client matching works</h3>
        <ul className="mt-2 text-sm text-blue-700 dark:text-blue-400 space-y-1">
          <li>• Calendar event "Ram call" will match client "Ram"</li>
          <li>• "Ram call (Day 1/2)" will also match "Ram"</li>
          <li>• Keywords help match variations (e.g., "ramesh" for "Ram")</li>
          <li>• Unmatched clients get the default rate of ₹{settings.defaultRate.toLocaleString('en-IN')}</li>
        </ul>
      </div>
    </div>
  )
}

