import { Noto_Sans, Noto_Sans_Devanagari } from "next/font/google";

// Self-hosted at build time by next/font (served from /_next/static, so the
// CSP's font-src 'self' holds). Latin first, then Devanagari for hi and mr;
// globals.css stacks them in --font-sans.
export const latin = Noto_Sans({
  subsets: ["latin"],
  variable: "--font-latin",
  display: "swap",
});

export const devanagari = Noto_Sans_Devanagari({
  subsets: ["devanagari"],
  variable: "--font-deva",
  display: "swap",
});

export const fontVariables = `${latin.variable} ${devanagari.variable}`;
