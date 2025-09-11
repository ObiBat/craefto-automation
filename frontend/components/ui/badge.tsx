import { clsx } from "clsx"

export function Badge({ variant = "default", className, children }: { variant?: "default" | "secondary" | "destructive" | "outline"; className?: string; children?: React.ReactNode }) {
  const base = "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors"
  const variants: Record<string, string> = {
    default: "border-transparent bg-primary text-primary-foreground",
    secondary: "border-transparent bg-secondary text-secondary-foreground", 
    destructive: "border-transparent bg-destructive text-destructive-foreground",
    outline: "text-foreground",
  }
  
  // If className contains custom background colors, don't apply variant styles
  const hasCustomBg = className?.includes('bg-')
  const variantClass = hasCustomBg ? '' : variants[variant]
  
  return <span className={clsx(base, variantClass, className)}>{children}</span>
}
