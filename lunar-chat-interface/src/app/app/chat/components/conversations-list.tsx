// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { useState } from "react";
import { Search } from "@/components/ui/search";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { SearchIcon } from "lucide-react";

const ConversationsList = () => {
  const [searchText, setSearchText] = useState("");
  // const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);
  const [searchResults, setSearchResults] = useState<string[]>([]);
  const [searchInputValue, setSearchInputValue] = useState("");
  const conversations: { title: string; time: string; icon?: React.ReactNode }[] = [
    {
      title: 'Conversation about AI',
      time: '2 hours ago',
      icon: undefined
    },
    {
      title: 'Project planning',
      time: '5 hours ago',
      icon: undefined
    },
    {
      title: 'Technical discussion',
      time: 'Yesterday',
      icon: undefined
    },
    {
      title: 'Meeting notes',
      time: 'Last week',
      icon: undefined
    }
  ];

  const filteredConversations = conversations.filter(conversation =>
    conversation.title.toLowerCase().includes(searchText.toLowerCase())
  );

  const handleSearch = (value: string) => {
    setSearchInputValue(value);
    const results = conversations
      .filter(conv => conv.title.toLowerCase().includes(value.toLowerCase()))
      .map(conv => conv.title);
    setSearchResults(results);
  };

  // const handleSearchItemClick = () => {
  //   setIsSearchModalOpen(true);
  // };

  // const handleModalClose = () => {
  //   setIsSearchModalOpen(false);
  //   setSearchInputValue("");
  //   setSearchResults([]);
  // };

  return (
    <div className="flex flex-col gap-4 mt-4">
      <div className="flex items-center gap-2">
        <DialogTrigger className="flex items-center gap-2">
          <SearchIcon />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="border-b border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </DialogTrigger>
      </div>
      <div className="flex flex-col">
        {filteredConversations.map((item) => (
          <div key={item.title} className="flex items-center gap-2">
            {item.icon}
            <span>{item.title}</span>
          </div>
        ))}
      </div>

      <Dialog>
        <DialogContent className="p-4">
          <DialogHeader>
            <DialogTitle className="text-lg font-semibold">
              Search Conversations
            </DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-4">
            <Search
              placeholder="Search conversations..."
              value={searchInputValue}
              onChange={(e) => handleSearch(e.target.value)}
            />
            <div className="flex flex-col">
              {searchResults.map((item) => (
                <div key={item} className="cursor-pointer hover:bg-gray-50 rounded p-2">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default ConversationsList;