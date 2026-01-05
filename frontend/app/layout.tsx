'use client';

import type { Metadata } from "next";
import "./globals.css";
import { ActivityChatProvider } from '@/contexts/ActivityChatContext';
import ActivityChatDrawer from '@/components/ActivityChatDrawer';

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <ActivityChatProvider>
          {children}
          <ActivityChatDrawer />
        </ActivityChatProvider>
      </body>
    </html>
  );
}
