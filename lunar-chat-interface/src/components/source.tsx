// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Badge } from "./ui/badge";
// import Image from "next/image";

interface SourceProps {
  url: string;
}

const Source: React.FC<SourceProps> = ({ url }) => {
  // const faviconUrl = url
  //   ? `https://www.google.com/s2/favicons?domain=${new URL(
  //     url
  //   ).hostname}`
  //   : undefined;
  return <Badge
    className="mt-4 mx-1 cursor-pointer hover:bg-gray-100 transition-colors"
    onClick={() => window.open(url, '_blank')}
    variant="outline"
  >
    {/* {faviconUrl && (
      <Image
        src={faviconUrl}
        alt="favicon"
        width={16}
        height={16}
        className="w-4 h-4 mr-2 inline-block"
      />
    )} */}
    {url.split('/').slice(2).at(0)}
  </Badge>

}

export default Source
