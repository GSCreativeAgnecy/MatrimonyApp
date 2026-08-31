"use client";

import { clsx } from "clsx";
import { ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "outline" | "ghost";
  size?: "md" | "lg";
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => (
    <button
      ref={ref}
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed",
        size === "md" ? "px-4 py-2 text-sm" : "px-6 py-3 text-base",
        variant === "primary" && "bg-primary text-white hover:bg-primary-dark",
        variant === "outline" && "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50",
        variant === "ghost" && "text-gray-600 hover:bg-gray-100",
        className,
      )}
      {...props}
    />
  ),
);
Button.displayName = "Button";