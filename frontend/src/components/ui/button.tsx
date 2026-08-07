import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { Slot } from "radix-ui";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex shrink-0 items-center justify-center gap-1.5 rounded-md border border-transparent font-sans text-sm font-semibold whitespace-nowrap transition-colors outline-none select-none cursor-pointer active:translate-y-px disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        accent:
          "bg-accent text-[#06210f] hover:bg-[#52e992] disabled:bg-surface-2 disabled:text-text-muted",
        ghost: "bg-transparent text-text-muted border-border hover:text-text hover:border-text-muted",
        danger: "bg-transparent text-danger border-border hover:bg-danger hover:text-[#2a0a0a] hover:border-danger",
      },
      size: {
        default: "px-4 py-2",
        sm: "px-2 py-2 text-xs",
      },
    },
    defaultVariants: {
      variant: "accent",
      size: "default",
    },
  }
);

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  }) {
  const Comp = asChild ? Slot.Root : "button";

  return (
    <Comp data-slot="button" className={cn(buttonVariants({ variant, size, className }))} {...props} />
  );
}

export { Button, buttonVariants };
