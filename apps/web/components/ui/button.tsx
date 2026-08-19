import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
const styles = cva("inline-flex items-center justify-center gap-2 rounded-full text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan disabled:opacity-50", { variants: { variant: { default: "bg-cyan text-ink hover:bg-white", outline: "border border-white/15 bg-white/5 text-current hover:border-cyan/60", ghost: "hover:bg-white/10" }, size: { default: "px-5 py-3", sm: "px-3.5 py-2 text-xs" } }, defaultVariants: { variant: "default", size: "default" } });
export function Button({ asChild, variant, size, className, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof styles> & { asChild?: boolean }) { const Comp = asChild ? Slot : "button"; return <Comp className={cn(styles({ variant, size }), className)} {...props} />; }
