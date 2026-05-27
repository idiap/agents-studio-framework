// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Shield, ShieldAlert, ShieldCheck } from "lucide-react";

interface TrustBadgeProps {
  trustIndex?: number | null;
  band?: string | null;
}

const TrustBadge: React.FC<TrustBadgeProps> = ({ trustIndex, band }) => {
  if (trustIndex === null || trustIndex === undefined) return null;

  const getBandColor = () => {
    switch (band) {
      case "green":
        return "bg-green-100 text-green-800 border-green-300";
      case "red":
        return "bg-red-100 text-red-800 border-red-300";
      case "amber":
      default:
        return "bg-amber-100 text-amber-800 border-amber-300";
    }
  };

  const getIcon = () => {
    switch (band) {
      case "green":
        return <ShieldCheck className="w-3 h-3" />;
      case "red":
        return <ShieldAlert className="w-3 h-3" />;
      default:
        return <Shield className="w-3 h-3" />;
    }
  };

  return (
    <div
      className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${getBandColor()}`}
      title={`Trust Index: ${trustIndex}/100 (${band})`}
    >
      {getIcon()}
      <span>{trustIndex}</span>
    </div>
  );
};

export default TrustBadge;
