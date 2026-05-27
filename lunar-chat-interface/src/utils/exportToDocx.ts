// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkGfm from "remark-gfm";
import remarkDocx from "remark-docx";
import type { RemarkDocxPlugin } from "remark-docx";
import { ImageRun } from "docx";
import { imageSize } from "image-size";
import { visit } from "unist-util-visit";
import type { Image } from "mdast";
import { saveAs } from "file-saver";
import {
  renderChartToBase64,
  parseLineChartTagToConfig,
  parseBarChartTagToConfig,
} from "./chartToImage";

// A4 page width in points minus margins (approximately 6.5 inches = 468 points)
// remark-docx uses default 1 inch margins, so content width is about 6.5 inches
const MAX_IMAGE_WIDTH = 600; // pixels - will be scaled proportionally

// Trust annotation patterns
const TRUST_START_PATTERN =
  /<!--\s*lunar\/component-id=\S+\s+lunar\/trust-start=\d+\/100\s+lunar\/confidence=\d+.*?-->/g;
const TRUST_END_PATTERN = /<!--\s*lunar\/trust-end\s*-->/g;

/**
 * Strip trust annotation comments from markdown content.
 * Keeps the content between annotations, removes only the annotation markers.
 */
export function stripTrustAnnotations(markdown: string): string {
  // Remove start annotations
  let result = markdown.replace(TRUST_START_PATTERN, "");
  // Remove end annotations
  result = result.replace(TRUST_END_PATTERN, "");
  // Clean up extra blank lines that may result from removing annotations
  result = result.replace(/\n{3,}/g, "\n\n");
  return result;
}

interface ChartImage {
  placeholder: string;
  base64DataUrl: string;
  title: string;
  note?: string;
}

/**
 * Extracts chart tags from markdown and renders them to images
 */
async function extractAndRenderCharts(
  markdown: string
): Promise<{ processedMarkdown: string; chartImages: ChartImage[] }> {
  const chartImages: ChartImage[] = [];
  let processedMarkdown = markdown;
  let chartIndex = 0;

  // Pattern to match chart tags
  const tagPattern = /<(LineChart|BarChart)\s+([^>]+)\/>/g;
  const matches: Array<{ fullMatch: string; tagName: string; index: number }> =
    [];

  let match;
  while ((match = tagPattern.exec(markdown)) !== null) {
    matches.push({
      fullMatch: match[0],
      tagName: match[1],
      index: match.index,
    });
  }

  // Process matches in reverse order to preserve indices
  for (const { fullMatch, tagName } of matches.reverse()) {
    const placeholder = `CHART_IMAGE_${chartIndex}`;
    let chartData = null;

    if (tagName === "LineChart") {
      chartData = parseLineChartTagToConfig(fullMatch);
    } else if (tagName === "BarChart") {
      chartData = parseBarChartTagToConfig(fullMatch);
    }

    if (chartData) {
      try {
        const base64Image = await renderChartToBase64(chartData.config, {
          width: 800,
          height: 400,
        });

        chartImages.unshift({
          placeholder,
          base64DataUrl: base64Image,
          title: chartData.title,
          note: chartData.note,
        });

        // Replace with markdown image syntax using data URL
        // Add blank line after chart note for spacing
        const imageMarkdown = chartData.note
          ? `\n\n![${chartData.title}](${base64Image})\n\n*${chartData.note}*\n\n`
          : `\n\n![${chartData.title}](${base64Image})\n\n`;

        processedMarkdown = processedMarkdown.replace(fullMatch, imageMarkdown);
        chartIndex++;
      } catch (error) {
        console.error(`Error rendering chart: ${error}`);
        processedMarkdown = processedMarkdown.replace(
          fullMatch,
          `\n\n**[Chart: ${
            chartData.title || "Untitled"
          } - could not be rendered]**\n\n`
        );
      }
    } else {
      processedMarkdown = processedMarkdown.replace(
        fullMatch,
        "\n\n**[Chart could not be rendered]**\n\n"
      );
    }
  }

  return { processedMarkdown, chartImages };
}

/**
 * Custom load function that handles data URLs
 */
async function loadImageData(url: string): Promise<ArrayBuffer> {
  if (url.startsWith("data:")) {
    const base64Data = url.split(",")[1];
    const binaryString = atob(base64Data);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
  }
  const response = await fetch(url);
  return response.arrayBuffer();
}

/**
 * Custom image plugin that scales images to fit document width
 */
const scaledImagePlugin = (): RemarkDocxPlugin => {
  const images = new Map<
    string,
    {
      type: "png" | "jpg" | "gif" | "bmp";
      width: number;
      height: number;
      data: ArrayBuffer;
    }
  >();

  return async ({ root }) => {
    const imageList: Image[] = [];

    visit(root, "image", (node: Image) => {
      imageList.push(node);
    });

    if (imageList.length !== 0) {
      const promises = new Map<string, Promise<void>>();

      imageList.forEach(({ url }) => {
        if (!images.has(url) && !promises.has(url)) {
          promises.set(
            url,
            (async () => {
              try {
                const data = await loadImageData(url);
                const sizeInfo = imageSize(new Uint8Array(data));
                const type = sizeInfo.type as "png" | "jpg" | "gif" | "bmp";

                if (!["png", "jpg", "gif", "bmp"].includes(type)) {
                  console.warn(`Unsupported image type: ${type}`);
                  return;
                }

                let width = sizeInfo.width || 800;
                let height = sizeInfo.height || 400;

                // Scale down to fit document width while maintaining aspect ratio
                if (width > MAX_IMAGE_WIDTH) {
                  const scale = MAX_IMAGE_WIDTH / width;
                  width = MAX_IMAGE_WIDTH;
                  height = Math.round(height * scale);
                }

                images.set(url, { type, width, height, data });
              } catch (e) {
                console.warn(`Failed to load image: ${url}`, e);
              }
            })()
          );
        }
      });

      await Promise.all(promises.values());
    }

    return {
      image: (node: Image) => {
        const data = images.get(node.url);
        if (!data) {
          return null;
        }

        const altText =
          node.alt || node.title
            ? {
                name: "",
                description: node.alt ?? undefined,
                title: node.title ?? undefined,
              }
            : undefined;

        return new ImageRun({
          type: data.type,
          data: data.data,
          transformation: {
            width: data.width,
            height: data.height,
          },
          altText,
        });
      },
    };
  };
};

/**
 * Adds blank lines after tables in markdown for better spacing in the document
 */
function addSpacingAfterTables(markdown: string): string {
  // Match markdown tables (lines starting with |) and add extra newline after them
  // This regex matches table blocks and ensures there's a blank line after
  return markdown.replace(/(\|[^\n]+\|\n)+(?!\n\n)/g, (match) => match + "\n");
}

export async function exportMarkdownToDocx(
  markdown: string,
  filename: string = "report.docx"
) {
  try {
    // Strip trust annotations before processing
    const markdownWithoutAnnotations = stripTrustAnnotations(markdown);

    // Extract and render charts to images
    const { processedMarkdown } = await extractAndRenderCharts(
      markdownWithoutAnnotations
    );

    // Add spacing after tables
    const spacedMarkdown = addSpacingAfterTables(processedMarkdown);

    // Convert markdown to DOCX using remark with custom plugins
    const processor = unified()
      .use(remarkParse)
      .use(remarkGfm)
      .use(remarkDocx, {
        plugins: [scaledImagePlugin()],
      });

    const doc = await processor.process(spacedMarkdown);

    // Create blob from the result
    const buffer = await (doc.result as Promise<ArrayBuffer>);
    const blob = new Blob([buffer], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });

    // Trigger download
    saveAs(blob, filename);
  } catch (error) {
    console.error("Error exporting to DOCX:", error);
    throw error;
  }
}
