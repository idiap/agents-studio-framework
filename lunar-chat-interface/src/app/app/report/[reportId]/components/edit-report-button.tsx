// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { Button } from "@/components/ui/button";
import { Pencil } from "lucide-react";
import { useRouter } from "next/navigation";

interface EditReportButtonProps {
  reportId: string;
}

const EditReportButton: React.FC<EditReportButtonProps> = ({ reportId }) => {
  const router = useRouter();

  const handleEdit = () => {
    router.push(`/app/report/${reportId}/edit`);
  };

  return (
    <Button
      onClick={handleEdit}
      variant="outline"
      title="Edit Report"
      className="ml-2"
    >
      <Pencil className="w-4 h-4" />
      Edit
    </Button>
  );
};

export default EditReportButton;
