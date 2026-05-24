import type { Metadata } from "next";
import { Inter, Manrope } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

const inter = Inter({
  subsets: ["latin", "cyrillic"],
  variable: "--font-inter",
});

const manrope = Manrope({
  subsets: ["latin", "cyrillic"],
  variable: "--font-manrope",
});

export const metadata: Metadata = {
  title: "Ilm AI",
  description: "Personal AI learning companion for your own study materials.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="uz-Latn">
      <body className={`${inter.variable} ${manrope.variable} antialiased`}>
        {children}
        <Toaster />
      </body>
    </html>
  );
}
