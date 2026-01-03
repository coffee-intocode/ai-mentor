import { type FormEvent, useCallback, useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/context/AuthContext'

export function ForgotPasswordForm() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const { resetPassword } = useAuth()

  const handleSubmit = useCallback(
    async (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault()
      setError(null)
      setIsLoading(true)

      const result = await resetPassword(email)

      setIsLoading(false)
      if (!result.success) {
        setError(result.error ?? 'Failed to send reset email')
        return
      }
      setSuccess(true)
    },
    [email, resetPassword],
  )

  if (success) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Check your email</CardTitle>
          <CardDescription>We&apos;ve sent a password reset link to {email}</CardDescription>
        </CardHeader>
        <CardContent>
          <Link to="/auth/login">
            <Button variant="outline" className="w-full">
              Back to sign in
            </Button>
          </Link>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Forgot password</CardTitle>
        <CardDescription>Enter your email to receive a reset link</CardDescription>
      </CardHeader>
      <CardContent>
        <form
          onSubmit={(e) => {
            handleSubmit(e).catch(() => {})
          }}
        >
          <div className="flex flex-col gap-4">
            <div className="grid gap-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                }}
              />
            </div>
            {error && (
              <p role="alert" className="text-sm text-red-500">
                {error}
              </p>
            )}
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Sending...' : 'Send reset link'}
            </Button>
            <Link to="/auth/login" className="text-center text-sm underline underline-offset-4">
              Back to sign in
            </Link>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
