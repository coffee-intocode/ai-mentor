import {createBrowserRouter} from 'react-router-dom'

export const router = createBrowserRouter([
  {path: '/', element: <Chat /> },
  {path: '/signup', element: <Signin/> },
  {path: '/signin', element: <Signin/> },

])
