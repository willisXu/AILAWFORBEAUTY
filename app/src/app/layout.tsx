import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: '跨國化妝品法規自動稽核系統 | Cosmetics Compliance Audit',
  description: '自動化法規追蹤與成分合規性檢查系統 | Automated regulation tracking and compliance checking',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-TW">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
