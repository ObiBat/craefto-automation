import "./globals.css"
import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "CRAEFTO Automation Dashboard",
  description: "End-to-end testing UI for CRAEFTO automation platform",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground antialiased">
        {children}
      </body>
    </html>
  )
}
