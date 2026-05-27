// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

interface PageContainerProps {
  children: React.ReactNode;
}

const PageContainer: React.FC<PageContainerProps> = ({ children }) => {
  return (
    <div className="flex-1 min-h-0 flex flex-col overflow-auto bg-background -mt-16">
      <div className="mx-auto w-full max-w-6xl px-6 pt-22 pb-10">
        <div className="mx-auto w-full max-w-4xl flex flex-col gap-6">
          {children}
        </div>
      </div>
    </div>
  );
};

export default PageContainer;
