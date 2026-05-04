import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Link from 'next/link'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Aadhaar Intelligence Platform',
  description: 'Enterprise-grade offline Aadhaar identity verification',
}

const navItems = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/upload',    label: 'Verify' },
  { href: '/batch',     label: 'Bulk Upload' },
  { href: '/results',   label: 'Results' },
  { href: '/reports',   label: 'Reports' },
]

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-50 min-h-screen`}>
        <nav className="bg-white border-b px-6 py-3 flex items-center gap-8 sticky top-0 z-50">
          <span className="font-bold text-blue-700 text-lg tracking-tight">AADHAAR INTEL</span>
          <div className="flex gap-6">
            {navItems.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className="text-sm text-gray-600 hover:text-blue-600 font-medium transition"
              >
                {label}
              </Link>
            ))}
          </div>
        </nav>
        <main className="p-6">{children}</main>
      </body>
    </html>
  )
}
