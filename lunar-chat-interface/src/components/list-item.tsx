// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Calendar } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { ReactNode } from "react";
import Link from "next/link";

interface ListItemProps {
  title: string;
  description?: string | ReactNode | null;
  date?: string | Date | null;
  href?: string;
  icon?: ReactNode;
  actions?: ReactNode;
}

export function ListItem({
  title,
  description,
  date,
  href,
  icon,
  actions,
}: ListItemProps) {
  const formattedDate = date
    ? typeof date === "string"
      ? new Date(date)
      : date
    : null;

  const content = (
    <>
      <div className="flex items-center justify-between p-4 hover:bg-accent cursor-pointer">
        <div className="flex items-start gap-4 w-full">
          <div className="flex flex-col gap-1 items-start w-full">
            <div className="flex items-center w-full gap-2">
              {icon && (
                <div className="p-1 bg-linear-to-r from-primary-main to-primary-light rounded-sm">
                  {icon}
                </div>
              )}
              <h3 className="text-text-primary font-medium text-base mr-auto">
                {title}
              </h3>
              {formattedDate && (
                <div className="flex items-center text-xs text-muted-foreground">
                  <Calendar className="w-3 h-3 mr-1" />
                  {formattedDate.toLocaleDateString()} •{" "}
                  {formattedDate.toLocaleTimeString()}
                </div>
              )}
              {actions && (
                <div className="flex items-center gap-1 ml-2">{actions}</div>
              )}
            </div>
            {description && (
              <div className="text-sm text-muted-foreground mt-1">
                {description}
              </div>
            )}
          </div>
        </div>
      </div>
      <Separator />
    </>
  );

  if (href) {
    return <Link href={href}>{content}</Link>;
  }

  return content;
}
