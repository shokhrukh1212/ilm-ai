import { redirect } from "next/navigation";
import Link from "next/link";
import { BookOpen, LayoutDashboard, Library, Settings } from "lucide-react";

import { createClient } from "@/lib/supabase/server";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SignOutButton } from "@/components/nav/sign-out-button";

const NAV = [
  { href: "/dashboard", label: "Bosh sahifa", icon: LayoutDashboard },
  { href: "/library", label: "Kutubxona", icon: Library },
  { href: "/settings", label: "Sozlamalar", icon: Settings },
];

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) redirect("/login");

  const { data: profile } = await supabase
    .from("users")
    .select("full_name, onboarded_at")
    .eq("id", user.id)
    .single();

  if (!profile?.onboarded_at) redirect("/onboarding");

  const displayName = profile?.full_name ?? user.email ?? "";
  const initials = displayName
    .split(" ")
    .map((p: string) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <div className="flex min-h-screen">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-56 flex-col border-r bg-card px-4 py-6 gap-6">
        <div className="flex items-center gap-2 px-2">
          <BookOpen className="h-5 w-5 text-primary" />
          <span className="font-semibold text-lg">Ilm AI</span>
        </div>
        <nav className="flex flex-col gap-1">
          {NAV.map(({ href, label, icon: Icon }) => (
            <Button key={href} variant="ghost" asChild className="justify-start gap-3 h-9">
              <Link href={href}>
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            </Button>
          ))}
        </nav>
        <div className="mt-auto">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="w-full justify-start gap-3 h-9 px-2">
                <Avatar className="h-6 w-6">
                  <AvatarFallback className="text-xs">{initials}</AvatarFallback>
                </Avatar>
                <span className="truncate text-sm">{displayName}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-40">
              <SignOutButton />
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex flex-1 flex-col">
        {/* Mobile top bar */}
        <header className="flex md:hidden items-center justify-between border-b px-4 h-14">
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-primary" />
            <span className="font-semibold">Ilm AI</span>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <Avatar className="h-7 w-7">
                  <AvatarFallback className="text-xs">{initials}</AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40">
              <SignOutButton />
            </DropdownMenuContent>
          </DropdownMenu>
        </header>

        <main className="flex-1 px-4 py-6 md:px-8">{children}</main>

        {/* Mobile bottom tab bar */}
        <nav className="flex md:hidden border-t bg-card" aria-label="Asosiy navigatsiya">
          {NAV.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className="flex flex-1 flex-col items-center gap-1 py-3 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <Icon className="h-5 w-5" aria-hidden="true" />
              {label}
            </Link>
          ))}
        </nav>
      </div>
    </div>
  );
}
