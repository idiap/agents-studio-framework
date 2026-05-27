// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

const NoReportFound = () => {
  return (
    <div className="container mx-auto p-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-700">No Report Found</h1>
        <p className="text-gray-500 mt-2">
          No report content was found for this ID.
        </p>
      </div>
    </div>
  );
};

export default NoReportFound;
