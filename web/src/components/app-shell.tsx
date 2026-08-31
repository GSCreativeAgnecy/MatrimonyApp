"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import { Compass, Heart, MessageCircle, User } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";

const NAV = [
  { href: "/discover", label: "Discover", icon: Compass },
  { href: "/matches", label: "Matches", icon: Heart },
  { href: "/messages", label: "Messages", icon: MessageCircle },
  { href: "/profile", label: "Profile", icon: User },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { logout, user } = useAuth();

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-md flex-col bg-gray-50">
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3">
        <Link href="/discover" className="text-lg font-bold text-primary">
          Ardhang
        </Link>
        <div className="flex items-center gap-2">
          {user?.email && <span className="hidden text-xs text-gray-500 sm:inline">{user.email}</span>}
          <Button variant="ghost" size="md" onClick={logout}>
            Sign out
          </Button>
        </div>
      </header>

      <main className="flex-1 px-4 py-4 pb-20">{children}</main>

      <nav className="fixed bottom-0 left-1/2 w-full max-w-md -translate-x-1/2 border-t border-gray-200 bg-white">
        <div className="grid grid-cols-4">
          {NAV.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "flex flex-col items-center gap-1 py-2.5 text-[11px] font-medium",
                  active ? "text-primary" : "text-gray-400 hover:text-gray-600",
                )}
              >
                <Icon size={22} />
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}