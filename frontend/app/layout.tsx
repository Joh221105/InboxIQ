import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { Inter } from "next/font/google";
import Link from "next/link";
import { Toaster } from "sonner";
import { cn } from "@/lib/utils";
import { SignOutButton } from "@/components/sign-out-button";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "InboxIQ",
  description: "AI-powered unified email — connect Gmail and triage your inbox",
};

const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/inbox", label: "Inbox" },
  { href: "/packages", label: "Packages" },
  { href: "/contacts", label: "Contacts" },
  { href: "/settings", label: "Settings" },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={cn("font-sans", inter.variable)}>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased flex h-screen`}>
        <nav className="flex flex-col w-56 shrink-0 border-r px-4 py-6 gap-1">
          <span className="text-base font-semibold mb-4">InboxIQ</span>
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm px-3 py-2 rounded hover:bg-accent"
            >
              {link.label}
            </Link>
          ))}
          <div className="mt-auto pt-4 border-t">
            <SignOutButton />
          </div>
        </nav>
        <main className="flex-1 overflow-auto">{children}</main>
        <Toaster richColors position="top-right" />
      </body>
    </html>
  );
}
