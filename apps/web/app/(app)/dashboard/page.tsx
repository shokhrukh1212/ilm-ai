import { createClient } from "@/lib/supabase/server";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BookOpen, MessageCircle } from "lucide-react";

export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const { data: profile } = await supabase
    .from("users")
    .select("full_name")
    .eq("id", user!.id)
    .single();

  const name = profile?.full_name ?? user?.email?.split("@")[0] ?? "foydalanuvchi";

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-semibold">Salom, {name}! 👋</h1>
        <p className="text-muted-foreground mt-1">Bugun nima o&apos;qiymiz?</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card className="opacity-60">
          <CardHeader className="flex flex-row items-center gap-3 pb-2">
            <BookOpen className="h-5 w-5 text-primary" />
            <CardTitle className="text-base">Materiallar</CardTitle>
          </CardHeader>
          <CardContent>
            <CardDescription>Phase 2 da qo&apos;shiladi — PDF va matnlarni yuklang.</CardDescription>
          </CardContent>
        </Card>

        <Card className="opacity-60">
          <CardHeader className="flex flex-row items-center gap-3 pb-2">
            <MessageCircle className="h-5 w-5 text-primary" />
            <CardTitle className="text-base">Chat</CardTitle>
          </CardHeader>
          <CardContent>
            <CardDescription>Phase 3 da qo&apos;shiladi — materiallar bo&apos;yicha savollar bering.</CardDescription>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
