import { useState } from 'react'
import { useStripe, useElements, PaymentElement } from '@stripe/react-stripe-js'
import { Button } from '../ui/button'

interface PaymentFormProps {
  onSuccess: () => void
  onError: (error: string) => void
  clientSecret: string
}

export function PaymentForm({ onSuccess, onError, clientSecret }: PaymentFormProps) {
  const stripe = useStripe()
  const elements = useElements()
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!stripe || !elements) {
      return
    }

    setIsLoading(true)

    try {
      const { error } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/billing`,
          payment_method_data: {
            billing_details: {
              // Add any additional billing details if needed
            },
          },
        },
      })

      if (error) {
        onError(error.message || 'Failed to process payment')
      } else {
        onSuccess()
      }
    } catch (e) {
      onError('An unexpected error occurred')
      console.error(e)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <PaymentElement />
      <Button
        type="submit"
        disabled={!stripe || !elements || isLoading}
        className="w-full"
      >
        {isLoading ? 'Processing...' : 'Complete Payment'}
      </Button>
    </form>
  )
}
