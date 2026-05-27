// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Report } from '@/models/report';
import { FileText, TrendingUp, Clock, BarChart3 } from 'lucide-react';

interface ReportsStatsProps {
  reports: Report[];
}

export function ReportsStats({ reports }: ReportsStatsProps) {
  const totalReports = reports.length;
  const recentReports = reports.slice(0, 3).length; // Last 3 reports as "recent"

  const stats = [
    {
      title: 'Total Reports',
      value: totalReports.toString(),
      description: 'All time',
      icon: FileText,
      color: 'text-blue-600'
    },
    {
      title: 'Recent Reports',
      value: recentReports.toString(),
      description: 'This week',
      icon: Clock,
      color: 'text-green-600'
    },
    {
      title: 'Analysis Types',
      value: '4',
      description: 'Categories available',
      icon: BarChart3,
      color: 'text-purple-600'
    },
    {
      title: 'Success Rate',
      value: '98%',
      description: 'Report generation',
      icon: TrendingUp,
      color: 'text-orange-600'
    }
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => {
        const IconComponent = stat.icon;
        return (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <IconComponent className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">
                {stat.description}
              </p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}