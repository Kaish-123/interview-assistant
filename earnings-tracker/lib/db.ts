import Database from 'better-sqlite3'
import path from 'path'

const dbPath = path.join(process.cwd(), 'earnings.db')
const db = new Database(dbPath)

// Initialize database tables
db.exec(`
  CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    rate INTEGER NOT NULL,
    keywords TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS earnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    event_title TEXT NOT NULL,
    client_name TEXT,
    date DATE NOT NULL,
    start_time TEXT,
    end_time TEXT,
    duration_minutes INTEGER,
    rate INTEGER NOT NULL,
    is_custom_client INTEGER DEFAULT 0,
    payment_status TEXT DEFAULT 'pending',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS sync_state (
    id INTEGER PRIMARY KEY,
    last_sync_token TEXT,
    last_sync_at DATETIME
  );

  CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
  );
`)

// Insert default settings if not exists
const defaultRate = db.prepare('SELECT value FROM settings WHERE key = ?').get('default_rate')
if (!defaultRate) {
  db.prepare('INSERT INTO settings (key, value) VALUES (?, ?)').run('default_rate', '12500')
}

// Insert exclude keywords if not exists
const excludeKeywords = db.prepare('SELECT value FROM settings WHERE key = ?').get('exclude_keywords')
if (!excludeKeywords) {
  db.prepare('INSERT INTO settings (key, value) VALUES (?, ?)').run(
    'exclude_keywords',
    JSON.stringify(['Daily Office meeting', 'team meeting', 'standup', 'internal'])
  )
}

export interface Client {
  id: number
  name: string
  rate: number
  keywords: string | null
  created_at: string
}

export interface Earning {
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
  created_at: string
}

// Client operations
export function getAllClients(): Client[] {
  return db.prepare('SELECT * FROM clients ORDER BY name').all() as Client[]
}

export function addClient(name: string, rate: number, keywords?: string): Client {
  const stmt = db.prepare('INSERT INTO clients (name, rate, keywords) VALUES (?, ?, ?)')
  const result = stmt.run(name, rate, keywords || null)
  return db.prepare('SELECT * FROM clients WHERE id = ?').get(result.lastInsertRowid) as Client
}

export function updateClient(id: number, name: string, rate: number, keywords?: string): Client {
  db.prepare('UPDATE clients SET name = ?, rate = ?, keywords = ? WHERE id = ?').run(name, rate, keywords || null, id)
  return db.prepare('SELECT * FROM clients WHERE id = ?').get(id) as Client
}

export function deleteClient(id: number): void {
  db.prepare('DELETE FROM clients WHERE id = ?').run(id)
}

// Earnings operations
export function addEarning(earning: Omit<Earning, 'id' | 'created_at'>): Earning {
  const stmt = db.prepare(`
    INSERT OR REPLACE INTO earnings 
    (event_id, event_title, client_name, date, start_time, end_time, duration_minutes, rate, is_custom_client, payment_status, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `)
  const result = stmt.run(
    earning.event_id,
    earning.event_title,
    earning.client_name,
    earning.date,
    earning.start_time,
    earning.end_time,
    earning.duration_minutes,
    earning.rate,
    earning.is_custom_client,
    earning.payment_status,
    earning.notes
  )
  return db.prepare('SELECT * FROM earnings WHERE id = ?').get(result.lastInsertRowid) as Earning
}

export function getEarningsByDateRange(startDate: string, endDate: string): Earning[] {
  return db.prepare(`
    SELECT * FROM earnings 
    WHERE date >= ? AND date <= ?
    ORDER BY date DESC, start_time DESC
  `).all(startDate, endDate) as Earning[]
}

export function getEarningsForDate(date: string): Earning[] {
  return db.prepare('SELECT * FROM earnings WHERE date = ? ORDER BY start_time').all(date) as Earning[]
}

export function getTodayEarnings(): Earning[] {
  const today = new Date().toISOString().split('T')[0]
  return getEarningsForDate(today)
}

export function getMonthEarnings(year: number, month: number): Earning[] {
  const startDate = `${year}-${String(month).padStart(2, '0')}-01`
  const endDate = `${year}-${String(month).padStart(2, '0')}-31`
  return getEarningsByDateRange(startDate, endDate)
}

export function updatePaymentStatus(id: number, status: string): void {
  db.prepare('UPDATE earnings SET payment_status = ? WHERE id = ?').run(status, id)
}

// Settings operations
export function getSetting(key: string): string | null {
  const result = db.prepare('SELECT value FROM settings WHERE key = ?').get(key) as { value: string } | undefined
  return result?.value || null
}

export function setSetting(key: string, value: string): void {
  db.prepare('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)').run(key, value)
}

export function getDefaultRate(): number {
  return parseInt(getSetting('default_rate') || '12500', 10)
}

export function getExcludeKeywords(): string[] {
  const keywords = getSetting('exclude_keywords')
  return keywords ? JSON.parse(keywords) : []
}

// Sync state operations
export function getSyncToken(): string | null {
  const result = db.prepare('SELECT last_sync_token FROM sync_state WHERE id = 1').get() as { last_sync_token: string } | undefined
  return result?.last_sync_token || null
}

export function setSyncToken(token: string): void {
  db.prepare('INSERT OR REPLACE INTO sync_state (id, last_sync_token, last_sync_at) VALUES (1, ?, CURRENT_TIMESTAMP)').run(token)
}

// Dashboard stats
export function getDashboardStats() {
  const today = new Date().toISOString().split('T')[0]
  const now = new Date()
  const startOfMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`
  const endOfMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-31`

  const todayEarnings = db.prepare(`
    SELECT COALESCE(SUM(rate), 0) as total, COUNT(*) as count 
    FROM earnings WHERE date = ?
  `).get(today) as { total: number; count: number }

  const monthEarnings = db.prepare(`
    SELECT COALESCE(SUM(rate), 0) as total, COUNT(*) as count 
    FROM earnings WHERE date >= ? AND date <= ?
  `).get(startOfMonth, endOfMonth) as { total: number; count: number }

  const pendingPayments = db.prepare(`
    SELECT COALESCE(SUM(rate), 0) as total, COUNT(*) as count 
    FROM earnings WHERE payment_status = 'pending'
  `).get() as { total: number; count: number }

  // Daily earnings for chart (last 7 days)
  const dailyEarnings = db.prepare(`
    SELECT date, SUM(rate) as total, COUNT(*) as count
    FROM earnings
    WHERE date >= date('now', '-7 days')
    GROUP BY date
    ORDER BY date
  `).all() as { date: string; total: number; count: number }[]

  // Client breakdown for current month
  const clientBreakdown = db.prepare(`
    SELECT 
      COALESCE(client_name, 'Other') as client_name,
      SUM(rate) as total,
      COUNT(*) as count
    FROM earnings 
    WHERE date >= ? AND date <= ?
    GROUP BY client_name
    ORDER BY total DESC
    LIMIT 10
  `).all(startOfMonth, endOfMonth) as { client_name: string; total: number; count: number }[]

  return {
    today: todayEarnings,
    month: monthEarnings,
    pending: pendingPayments,
    dailyEarnings,
    clientBreakdown
  }
}

export default db

