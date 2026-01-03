import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export function SignUpSuccess() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Check your email</CardTitle>
        <CardDescription>
          We&apos;ve sent you a verification link. Please check your email to verify your account.
        </CardDescription>
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
