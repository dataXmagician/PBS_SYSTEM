import { Badge, type BadgeProps } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { LucideIcon } from "lucide-react"

interface StatusConfig {
  label: string
  variant: BadgeProps["variant"]
  icon?: LucideIcon
}

interface StatusBadgeProps extends Omit<BadgeProps, "variant"> {
  status: string
  configMap: Record<string, StatusConfig>
  fallbackLabel?: string
}

function StatusBadge({ status, configMap, fallbackLabel, className, ...props }: StatusBadgeProps) {
  const config = configMap[status]
  const label = config?.label ?? fallbackLabel ?? status
  const variant = config?.variant ?? "secondary"
  const Icon = config?.icon

  return (
    <Badge variant={variant} className={cn("gap-1", className)} {...props}>
      {Icon && <Icon className="h-3 w-3" />}
      {label}
    </Badge>
  )
}

export { StatusBadge }
export type { StatusConfig }
