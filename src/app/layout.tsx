import type { Metadata, Viewport } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist" });

export const metadata: Metadata = {
  title: "ColorMatch – Test Your Color Knowledge",
  description:
    "A fast-paced color matching game. Name colors, find swatches, and beat the Stroop challenge. How high can you score?",
  icons: { icon: "/favicon.svg", shortcut: "/favicon.svg" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#0a0a1a",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${geist.variable} font-[family-name:var(--font-geist)] antialiased`}>
        {children}
      </body>
    </html>
  );
}
