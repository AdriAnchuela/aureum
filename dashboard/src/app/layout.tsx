import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AUREUM · macro intelligence",
  description:
    "Gold, bonds, geopolitical risk and prediction markets — explained with data, not predicted with hope.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
