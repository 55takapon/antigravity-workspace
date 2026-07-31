import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from '@/components/ui/sonner'
import { AuthProvider } from '@/features/auth/auth-provider'
import App from '@/App'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 体重データは頻繁に変わらないため、無駄な再取得を抑える
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <App />
      </AuthProvider>
      <Toaster position="top-center" richColors />
    </QueryClientProvider>
  </StrictMode>,
)
