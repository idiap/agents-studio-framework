// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

/**
 * Parse a Server-Sent Events (SSE) stream, correctly handling chunk boundaries.
 *
 * Raw `reader.read()` chunks may split SSE events across multiple reads.
 * Naïvely splitting by "\n" can produce partial JSON payloads that fail to
 * parse, silently dropping text deltas (especially small ones like "\n").
 *
 * This helper buffers incomplete lines across reads so that every `data:`
 * payload is reassembled before being passed to the callback.
 */
export async function parseSSEStream(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  onEvent: (event: { type: string; [key: string]: unknown }) => void,
): Promise<void> {
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // SSE events are separated by "\n\n". Process only fully received events.
    const parts = buffer.split("\n\n");

    // The last element is either "" (if the buffer ended with "\n\n")
    // or an incomplete event that we need to keep in the buffer.
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const lines = part.split("\n");

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;

        const payload = line.slice(6);
        if (payload === "[DONE]") continue;

        try {
          const event = JSON.parse(payload);
          onEvent(event);
        } catch {
          // Skip malformed JSON (shouldn't happen with proper buffering)
        }
      }
    }
  }

  // Flush any remaining buffer content
  if (buffer.trim()) {
    const lines = buffer.split("\n");
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;

      const payload = line.slice(6);
      if (payload === "[DONE]") continue;

      try {
        const event = JSON.parse(payload);
        onEvent(event);
      } catch {
        // Skip malformed JSON
      }
    }
  }
}
