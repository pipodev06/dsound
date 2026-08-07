import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { Slot } from "radix-ui";

import { cn } from "@/lib/utils";

const iconButtonVariants = cva(
  "inline-flex size-[30px] shrink-0 items-center justify-center rounded-md border border-border bg-transparent p-0 text-text-muted transition-colors outline-none cursor-pointer hover:text-text hover:border-text-muted disabled:opacity-40 disabled:cursor-not-allowed [&_svg]:size-[15px] [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "",
        accent: "text-accent hover:bg-accent hover:text-[#06210f] hover:border-accent",
        danger: "hover:text-danger hover:border-danger",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

function IconButton({
  className,
  variant,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> & VariantProps<typeof iconButtonVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot.Root : "button";
  return <Comp data-slot="icon-button" className={cn(iconButtonVariants({ variant, className }))} {...props} />;
}

export { IconButton, iconButtonVariants };
