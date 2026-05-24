import { BookOpen, MessageCircle, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const highlights = [
  {
    title: "Upload your materials",
    text: "PDFs, notes, textbooks, and pasted text become a private learning space.",
    icon: BookOpen,
  },
  {
    title: "Ask grounded questions",
    text: "Ilm AI answers from your sources and points back to the material.",
    icon: MessageCircle,
  },
  {
    title: "Practice until it sticks",
    text: "Quizzes, gap detection, and plans turn reading into mastery.",
    icon: Sparkles,
  },
];

export default function Home() {
  return (
    <main className="min-h-screen px-6 py-10">
      <section className="mx-auto flex max-w-5xl flex-col gap-10">
        <div className="max-w-3xl space-y-6">
          <p className="text-sm font-medium uppercase tracking-wide text-muted-foreground">Ilm AI</p>
          <h1 className="text-4xl font-semibold tracking-normal text-foreground sm:text-5xl">
            Your AI ustoz for any material you are studying.
          </h1>
          <p className="max-w-2xl text-lg leading-8 text-muted-foreground">
            Bring a textbook chapter, research paper, course transcript, or your own notes. Ilm AI helps
            you understand, practice, and plan in Uzbek, Russian, or English.
          </p>
          <Button size="lg">Boshlash</Button>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {highlights.map((item) => (
            <Card key={item.title}>
              <CardHeader>
                <item.icon className="h-5 w-5 text-primary" aria-hidden="true" />
                <CardTitle className="text-lg">{item.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-6 text-muted-foreground">{item.text}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}
