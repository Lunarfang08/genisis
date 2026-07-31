import type { Metadata, Viewport } from "next";
import { headers } from "next/headers";
import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host =
    requestHeaders.get("x-forwarded-host") ??
    requestHeaders.get("host") ??
    "localhost:3000";
  const protocol =
    requestHeaders.get("x-forwarded-proto") ??
    (host.startsWith("localhost") ? "http" : "https");
  const baseUrl = new URL(`${protocol}://${host}`);

  const title = "GENESIS // Civilization Runtime";
  const description =
    "A deterministic artificial civilization simulator with selective AI narratives.";

  return {
    metadataBase: baseUrl,
    title,
    description,
    applicationName: "GENESIS",
    openGraph: {
      title,
      description:
        "Observe a civilization emerge from deterministic systems and immutable history.",
      type: "website",
      url: baseUrl,
      images: [
        {
          url: new URL("/og-release.png", baseUrl),
          width: 1536,
          height: 1024,
          alt: "GENESIS - History you can prove",
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [new URL("/og-release.png", baseUrl)],
    },
  };
}

export const viewport: Viewport = {
  colorScheme: "dark",
  themeColor: "#080b0a",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
