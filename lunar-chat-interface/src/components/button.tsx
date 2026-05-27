// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import React from "react";
import { Button as ShadcnButton } from "@/components/ui/button";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
}

const Button: React.FC<ButtonProps> = ({
  children,
  className,
  variant = "default",
  disabled = false,
  ...rest
}) => {
  // For custom variants (primary/default), apply custom styling
  if (variant === "primary" || variant === "default") {
    const getButtonClasses = () => {
      const baseClasses = "px-3 py-2 rounded-md font-semibold transition cursor-pointer";

      if (disabled) {
        return `${baseClasses} bg-gray-100 text-gray-400 border-gray-300 cursor-not-allowed`;
      }

      if (variant === "primary") {
        return `${baseClasses} bg-gradient-to-r from-[#4DB1DD] to-[#69C3E2] hover:from-[#245C82] hover:to-[#3A8AB4] text-white border-0`;
      }

      return `${baseClasses} border-2 border-primary-main hover:bg-gray-100 bg-transparent text-[#4DB1DD]`;
    };

    return (
      <ShadcnButton
        className={`${getButtonClasses()} ${className ?? ""}`}
        disabled={disabled}
        {...rest}
      >
        {children}
      </ShadcnButton>
    );
  }

  // For other variants, pass through to shadcn with the variant prop
  return (
    <ShadcnButton
      variant={variant}
      className={className}
      disabled={disabled}
      {...rest}
    >
      {children}
    </ShadcnButton>
  );
};

export default Button;
