import type { Metadata } from 'next'
import { AuthProvider } from '@/contexts/AuthContext'
import './globals.css'

export const metadata: Metadata = {
  title: 'Interview Assistant | TechYera',
  description: 'AI-powered interview assistant with real-time transcription and intelligent responses',
  keywords: ['interview', 'AI', 'assistant', 'preparation', 'tech', 'coding'],
  authors: [{ name: 'TechYera' }],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}
