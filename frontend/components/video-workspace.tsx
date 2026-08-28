"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

import {
  Evidence,
  MediaDetails,
  Modality,
  ProcessingError,
  ProcessingRun,
  SegmentResult,
} from "@/lib/types";


const MODALITIES: Modality[] = ["visual", "audio", "transcript", "ocr"];
const FINISHED_STATUSES = ["completed", "completed_with_errors", "failed"];


interface VideoWorkspaceProperties {
  apiBaseUrl: string;
  initialVideo: MediaDetails;
}


interface EvidenceMetrics {
  assetExtractionSeconds: number;
  processorSeconds: number;
  costUsd: number | null;
}


function formatTimestamp(timestampMs: number): string {
  const totalSeconds = Math.floor(timestampMs / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}


function formatDuration(seconds: number): string {
  return seconds < 1 ? `${Math.round(seconds * 1000)} ms` : `${seconds.toFixed(2)} s`;
}


function getEvidenceMetrics(evidence: Evidence): EvidenceMetrics | null {
  const metrics = evidence.attributes.metrics;
  if (!metrics || typeof metrics !== "object" || Array.isArray(metrics)) {
    return null;
  }

  const values = metrics as Record<string, unknown>;
  if (
    typeof values.asset_extraction_seconds !== "number" ||
    typeof values.processor_seconds !== "number"
  ) {
    return null;
  }

  return {
    assetExtractionSeconds: values.asset_extraction_seconds,
    processorSeconds: values.processor_seconds,
    costUsd: typeof values.cost_usd === "number" ? values.cost_usd : null,
  };
}


async function fetchJson<Response>(url: string): Promise<Response> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json() as Promise<Response>;
}


export function VideoWorkspace({
  apiBaseUrl,
  initialVideo,
}: VideoWorkspaceProperties) {
  const videoElement = useRef<HTMLVideoElement>(null);
  const [durationSeconds, setDurationSeconds] = useState(30);
  const [overlapSeconds, setOverlapSeconds] = useState(5);
  const [maxSegments, setMaxSegments] = useState(1);
  const [modalities, setModalities] = useState<Modality[]>(MODALITIES);
  const [runs, setRuns] = useState(initialVideo.processing_runs);
  const [selectedRunId, setSelectedRunId] = useState(
    initialVideo.processing_runs[0]?.run_id ?? "",
  );
  const [segments, setSegments] = useState<SegmentResult[]>([]);
  const [processingErrors, setProcessingErrors] = useState<ProcessingError[]>([]);
  const [selectedSegmentId, setSelectedSegmentId] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const selectedRun = runs.find((run) => run.run_id === selectedRunId);
  const selectedSegment = segments.find(
    (result) => result.segment.segment_id === selectedSegmentId,
  );
  const selectedMetrics =
    selectedSegment?.evidence
      .map(getEvidenceMetrics)
      .filter((metrics) => metrics !== null) ?? [];
  const extractionSeconds = selectedMetrics[0]?.assetExtractionSeconds ?? 0;
  const processorSeconds = selectedMetrics.reduce(
    (total, metrics) => total + metrics.processorSeconds,
    0,
  );
  const segmentCost = selectedMetrics.reduce(
    (total, metrics) => total + (metrics.costUsd ?? 0),
    0,
  );
  const hasReportedCost = selectedMetrics.some((metrics) => metrics.costUsd !== null);

  useEffect(() => {
    if (!selectedRunId) {
      return;
    }

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function refreshRun() {
      const run = await fetchJson<ProcessingRun>(
        `${apiBaseUrl}/api/processing-runs/${selectedRunId}`,
      );

      if (cancelled) {
        return;
      }

      setRuns((currentRuns) =>
        currentRuns.map((currentRun) =>
          currentRun.run_id === run.run_id ? run : currentRun,
        ),
      );

      const [nextSegments, nextErrors] = await Promise.all([
        fetchJson<SegmentResult[]>(
          `${apiBaseUrl}/api/processing-runs/${selectedRunId}/segments`,
        ),
        fetchJson<ProcessingError[]>(
          `${apiBaseUrl}/api/processing-runs/${selectedRunId}/errors`,
        ),
      ]);

      if (!cancelled) {
        setSegments(nextSegments);
        setProcessingErrors(nextErrors);
        setSelectedSegmentId((currentId) =>
          currentId || nextSegments[0]?.segment.segment_id || "",
        );
      }

      if (!FINISHED_STATUSES.includes(run.status)) {
        timer = setTimeout(refreshRun, 1000);
      }
    }

    refreshRun().catch(() => setError("Could not load processing results."));

    return () => {
      cancelled = true;
      if (timer) {
        clearTimeout(timer);
      }
    };
  }, [apiBaseUrl, selectedRunId]);

  function toggleModality(modality: Modality) {
    setModalities((currentModalities) =>
      currentModalities.includes(modality)
        ? currentModalities.filter((item) => item !== modality)
        : [...currentModalities, modality],
    );
  }

  async function startProcessing(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (modalities.length === 0) {
      setError("Select at least one modality.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/videos/${initialVideo.media_id}/processing-runs`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            segment_duration_ms: durationSeconds * 1000,
            segment_overlap_ms: overlapSeconds * 1000,
            modalities,
            max_segments: maxSegments,
          }),
        },
      );

      if (!response.ok) {
        const responseBody = await response.json();
        const message =
          typeof responseBody.detail === "string"
            ? responseBody.detail
            : "Invalid processing settings.";
        throw new Error(message);
      }

      const run = (await response.json()) as ProcessingRun;
      setRuns((currentRuns) => [run, ...currentRuns]);
      setSelectedRunId(run.run_id);
      setSegments([]);
      setProcessingErrors([]);
      setSelectedSegmentId("");
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : "Processing failed",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  function selectSegment(segment: SegmentResult) {
    setSelectedSegmentId(segment.segment.segment_id);
    if (videoElement.current) {
      videoElement.current.currentTime = segment.segment.start_ms / 1000;
      videoElement.current.play().catch(() => undefined);
    }
  }

  const processedItems =
    (selectedRun?.completed_items ?? 0) + (selectedRun?.failed_items ?? 0);

  return (
    <div className="mt-5 grid gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(340px,0.8fr)]">
      <section>
        <h1 className="mb-4 text-3xl font-semibold">{initialVideo.filename}</h1>
        <video
          className="aspect-video w-full rounded-xl bg-black"
          controls
          ref={videoElement}
          src={`${apiBaseUrl}${initialVideo.file_url}`}
        />

        <div className="mt-6 rounded-xl border border-[var(--border)] bg-[var(--panel)] p-5">
          <div className="mb-4 flex items-center justify-between gap-4">
            <h2 className="text-lg font-medium">Processed segments</h2>
            {runs.length > 0 && (
              <select
                className="rounded-md border border-[var(--border)] bg-[var(--panel-light)] px-3 py-2 text-sm"
                onChange={(event) => {
                  setSelectedRunId(event.target.value);
                  setSegments([]);
                  setProcessingErrors([]);
                  setSelectedSegmentId("");
                }}
                value={selectedRunId}
              >
                {runs.map((run) => (
                  <option key={run.run_id} value={run.run_id}>
                    {run.run_id} · {run.status}
                  </option>
                ))}
              </select>
            )}
          </div>

          {selectedRun && (
            <p className="mb-4 text-sm text-[var(--muted)]">
              {processedItems} of {selectedRun.total_items} items processed
              {selectedRun.failed_items > 0 && ` · ${selectedRun.failed_items} failed`}
            </p>
          )}

          {selectedRun?.error && (
            <p className="mb-4 rounded-md bg-red-950/30 p-3 text-sm text-red-300">
              {selectedRun.error}
            </p>
          )}

          <div className="max-h-[420px] space-y-2 overflow-y-auto">
            {segments.map((result) => (
              <button
                className={`w-full rounded-lg border p-3 text-left transition ${
                  result.segment.segment_id === selectedSegmentId
                    ? "border-[var(--accent)] bg-[var(--panel-light)]"
                    : "border-[var(--border)] hover:border-slate-500"
                }`}
                key={result.segment.segment_id}
                onClick={() => selectSegment(result)}
                type="button"
              >
                <span className="font-medium">
                  {formatTimestamp(result.segment.start_ms)}–
                  {formatTimestamp(result.segment.end_ms)}
                </span>
                <span className="ml-3 text-sm text-[var(--muted)]">
                  {result.evidence.length} evidence records
                </span>
              </button>
            ))}
          </div>

          {!selectedRun && (
            <p className="text-sm text-[var(--muted)]">
              Create a processing run to inspect segment evidence.
            </p>
          )}
        </div>
      </section>

      <aside className="space-y-6">
        <form
          className="rounded-xl border border-[var(--border)] bg-[var(--panel)] p-5"
          onSubmit={startProcessing}
        >
          <h2 className="mb-4 text-lg font-medium">New processing run</h2>

          <label className="mb-4 block text-sm">
            <span className="mb-2 block text-[var(--muted)]">Segment duration</span>
            <input
              className="w-full rounded-md border border-[var(--border)] bg-[var(--panel-light)] px-3 py-2"
              max="60"
              min="1"
              onChange={(event) => setDurationSeconds(Number(event.target.value))}
              type="number"
              value={durationSeconds}
            />
          </label>

          <label className="mb-5 block text-sm">
            <span className="mb-2 block text-[var(--muted)]">Overlap seconds</span>
            <input
              className="w-full rounded-md border border-[var(--border)] bg-[var(--panel-light)] px-3 py-2"
              min="0"
              onChange={(event) => setOverlapSeconds(Number(event.target.value))}
              type="number"
              value={overlapSeconds}
            />
          </label>

          <label className="mb-5 block text-sm">
            <span className="mb-2 block text-[var(--muted)]">
              Maximum segments (cost guard)
            </span>
            <input
              className="w-full rounded-md border border-[var(--border)] bg-[var(--panel-light)] px-3 py-2"
              max="1000"
              min="1"
              onChange={(event) => setMaxSegments(Number(event.target.value))}
              type="number"
              value={maxSegments}
            />
          </label>

          <fieldset className="mb-5">
            <legend className="mb-2 text-sm text-[var(--muted)]">Modalities</legend>
            <div className="grid grid-cols-2 gap-2">
              {MODALITIES.map((modality) => (
                <label
                  className="flex items-center gap-2 rounded-md border border-[var(--border)] px-3 py-2 text-sm"
                  key={modality}
                >
                  <input
                    checked={modalities.includes(modality)}
                    onChange={() => toggleModality(modality)}
                    type="checkbox"
                  />
                  <span className="capitalize">{modality}</span>
                </label>
              ))}
            </div>
          </fieldset>

          {error && <p className="mb-4 text-sm text-red-400">{error}</p>}

          <button
            className="w-full rounded-md bg-[var(--accent)] px-4 py-2 font-medium text-black disabled:cursor-not-allowed disabled:opacity-50"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? "Starting…" : "Process video"}
          </button>
        </form>

        <div className="rounded-xl border border-[var(--border)] bg-[var(--panel)] p-5">
          <h2 className="mb-4 text-lg font-medium">Segment evidence</h2>
          {selectedMetrics.length > 0 && (
            <div className="mb-4 grid grid-cols-2 gap-2 text-sm">
              <div className="rounded-md bg-[var(--panel-light)] p-3">
                <span className="block text-xs text-[var(--muted)]">Elapsed</span>
                {formatDuration(extractionSeconds + processorSeconds)}
              </div>
              <div className="rounded-md bg-[var(--panel-light)] p-3">
                <span className="block text-xs text-[var(--muted)]">Model cost</span>
                {hasReportedCost ? `$${segmentCost.toFixed(6)}` : "Not reported"}
              </div>
            </div>
          )}
          <div className="space-y-3">
            {selectedSegment?.evidence.map((evidence) => {
              const metrics = getEvidenceMetrics(evidence);
              return (
                <article
                  className="rounded-lg border border-[var(--border)] bg-[var(--panel-light)] p-4"
                  key={evidence.modality}
                >
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <span className="text-sm font-medium capitalize text-[var(--accent)]">
                      {evidence.modality}
                    </span>
                    <span className="text-right text-xs text-[var(--muted)]">
                      {metrics && `${formatDuration(metrics.processorSeconds)} · `}
                      {metrics?.costUsd !== null && metrics?.costUsd !== undefined
                        ? `$${metrics.costUsd.toFixed(6)} · `
                        : ""}
                      {evidence.processor.model}
                    </span>
                  </div>
                  <p className="text-sm leading-6">{evidence.content}</p>
                  <pre className="mt-3 overflow-x-auto text-xs text-[var(--muted)]">
                    {JSON.stringify(evidence.attributes, null, 2)}
                  </pre>
                </article>
              );
            })}
          </div>

          {!selectedSegment && (
            <p className="text-sm text-[var(--muted)]">
              Select a processed segment to inspect its evidence.
            </p>
          )}

          {processingErrors.length > 0 && (
            <div className="mt-5 border-t border-[var(--border)] pt-4">
              <h3 className="mb-3 text-sm font-medium text-red-400">
                Processing issues
              </h3>
              <div className="space-y-2">
                {processingErrors.map((processingError) => (
                  <p
                    className="rounded-md bg-red-950/30 p-3 text-xs text-red-300"
                    key={`${processingError.segment_id}:${processingError.modality}`}
                  >
                    <span className="font-medium capitalize">
                      {processingError.modality}
                    </span>{" "}
                    · {processingError.segment_id}: {processingError.message}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
