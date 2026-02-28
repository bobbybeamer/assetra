import { useCallback, useRef, useState } from 'react'

export type ToastItem = {
  id: number
  message: string
}

export function useToasts() {
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const nextIdRef = useRef(1)

  const removeToast = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const addToast = useCallback(
    (message: string) => {
      const id = nextIdRef.current++
      setToasts((current) => [...current, { id, message }])
      window.setTimeout(() => removeToast(id), 3500)
    },
    [removeToast],
  )

  return {
    toasts,
    addToast,
    removeToast,
  }
}
