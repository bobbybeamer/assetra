import { type ToastItem } from '../hooks/useToasts'

type ToastStackProps = {
  toasts: ToastItem[]
  onDismiss: (id: number) => void
}

export function ToastStack({ toasts, onDismiss }: ToastStackProps) {
  if (toasts.length === 0) {
    return null
  }

  return (
    <div className="toast-stack" role="status" aria-live="polite">
      {toasts.map((toast) => (
        <div key={toast.id} className="toast-item">
          <span>{toast.message}</span>
          <button className="toast-dismiss" type="button" onClick={() => onDismiss(toast.id)}>
            ×
          </button>
        </div>
      ))}
    </div>
  )
}
