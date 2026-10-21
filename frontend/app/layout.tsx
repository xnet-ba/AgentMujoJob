import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgentMujoJob — Pronađi posao koji ti odgovara",
  description: "Pretraži oglase u BiH, regionu i svijetu uz pomoć AI asistenta.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f3f3f3" },
    { media: "(prefers-color-scheme: dark)", color: "#1f1f1f" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (<html lang="bs"><body><main>{children}</main></body></html>);
}
