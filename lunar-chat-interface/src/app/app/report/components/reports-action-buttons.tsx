// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

'use client'

import { Button } from '@/components/ui/button';
import { buildReportAction } from '@/actions/build-report-action';
import { buildComparativeReportAction } from '@/actions/build-comparative-report-action';
import { useState } from 'react';
import { toast } from 'sonner';

export function ReportsActionButtons() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [isGeneratingComparative, setIsGeneratingComparative] = useState(false);

  const handleGenerateReport = async () => {
    setIsGenerating(true);
    try {
      await buildReportAction();
      toast.success('Report generated successfully');
    } catch (error) {
      toast.error('Failed to generate report');
      console.error(error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateComparativeReport = async () => {
    setIsGeneratingComparative(true);
    try {
      await buildComparativeReportAction();
      toast.success('Comparative report generated successfully');
    } catch (error) {
      toast.error('Failed to generate comparative report');
      console.error(error);
    } finally {
      setIsGeneratingComparative(false);
    }
  };

  return (
    <div className="flex gap-2">
      <Button 
        variant="outline" 
        onClick={handleGenerateReport}
        disabled={isGenerating}
      >
        {isGenerating ? 'Generating...' : 'Generate New Report'}
      </Button>
      <Button 
        onClick={handleGenerateComparativeReport}
        disabled={isGeneratingComparative}
      >
        {isGeneratingComparative ? 'Creating...' : 'Create Comparative Report'}
      </Button>
    </div>
  );
}