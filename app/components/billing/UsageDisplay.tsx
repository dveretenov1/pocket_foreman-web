interface Usage {
  input_tokens: number
  output_tokens: number
  storage_bytes: number
  total_pft: number
  cost_usd: number
  base_cost_usd: number
  overage_cost_usd: number
}

interface Subscription {
  tier: {
    monthly_pft: number
  }
}

interface UsageDisplayProps {
  usage: Usage
  subscription: Subscription | null
}

export function UsageDisplay({ usage, subscription }: UsageDisplayProps) {
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
  }

  const getUsagePercentage = () => {
    if (!subscription) return 0
    return (usage.total_pft / subscription.tier.monthly_pft) * 100
  }

  const usagePercentage = getUsagePercentage()

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <h3 className="text-sm font-medium text-gray-500">Token Usage</h3>
          <div className="mt-1">
            <p className="text-2xl font-semibold">
              {usage.total_pft.toLocaleString()} PFT
            </p>
            <p className="text-sm text-gray-500">
              Input: {usage.input_tokens.toLocaleString()} tokens
              <br />
              Output: {usage.output_tokens.toLocaleString()} tokens
            </p>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-500">Storage Usage</h3>
          <div className="mt-1">
            <p className="text-2xl font-semibold">{formatBytes(usage.storage_bytes)}</p>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-500">Cost</h3>
          <div className="mt-1">
            <p className="text-2xl font-semibold">${usage.cost_usd.toFixed(2)}</p>
            {usage.overage_cost_usd > 0 && (
              <p className="text-sm text-gray-500">
                Includes ${usage.overage_cost_usd.toFixed(2)} overage
              </p>
            )}
          </div>
        </div>
      </div>

      {subscription && (
        <div className="mt-4">
          <div className="flex justify-between text-sm text-gray-500 mb-1">
            <span>Monthly Usage</span>
            <span>{Math.round(usagePercentage)}% of {subscription.tier.monthly_pft.toLocaleString()} PFT</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${
                usagePercentage > 90
                  ? 'bg-red-500'
                  : usagePercentage > 75
                  ? 'bg-yellow-500'
                  : 'bg-blue-500'
              }`}
              style={{ width: `${Math.min(usagePercentage, 100)}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
