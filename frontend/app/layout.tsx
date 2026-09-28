import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'StartupOps AI — Autonomous Operations Layer',
  description: 'AI-driven operations layer for tech startups with cross-system correlation, risk policies, and verified execution.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#080b11] text-slate-100 min-h-screen selection:bg-indigo-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
