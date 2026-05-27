// Copyright © 2024 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo.gusicuma@idiap.ch>
//
// SPDX-License-Identifier: GPL-3.0-or-later

import Search from './components/search';

export default async function SearchPage() {
  return <>
    <div className='relative flex flex-col max-w-[800px] w-full gap-8 min-h-[calc(100vh-66px)] mb-0 mr-auto ml-auto'>
      <Search />
    </div>
  </>
}
