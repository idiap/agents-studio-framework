// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import './globals.css'
import { Inter } from 'next/font/google'
import { NextAuthProvider } from './utils/next-auth-provider';
import { Toaster } from 'sonner';

const inter = Inter({ weight: ["200", "400", "600", "800"], subsets: ['latin'] })

export const metadata = {
  title: 'Lunar',
  description: 'Lunar',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Kantumruy+Pro:ital,wght@0,100..700;1,100..700&display=swap" rel="stylesheet" />
      </head>
      <body className={inter.className} style={{ height: '100%', backgroundColor: '#fff', color: 'unset', colorScheme: 'unset' }}>
        <NextAuthProvider>
          {children}
          <Toaster />
        </NextAuthProvider>
      </body>
    </html>
  )
}
