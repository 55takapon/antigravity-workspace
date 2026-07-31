import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2, Mail, Scale } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/features/auth/auth-context'

const schema = z.object({
  email: z.string().min(1, 'メールアドレスを入力してください').email('メールアドレスの形式が正しくありません'),
})

type FormValues = z.infer<typeof schema>

export function LoginPage() {
  const { signInWithEmail } = useAuth()
  const [sentTo, setSentTo] = useState<string | null>(null)

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: '' },
  })

  const onSubmit = async (values: FormValues) => {
    try {
      await signInWithEmail(values.email)
      setSentTo(values.email)
    } catch (error) {
      toast.error('送信に失敗しました', {
        description: error instanceof Error ? error.message : undefined,
      })
    }
  }

  return (
    <div className="flex min-h-dvh items-center justify-center px-6">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3 text-center">
          <div className="bg-primary text-primary-foreground flex size-12 items-center justify-center rounded-2xl">
            <Scale className="size-6" />
          </div>
          <div>
            <h1 className="text-xl font-semibold tracking-tight">体重記録</h1>
            <p className="text-muted-foreground mt-1 text-sm">
              メールに届くリンクからログインします
            </p>
          </div>
        </div>

        {sentTo ? (
          <div className="space-y-4 text-center">
            <div className="bg-muted text-muted-foreground mx-auto flex size-12 items-center justify-center rounded-full">
              <Mail className="size-5" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium">メールを送信しました</p>
              <p className="text-muted-foreground text-sm">
                <span className="text-foreground">{sentTo}</span> 宛のリンクを開くとログインできます。
              </p>
            </div>
            <Button variant="ghost" className="w-full" onClick={() => setSentTo(null)}>
              別のアドレスで送り直す
            </Button>
          </div>
        ) : (
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4" noValidate>
            <div className="space-y-2">
              <Label htmlFor="email">メールアドレス</Label>
              <Input
                id="email"
                type="email"
                inputMode="email"
                autoComplete="email"
                placeholder="you@example.com"
                aria-invalid={Boolean(form.formState.errors.email)}
                {...form.register('email')}
              />
              {form.formState.errors.email && (
                <p className="text-destructive text-xs">{form.formState.errors.email.message}</p>
              )}
            </div>

            <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting && <Loader2 className="size-4 animate-spin" />}
              ログインリンクを送る
            </Button>
          </form>
        )}
      </div>
    </div>
  )
}
