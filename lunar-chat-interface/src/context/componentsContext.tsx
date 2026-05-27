// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { ComponentModel } from "@/app/app/agents/[id]/editor/models/component";
import { createContext, useContext, useState, ReactNode } from "react";

type ComponentsContextType = {
  components: ComponentModel[];
  setComponents: (components: ComponentModel[]) => void;
};

const ComponentsContext = createContext<ComponentsContextType | undefined>(
  undefined,
);

type ComponentsProviderProps = {
  initialComponents?: ComponentModel[];
  children: ReactNode;
};

export function ComponentsProvider({
  initialComponents = [],
  children,
}: ComponentsProviderProps) {
  const [components, setComponents] =
    useState<ComponentModel[]>(initialComponents);

  return (
    <ComponentsContext.Provider value={{ components, setComponents }}>
      {children}
    </ComponentsContext.Provider>
  );
}

export function useComponents(): ComponentsContextType {
  const context = useContext(ComponentsContext);
  if (!context) {
    throw new Error("useComponents must be used within a ComponentsProvider");
  }
  return context;
}
