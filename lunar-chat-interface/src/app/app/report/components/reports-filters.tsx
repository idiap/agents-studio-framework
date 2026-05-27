// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { useState } from "react";

interface ReportsFiltersProps {
  onSearchChange: (search: string) => void;
  onFilterChange: (filter: string) => void;
  onSortChange: (sort: string) => void;
  totalReports: number;
}

export function ReportsFilters({
  onSearchChange,
  totalReports,
}: ReportsFiltersProps) {
  const [searchTerm, setSearchTerm] = useState("");
  // const [activeFilter, setActiveFilter] = useState('all');
  // const [activeSort, setActiveSort] = useState('newest');

  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
    onSearchChange(value);
  };

  // const handleFilterChange = (filter: string) => {
  //   setActiveFilter(filter);
  //   onFilterChange(filter);
  // };

  // const handleSortChange = (sort: string) => {
  //   setActiveSort(sort);
  //   onSortChange(sort);
  // };

  return (
    <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between w-full">
      <div className="flex flex-col sm:flex-row gap-2 w-full">
        {/* Search */}
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
          <Input
            placeholder="Search reports..."
            value={searchTerm}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-9 w-full"
          />
        </div>

        {/* Filter */}
        {/* <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="gap-2">
              <Filter className="w-4 h-4" />
              Filter
              {activeFilter !== 'all' && (
                <Badge variant="secondary" className="ml-1">
                  {activeFilter}
                </Badge>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => handleFilterChange('all')}>
              All Reports
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleFilterChange('market')}>
              Market Analysis
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleFilterChange('portfolio')}>
              Portfolio Reviews
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleFilterChange('risk')}>
              Risk Assessments
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleFilterChange('comparative')}>
              Comparative Analysis
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu> */}

        {/* Sort */}
        {/* <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="gap-2">
              <SortDesc className="w-4 h-4" />
              Sort
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => handleSortChange('newest')}>
              Newest First
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleSortChange('oldest')}>
              Oldest First
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleSortChange('title')}>
              By Title (A-Z)
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleSortChange('type')}>
              By Type
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu> */}
      </div>
    </div>
  );
}
