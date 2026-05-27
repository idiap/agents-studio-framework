// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client"

import { ChatRequestOptions } from "ai"
import SendButton from "@/components/send-button";
import { SearchTextArea } from "@/components/text-area";
import { ResourceHighlight } from "@/models/resource";

interface ChatInputProps {
  resources: ResourceHighlight[];
  handleSubmit: (event?: {
    preventDefault?: () => void;
  }, chatRequestOptions?: ChatRequestOptions) => void
  input: string
  handleInputChange: (e: React.ChangeEvent<HTMLInputElement> | React.ChangeEvent<HTMLTextAreaElement>) => void
  loading: boolean
}

const SearchInput: React.FC<ChatInputProps> = ({
  handleSubmit,
  input,
  handleInputChange,
  loading
}) => {
  // const router = useRouter()
  // const [reportLoading, setReportLoading] = useState<boolean>(false)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSubmit()
    }
  }
  // const createReport = async () => {
  //   setReportLoading(true)
  //   const context = resources.reduce((acc, resource) => acc + resource.highlight, '\n')
  //   try {
  //     const newReportId = await buildReportAction(context)
  //     router.push(`/editor/${newReportId}`)
  //   } catch (e) {
  //     console.error(e)
  //     toast('Error', { description: 'There was an error while creating a new report' })
  //   }
  //   setReportLoading(false)
  // }
  return <div className="sticky bottom-0 z-10 right-0 left-0 w-full bg-white">
    <div style={{ backgroundColor: "#ffffff", borderColor: "rgba(13, 24, 28, 0.12)" }} className="flex flex-col p-4 w-full bg-transparent overflow-hidden shadow-lg rounded-lg border-[1px] mb-4">
      <SearchTextArea value={input} onChange={handleInputChange} onKeyDown={handleKeyDown} placeholder='Search' />
      <div className="flex items-center mt-1 gap-2">
        <div className="ml-auto" />
        {/* <Button disabled={resources.length === 0 || reportLoading} onClick={createReport}>
          {reportLoading
            ? <LoaderIcon className="animate-spin" />
            : 'Generate Report'
          }
        </Button> */}
        <SendButton
          onSubmit={handleSubmit}
          value={input}
          loading={loading}
        />
      </div>
    </div>
  </div>
}

export default SearchInput
