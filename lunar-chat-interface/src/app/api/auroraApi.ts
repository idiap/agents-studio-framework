// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { serverApiUrl } from '@/configuration'
import axios, { AxiosInstance } from 'axios'

const serverApi: AxiosInstance = axios.create({
  baseURL: serverApiUrl
})

serverApi.interceptors.request.use(async config => {
  config.headers['Access-Control-Allow-Origin'] = '*'
  return config
})

serverApi.interceptors.response.use(
  response => response,
  error => {
    return Promise.reject(error)
  }
)

export default serverApi
