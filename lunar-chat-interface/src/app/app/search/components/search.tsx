// SPDX-FileCopyrightText: Copyright © 2024 Lunarbase (https://lunarbase.ai/) <contact@lunarbase.ai>
//
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-or-later

"use client"
import { useState } from "react"
import { SessionProvider } from "next-auth/react"
import SearchInput from "./searchInput"
import { searchResourceAction } from "@/actions/search"
import { ResourceHighlight } from "@/models/resource"
import MarkdownOutput from "@/components/io/markdown-output/markdown-output"
import { Card, CardContent } from "@/components/ui/card"
import Source from "@/components/source"

function preserveMarkdownLinks(text: string): string {
  const lines = text.split('\n');
  let combined = '';
  let buffer = '';
  let insideLink = false;

  for (const line of lines) {
    if (!insideLink) {
      buffer = line;
    } else {
      buffer += ' ' + line.trim();
    }

    const openBracketCount = (buffer.match(/\[(?!.*\])/g) || []).length;
    const closeBracketCount = (buffer.match(/\](?!.*\[)/g) || []).length;
    const openParenCount = (buffer.match(/\((?!.*\))/g) || []).length;
    const closeParenCount = (buffer.match(/\)(?!.*\()/g) || []).length;

    if (openBracketCount === closeBracketCount && openParenCount === closeParenCount) {
      combined += buffer + '\n';
      buffer = '';
      insideLink = false;
    } else {
      insideLink = true;
    }
  }
  if (buffer) combined += buffer + '\n';

  return combined.trim();
}

const Search: React.FC = () => {
  return <SessionProvider>
    <SearchContent />
  </SessionProvider>
}

// const scrollToBottom = () => {
//   setTimeout(() => {
//     const scroller = document.getElementById('scroller');
//     scroller?.scrollTo({
//       top: scroller.scrollHeight,
//       behavior: 'smooth'
//     });
//   }, 50);
// }

const SearchContent: React.FC = () => {

  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [resources, setResources] = useState<ResourceHighlight[]>([])
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement> | React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
  }
  const handleSubmit = async () => {
    setLoading(true)
    const query = input
    const resources = await searchResourceAction(query)
    setResources(resources)
    setLoading(false)
  }

  return <>
    <SessionProvider>
      <div className="flex flex-col justify-center mt-20 absolute z-10 w-full">
        <SearchInput
          resources={resources}
          handleSubmit={handleSubmit}
          input={input}
          handleInputChange={handleInputChange}
          loading={loading}
        />
        <div id="scroller" className="mb-10">
          {resources.map((resource, index) => (
            <Card className="my-4" key={index}>
              <CardContent>
                {preserveMarkdownLinks(resource.highlight).split('\n').map((line, index) => (
                  <MarkdownOutput key={index} content={line} />
                ))}
                <Source url={`${process.env.NEXT_PUBLIC_AURORA_FRONTEND_ADDRESS}/resource/${resource.resource_external_reference}`} />
                <Source url={`https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2017/decreto/d${resource.resource_external_reference}.htm`} />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </SessionProvider>
  </>
}

export default Search
