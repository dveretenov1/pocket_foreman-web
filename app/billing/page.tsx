'use client'

import { useEffect, useState, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { Elements } from '@stripe/react-stripe-js'
import { loadStripe, Appearance } from '@stripe/stripe-js'
import { Card } from '../components/ui/card'
import { PaymentForm } from '../components/billing/PaymentForm'
import { SubscriptionTiers } from '../components/billing/SubscriptionTiers'
import { PaymentMethodManager } from '../components/billing/PaymentMethodManager'
import { UsageDisplay } from '../components/billing/UsageDisplay'
import { api } from '../services/api'

interface Tier {
  id: number
  name: string
  price_usd: number
  monthly_pft: number
  overage_pft_price: number
}

interface Subscription {
  tier: Tier
  status: string
  current_period_end: string
  stripe_subscription_id: string
  available_tiers: Tier[]
}

interface PaymentMethod {
  id: string
  brand: string
  last4: string
  exp_month: number
  exp_year: number
}

interface Usage {
  input_tokens: number
  output_tokens: number
  storage_bytes: number
  total_pft: number
  cost_usd: number
  base_cost_usd: number
  overage_cost_usd: number
}

// Initialize Stripe
const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!)

export default function BillingPage() {
  const [tiers, setTiers] = useState<Tier[]>([])
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([])
  const [selectedTierId, setSelectedTierId] = useState<number | null>(null)
  const [clientSecret, setClientSecret] = useState<string>('')
  const [usage, setUsage] = useState<Usage | null>(null)
  const [error, setError] = useState<string>('')

  const { user } = useAuth()

  const getToken = useCallback(async () => {
    if (!user) throw new Error('Not authenticated')
    return user.getIdToken()
  }, [user])

  useEffect(() => {
    if (user) {
      loadBillingData()
    }
  }, [user])

  const loadBillingData = async () => {
    try {
      // Load subscription data including tiers
      const subscriptionData = await api.get<Subscription & { available_tiers: Tier[] }>('/billing/subscription', getToken)
      setTiers(subscriptionData.available_tiers)
      setSubscription(subscriptionData)
      setSelectedTierId(subscriptionData.tier.id)

      // Load payment methods
      const methods = await api.get<PaymentMethod[]>('/billing/payment-methods', getToken)
      setPaymentMethods(methods)

      // Load usage data
      const usageData = await api.get<Usage>('/billing/usage/current', getToken)
      setUsage(usageData)
    } catch (err) {
      setError('Failed to load billing data')
      console.error(err)
    }
  }

  const handleSelectTier = async (tierId: number) => {
    setSelectedTierId(tierId)
    try {
      if (paymentMethods.length === 0) {
        // No payment method - create setup intent
        const setupResponse = await api.post<{ client_secret: string }>(
          '/billing/setup-intent',
          {},
          getToken
        )
        setClientSecret(setupResponse.client_secret)
      } else {
        // Create subscription with existing payment method
        const subscriptionResponse = await api.post<{ client_secret: string }>(
          '/billing/subscription',
          { 
            tier_id: tierId,
            payment_method_id: paymentMethods[0].id
          },
          getToken
        )
        setClientSecret(subscriptionResponse.client_secret)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process request')
      console.error(err)
    }
  }

  const handlePaymentSuccess = async () => {
    await loadBillingData() // Reload all data
    setClientSecret('') // Clear client secret to hide payment form
    setError('') // Clear any errors
  }

  const handlePaymentError = (message: string) => {
    setError(message)
  }

  const handleDeletePaymentMethod = async (paymentMethodId: string) => {
    try {
      await api.delete(`/billing/payment-methods/${paymentMethodId}`, getToken)
      setPaymentMethods(paymentMethods.filter(pm => pm.id !== paymentMethodId))
    } catch (err) {
      setError('Failed to remove payment method')
      console.error(err)
    }
  }

  const appearance: Appearance = {
    theme: 'stripe' as const,
    variables: {
      colorPrimary: '#0066cc',
    },
  }

  return (
    <div className="container mx-auto py-8 space-y-8">
      <h1 className="text-3xl font-bold">Billing & Usage</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded">
          {error}
        </div>
      )}

      {/* Current Usage */}
      {usage && (
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Current Usage</h2>
          <UsageDisplay usage={usage} subscription={subscription} />
        </Card>
      )}

      {/* Subscription Tiers */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Subscription Plans</h2>
        <SubscriptionTiers
          tiers={tiers}
          currentTierId={subscription?.tier.id}
          onSelectTier={handleSelectTier}
        />
      </Card>

      {/* Payment Methods */}
      <Card className="p-6">
        <PaymentMethodManager
          paymentMethods={paymentMethods}
          onSelect={(id) => console.log('Selected payment method:', id)}
          onDelete={handleDeletePaymentMethod}
        />
      </Card>

      {/* Payment Form */}
      {clientSecret && (
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Payment Details</h2>
          <Elements
            stripe={stripePromise}
            options={{
              clientSecret,
              appearance,
            }}
          >
            <PaymentForm
              clientSecret={clientSecret}
              onSuccess={handlePaymentSuccess}
              onError={handlePaymentError}
            />
          </Elements>
        </Card>
      )}
    </div>
  )
}
