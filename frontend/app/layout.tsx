import "./globals.css"
import type { Metadata } from "next"
import { ToastProvider } from "@/hooks/use-toast"
import { Toaster } from "@/components/ui/toaster"
import Navbar from "@/components/navbar"

export const metadata: Metadata = {
  title: "Craefto Automation",
  description: "AI-powered content automation platform for modern businesses",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground antialiased">
        <ToastProvider>
          <Navbar />
          <div className="pt-6">{children}</div>
          <Toaster />
        </ToastProvider>
      </body>
    </html>
  )
}
