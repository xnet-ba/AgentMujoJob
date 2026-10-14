import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "AgentMujoJob — Pronađi posao koji ti odgovara", description: "Pretraži oglase u BiH, regionu i svijetu uz pomoć AI asistenta." };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (<html lang="bs"><body><main>{children}</main></body></html>);
}
