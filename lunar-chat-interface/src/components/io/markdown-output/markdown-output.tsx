// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

/* eslint-disable @typescript-eslint/no-unused-vars */
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from '@/components/ui/table';

interface MarkdownRendererProps {
  content: string;
}

const MarkdownOutput: React.FC<MarkdownRendererProps> = ({ content }) => {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        table: ({ node, ...props }) => <Table {...props} />,
        thead: ({ node, ...props }) => <TableHeader {...props} />,
        tbody: ({ node, ...props }) => <TableBody {...props} />,
        tr: ({ node, ...props }) => <TableRow {...props} />,
        th: ({ node, ...props }) => <TableHead {...props} />,
        td: ({ node, ...props }) => <TableCell {...props} />,
        h1: ({ node, ...props }) => <h1 className="text-3xl font-bold text-gray-900 my-6" {...props} />,
        h3: ({ node, ...props }) => <h3 className="text-xl font-semibold text-gray-800 my-4" {...props} />,
        ul: ({ node, ...props }) => (
          <ul
            className="list-disc list-outside pl-5 space-y-3 text-gray-800"
            {...props}
          />
        ),
        li: ({ node, ...props }) => (
          <li
            className="leading-relaxed marker:text-gray-600 [&>p]:m-0 [&>p]:inline"
            {...props}
          />
        ),
        p: ({ node, ...props }) => <p className="my-2" {...props} />,
        strong: ({ node, ...props }) => <strong className="font-semibold" {...props} />,
        hr: ({ node, ...props }) => <hr className="my-6 border-gray-300" {...props} />,
      }}
    >
      {content}
    </ReactMarkdown>
  );
};

export default MarkdownOutput;
