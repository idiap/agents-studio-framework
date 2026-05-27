// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { createRouteHandler } from 'uploadthing/next';

import { ourFileRouter } from '@/lib/uploadthing';

export const { GET, POST } = createRouteHandler({ router: ourFileRouter });
