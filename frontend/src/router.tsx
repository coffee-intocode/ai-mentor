import { createBrowserRouter } from 'react-router-dom'
import App from './App'
import { AuthLayout } from './components/auth/AuthLayout'
import { ForgotPasswordForm } from './components/auth/ForgotPassword'
import { PrivateRoute } from './components/auth/PrivateRoute'
import { ResetPasswordForm } from './components/auth/ResetPassword'
import { SignInForm } from './components/auth/SignIn'
import { SignUpForm } from './components/auth/Signup'
import { SignUpSuccess } from './components/auth/SignUpSuccess'

export const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <PrivateRoute>
        <App />
      </PrivateRoute>
    ),
  },
  {
    path: '/:conversationId',
    element: (
      <PrivateRoute>
        <App />
      </PrivateRoute>
    ),
  },
  {
    path: '/auth',
    element: <AuthLayout />,
    children: [
      { path: 'login', element: <SignInForm /> },
      { path: 'signup', element: <SignUpForm /> },
      { path: 'forgot-password', element: <ForgotPasswordForm /> },
      { path: 'reset-password', element: <ResetPasswordForm /> },
      { path: 'sign-up-success', element: <SignUpSuccess /> },
    ],
  },
])
