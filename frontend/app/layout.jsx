import { Inter, Source_Serif_4 } from 'next/font/google'
import './globals.css'
import ClientThemeSync from '../components/ClientThemeSync'
import { Toaster } from 'sonner'
import Script from 'next/script'
import { ThemeProvider } from 'next-themes'
import BottomNav from '../components/BottomNav'
import SplashScreen from '../components/SplashScreen'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const sourceSerif = Source_Serif_4({ subsets: ['latin'], weight: ['400'], variable: '--font-display' })

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: 'cover',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#0B1F3A' },
    { media: '(prefers-color-scheme: dark)', color: '#0A1628' },
  ],
};

export const metadata = {
  title: 'MetroLens',
  description: 'Legal Metrology Compliance Checker',
  icons: {
    icon: '/icon.png',
    shortcut: '/icon.png',
    apple: '/icon.png',
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'MetroLens',
  },
}

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head></head>
      <body className={`${inter.variable} ${sourceSerif.variable} font-sans pb-24 md:pb-0 overflow-x-hidden w-full`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="light" forcedTheme="light"
          enableSystem={false}
          disableTransitionOnChange={false}
          storageKey="satya-theme"
        >
          {/* Clean flat government background — no ambient orbs */}
          <div className="fixed inset-0 z-[-1] pointer-events-none bg-background" />
          {children}
          <BottomNav />
          
          <ClientThemeSync />
        </ThemeProvider>
        <Toaster position="top-right" />
      </body>
    </html>
  )
}

