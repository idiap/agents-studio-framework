// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import type { Metadata } from "next";
import Image from 'next/image';
import Logo from '@/assets/logo.png';
import Link from 'next/link';

export const metadata: Metadata = {
  title: "Lunar",
  description: "Lunar",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="h-screen bg-white">
      <div className="flex items-center bg-white/50 backdrop-blur-md w-full fixed z-20 mx-4">
        <Link href="/">
          <Image src={Logo} width={128} height={64} alt='Lunar' className="align-middle" />
        </Link>
        <div className="flex gap-4 ml-6">
          <Link style={{ color: "#0D181C" }} href="/app/chat" className="px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors text-[15px] font-semibold leading-[15px]">Chat</Link>
          <Link style={{ color: "#0D181C" }} href="/app/search" className="px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors text-[15px] font-semibold leading-[15px]">Search</Link>
        </div>
      </div>
      {children}
    </div>
  );
}
