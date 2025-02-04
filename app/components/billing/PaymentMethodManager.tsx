import { useState } from 'react'
import { Card } from '../ui/card'
import { Button } from '../ui/button'

interface PaymentMethod {
  id: string
  brand: string
  last4: string
  exp_month: number
  exp_year: number
}

interface PaymentMethodManagerProps {
  paymentMethods: PaymentMethod[]
  onSelect: (paymentMethodId: string) => void
  onDelete: (paymentMethodId: string) => void
}

export function PaymentMethodManager({
  paymentMethods,
  onSelect,
  onDelete,
}: PaymentMethodManagerProps) {
  const [selectedId, setSelectedId] = useState<string>()

  const handleSelect = (id: string) => {
    setSelectedId(id)
    onSelect(id)
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Saved Payment Methods</h3>
      
      {paymentMethods.length === 0 ? (
        <p className="text-gray-500">No saved payment methods</p>
      ) : (
        <div className="grid gap-4">
          {paymentMethods.map((method) => (
            <Card
              key={method.id}
              className={`p-4 ${
                selectedId === method.id
                  ? 'border-2 border-blue-500'
                  : 'border border-gray-200'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex-1">
                    <p className="font-medium capitalize">
                      {method.brand} •••• {method.last4}
                    </p>
                    <p className="text-sm text-gray-500">
                      Expires {method.exp_month}/{method.exp_year}
                    </p>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <Button
                    variant={selectedId === method.id ? "default" : "outline"}
                    onClick={() => handleSelect(method.id)}
                  >
                    {selectedId === method.id ? 'Selected' : 'Use'}
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => onDelete(method.id)}
                  >
                    Remove
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
