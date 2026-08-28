import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";


export const metadata: Metadata = {
  title: "Code Four Video Search",
  description: "Inspect and search processed body-camera footage",
};


export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-[var(--border)] bg-[var(--panel)]">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
            <Link className="text-lg font-semibold tracking-tight" href="/">
              Code Four
            </Link>
            <span className="text-sm text-[var(--muted)]">Processing workspace</span>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}

