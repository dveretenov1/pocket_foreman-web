import { useState } from 'react'
import { Card } from '../ui/card'
import { Button } from '../ui/button'

interface Tier {
  id: number
  name: string
  price_usd: number
  monthly_pft: number
  overage_pft_price: number
}

interface SubscriptionTiersProps {
  tiers: Tier[]
  currentTierId?: number
  onSelectTier: (tierId: number) => void
}

export function SubscriptionTiers({
  tiers,
  currentTierId,
  onSelectTier,
}: SubscriptionTiersProps) {
  const [selectedTier, setSelectedTier] = useState<number | undefined>(currentTierId)

  const handleSelectTier = (tierId: number) => {
    setSelectedTier(tierId)
    onSelectTier(tierId)
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {tiers.map((tier) => (
        <Card
          key={tier.id}
          className={`p-6 ${
            selectedTier === tier.id
              ? 'border-2 border-blue-500'
              : 'border border-gray-200'
          }`}
        >
          <div className="space-y-4">
            <div className="text-center">
              <h3 className="text-2xl font-bold">{tier.name}</h3>
              <p className="text-3xl font-bold mt-2">
                ${Number(tier.price_usd).toFixed(2)}
                <span className="text-base font-normal text-gray-600">/month</span>
              </p>
            </div>

            <div className="space-y-2">
              <p className="text-gray-600">
                <span className="font-semibold">{tier.monthly_pft.toLocaleString()}</span>{' '}
                PFT monthly allocation
              </p>
              <p className="text-gray-600">
                ${Number(tier.overage_pft_price).toFixed(4)} per additional PFT
              </p>
            </div>

            <div className="pt-4">
              <Button
                onClick={() => handleSelectTier(tier.id)}
                variant={selectedTier === tier.id ? 'default' : 'outline'}
                className="w-full"
              >
                {selectedTier === tier.id ? 'Selected' : 'Select Plan'}
              </Button>
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
}
