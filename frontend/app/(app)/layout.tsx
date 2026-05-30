import { AppNav } from "@/components/app-nav";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen">
      <AppNav />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
