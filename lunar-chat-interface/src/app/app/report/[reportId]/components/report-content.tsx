// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";
import { Fragment, useMemo, useCallback } from "react";
import MarkdownOutput from "@/components/io/markdown-output/markdown-output";
import { LineChart } from "@/components/data-vis/line-chart";
import { BarChart } from "@/components/data-vis/bar-chart";
import lineChartData10y from "@/data/line_chart-10y.json";
import lineChartData20y from "@/data/line_chart-20y.json";
import candleData10y from "@/data/candle-data.json";
import candleData20y from "@/data/candle-data-20y.json";
import DynamicExpectedReturnsByAssetClass from "@/components/dynamic-expected_returns_by_asset_class";
import { DynamicCorrelationMatrix } from "@/components/dynamic-correlation-matrix";
import {
  TrustAnnotatedSection,
  parseAllAnnotations,
  type ParsedAnnotation,
} from "@/components/trust-annotation";

interface ReportContentProps {
  reportContent: string;
}

type ChartParser = (tagString: string) => React.ReactNode | null;
type VariablesMap = Record<string, React.ReactNode>;

/**
 * Process inner content for tags and variables (used inside trust annotation blocks).
 */
function processInnerContent(
  content: string,
  variables: VariablesMap,
  parseLineChart: ChartParser,
  parseBarChart: ChartParser
): (string | React.ReactNode)[] {
  const parts: (string | React.ReactNode)[] = [];
  let lastIndex = 0;

  const tagPattern = /<(\w+)\s+([^>]+)\/>/g;
  const variablePattern = /\{\{([^}]+)\}\}/g;

  const matches: Array<{
    type: "tag" | "variable";
    match: RegExpExecArray;
  }> = [];

  let tagMatch;
  while ((tagMatch = tagPattern.exec(content)) !== null) {
    matches.push({ type: "tag", match: tagMatch });
  }

  let varMatch;
  while ((varMatch = variablePattern.exec(content)) !== null) {
    matches.push({ type: "variable", match: varMatch });
  }

  matches.sort((a, b) => a.match.index - b.match.index);

  for (const { type, match } of matches) {
    const startIndex = match.index;
    const fullMatch = match[0];

    if (startIndex > lastIndex) {
      const textBefore = content.slice(lastIndex, startIndex);
      if (textBefore.trim()) {
        parts.push(textBefore);
      }
    }

    if (type === "tag") {
      const tagName = match[1];
      if (tagName === "LineChart") {
        const chartComponent = parseLineChart(fullMatch);
        parts.push(chartComponent || fullMatch);
      } else if (tagName === "BarChart") {
        const chartComponent = parseBarChart(fullMatch);
        parts.push(chartComponent || fullMatch);
      } else {
        parts.push(fullMatch);
      }
    } else if (type === "variable") {
      const variableName = match[1];
      if (variableName in variables) {
        parts.push(variables[variableName]);
      } else {
        parts.push(fullMatch);
      }
    }

    lastIndex = startIndex + fullMatch.length;
  }

  if (lastIndex < content.length) {
    const remainingText = content.slice(lastIndex);
    if (remainingText.trim()) {
      parts.push(remainingText);
    }
  }

  if (parts.length === 0 && content.trim()) {
    parts.push(content);
  }

  return parts;
}

const variables = {
  line_chart_10y: (
    <LineChart
      data={lineChartData10y}
      title="Expected Returns by Asset Class (10-Year Horizon)"
      height={500}
      showLegend={false}
    />
  ),
  line_chart_20y: (
    <LineChart
      data={lineChartData20y}
      title="Expected Returns by Asset Class (20-Year Horizon)"
      height={500}
      showLegend={false}
    />
  ),
  expected_returns_by_asset_class_10y: (
    <DynamicExpectedReturnsByAssetClass
      candleData={candleData10y}
      title="Expected Returns by Asset Class - 10 Years"
    />
  ),
  expected_returns_by_asset_class_20y: (
    <DynamicExpectedReturnsByAssetClass
      candleData={candleData20y}
      title="Expected Returns by Asset Class - 20 Years"
    />
  ),
  correlation_matrix: <DynamicCorrelationMatrix />,
};

const ReportContent: React.FC<ReportContentProps> = ({ reportContent }) => {
  const defaultVariables = useMemo(
    () => ({
      ...variables,
    }),
    []
  );

  const parseLineChartTag = useCallback(
    (tagString: string): React.ReactNode | null => {
      try {
        const seriesMatch = tagString.match(
          /series=\{(.+?)\}(?=\s+\w+=|\s*\/>)/
        );
        const titleMatch = tagString.match(/title="([^"]+)"/);
        const noteMatch = tagString.match(/note="([^"]+)"/);
        if (!seriesMatch) return null;
        const seriesStr = seriesMatch[1].trim();
        const jsonStr = `{${seriesStr}}`.replace(/'/g, '"');
        const seriesData = JSON.parse(jsonStr);
        const colors = [
          { border: "rgb(59, 130, 246)", bg: "rgba(59, 130, 246, 0.1)" },
          { border: "rgb(16, 185, 129)", bg: "rgba(16, 185, 129, 0.1)" },
          { border: "rgb(245, 158, 11)", bg: "rgba(245, 158, 11, 0.1)" },
          { border: "rgb(239, 68, 68)", bg: "rgba(239, 68, 68, 0.1)" },
          { border: "rgb(168, 85, 247)", bg: "rgba(168, 85, 247, 0.1)" },
          { border: "rgb(236, 72, 153)", bg: "rgba(236, 72, 153, 0.1)" },
        ];
        const allDates = new Set<string>();
        Object.values(seriesData).forEach((data: any) => {
          data.x.forEach((date: string) => allDates.add(date));
        });
        const sortedDates = Array.from(allDates).sort();
        const transformedData = {
          labels: sortedDates.map((date) => new Date(date).getTime()),
          datasets: Object.entries(seriesData).map(
            ([name, data]: [string, any], idx: number) => {
              const color = colors[idx % colors.length];
              const dateValueMap = new Map<string, number>();
              data.x.forEach((date: string, i: number) => {
                dateValueMap.set(date, data.y[i]);
              });
              return {
                label: name,
                data: sortedDates.map((date) => dateValueMap.get(date) ?? null),
                borderColor: color.border,
                backgroundColor: color.bg,
                fill: false,
                tension: 0.1,
              };
            }
          ),
        };

        return (
          <div className="my-6">
            <LineChart
              data={transformedData}
              title={titleMatch?.[1] || ""}
              height={400}
              showLegend={true}
            />
            {noteMatch?.[1] && (
              <p className="text-sm text-gray-600 italic mt-2">
                {noteMatch[1]}
              </p>
            )}
          </div>
        );
      } catch (error) {
        console.error("Error parsing LineChart tag:", error);
        return null;
      }
    },
    []
  );

  const parseBarChartTag = useCallback(
    (tagString: string): React.ReactNode | null => {
      try {
        const xMatch = tagString.match(/x=\[([^\]]+)\]/);
        const yMatch = tagString.match(/y=\[([^\]]+)\]/);
        const titleMatch = tagString.match(/title="([^"]+)"/);
        const noteMatch = tagString.match(/note="([^"]+)"/);

        if (!xMatch || !yMatch) return null;

        // Parse x values (strings)
        const xValues = xMatch[1]
          .split(",")
          .map((val) => val.trim().replace(/^["']|["']$/g, ""));

        // Parse y values (numbers)
        const yValues = yMatch[1]
          .split(",")
          .map((val) => parseFloat(val.trim()));

        // Transform data for BarChart component
        const transformedData = {
          labels: xValues,
          datasets: [
            {
              label: titleMatch?.[1] || "Data",
              data: yValues,
              backgroundColor: "rgba(59, 130, 246, 0.6)",
              borderColor: "rgb(59, 130, 246)",
              borderWidth: 1,
              fill: false,
              tension: 0,
            },
          ],
        };

        return (
          <div className="my-6">
            <BarChart
              data={transformedData}
              title={titleMatch?.[1] || ""}
              height={400}
            />
            {noteMatch?.[1] && (
              <p className="text-sm text-gray-600 italic mt-2">
                {noteMatch[1]}
              </p>
            )}
          </div>
        );
      } catch (error) {
        console.error("Error parsing BarChart tag:", error);
        return null;
      }
    },
    []
  );

  const processedContent = useMemo(() => {
    if (typeof reportContent !== "string") return [];

    const parts: (string | React.ReactNode)[] = [];
    let content = reportContent;
    let lastIndex = 0;

    // First, parse trust annotations
    const trustAnnotations = parseAllAnnotations(content);

    // Process custom tags (LineChart, etc.)
    const tagPattern = /<(\w+)\s+([^>]+)\/>/g;
    const variablePattern = /\{\{([^}]+)\}\}/g;

    // Trust annotation pattern for matching
    const trustStartPattern =
      /<!--\s*lunar\/component-id=(\S+)\s+lunar\/trust-start=(\d+)\/100\s+lunar\/confidence=(\d+)(?:\s+lunar\/band=(\S+))?(?:\s+lunar\/risk=([\d.]+))?(?:\s+lunar\/step-kind=(\S+))?.*?-->/g;
    const trustEndPattern = /<!--\s*lunar\/trust-end\s*-->/g;

    const matches: Array<{
      type: "tag" | "variable" | "trust-annotation";
      match: RegExpExecArray;
      annotation?: ParsedAnnotation;
    }> = [];

    // Add trust annotation matches
    for (const annotation of trustAnnotations) {
      // Create a synthetic match object for sorting
      const syntheticMatch = {
        0: content.slice(annotation.startPos, annotation.endPos),
        index: annotation.startPos,
        input: content,
      } as RegExpExecArray;
      matches.push({
        type: "trust-annotation",
        match: syntheticMatch,
        annotation,
      });
    }

    let tagMatch: RegExpExecArray | null;
    while ((tagMatch = tagPattern.exec(content)) !== null) {
      // Skip if inside a trust annotation block
      const isInsideAnnotation = trustAnnotations.some(
        (ann) =>
          tagMatch &&
          tagMatch.index >= ann.startPos &&
          tagMatch.index < ann.endPos
      );
      if (!isInsideAnnotation) {
        matches.push({ type: "tag", match: tagMatch });
      }
    }

    let varMatch: RegExpExecArray | null;
    while ((varMatch = variablePattern.exec(content)) !== null) {
      // Skip if inside a trust annotation block
      const isInsideAnnotation = trustAnnotations.some(
        (ann) =>
          varMatch &&
          varMatch.index >= ann.startPos &&
          varMatch.index < ann.endPos
      );
      if (!isInsideAnnotation) {
        matches.push({ type: "variable", match: varMatch });
      }
    }

    matches.sort((a, b) => a.match.index - b.match.index);

    // Filter out nested matches (keep only top-level)
    const filteredMatches = matches.filter((m, idx) => {
      if (m.type === "trust-annotation") return true;
      // Check if this match is inside any trust annotation
      return !matches.some(
        (other) =>
          other.type === "trust-annotation" &&
          other.annotation &&
          m.match.index > other.annotation.startPos &&
          m.match.index < other.annotation.endPos
      );
    });

    for (const { type, match, annotation } of filteredMatches) {
      const startIndex = match.index;
      const fullMatch = match[0];

      if (startIndex > lastIndex) {
        const textBefore = content.slice(lastIndex, startIndex);
        if (textBefore.trim()) {
          parts.push(textBefore);
        }
      }

      if (type === "trust-annotation" && annotation) {
        // Process the content inside the annotation
        const innerContent = annotation.content;

        // Recursively process inner content for tags/variables
        const innerParts = processInnerContent(
          innerContent,
          defaultVariables,
          parseLineChartTag,
          parseBarChartTag
        );

        // Wrap with trust annotation component
        parts.push(
          <TrustAnnotatedSection
            key={`trust-${annotation.annotation.componentId}-${startIndex}`}
            annotation={annotation.annotation}
          >
            {innerParts.map((innerPart, innerIdx) => (
              <Fragment key={innerIdx}>
                {typeof innerPart === "string" ? (
                  <MarkdownOutput content={innerPart} />
                ) : (
                  innerPart
                )}
              </Fragment>
            ))}
          </TrustAnnotatedSection>
        );
        lastIndex = annotation.endPos;
      } else if (type === "tag") {
        const tagName = match[1];

        if (tagName === "LineChart") {
          const chartComponent = parseLineChartTag(fullMatch);
          if (chartComponent) {
            parts.push(chartComponent);
          } else {
            parts.push(fullMatch);
          }
        } else if (tagName === "BarChart") {
          const chartComponent = parseBarChartTag(fullMatch);
          if (chartComponent) {
            parts.push(chartComponent);
          } else {
            parts.push(fullMatch);
          }
        } else {
          // Future tag types can be added here
          parts.push(fullMatch);
        }
        lastIndex = startIndex + fullMatch.length;
      } else if (type === "variable") {
        const variableName = match[1];
        if (variableName in defaultVariables) {
          parts.push(
            defaultVariables[variableName as keyof typeof defaultVariables]
          );
        } else {
          parts.push(fullMatch);
        }
        lastIndex = startIndex + fullMatch.length;
      }
    }
    if (lastIndex < content.length) {
      const remainingText = content.slice(lastIndex);
      if (remainingText.trim()) {
        parts.push(remainingText);
      }
    }

    if (parts.length === 0) {
      parts.push(content);
    }

    return parts;
  }, [reportContent, defaultVariables, parseLineChartTag, parseBarChartTag]);
  return (
    <div className="p-8">
      <div className="prose max-w-none text-gray-800 leading-relaxed">
        {processedContent.map((part, index) => (
          <Fragment key={index}>
            {typeof part === "string" ? (
              <MarkdownOutput content={part} />
            ) : (
              part
            )}
          </Fragment>
        ))}
      </div>
    </div>
  );
};

export default ReportContent;
