export type Modality = "visual" | "audio" | "transcript" | "ocr";

export type RunStatus =
  | "queued"
  | "running"
  | "completed"
  | "completed_with_errors"
  | "failed";

export interface ProcessingConfiguration {
  segment_duration_ms: number;
  segment_overlap_ms: number;
  modalities: Modality[];
  max_segments: number | null;
}

export interface ProcessingRun {
  run_id: string;
  media_id: string;
  status: RunStatus;
  configuration: ProcessingConfiguration;
  completed_items: number;
  failed_items: number;
  total_items: number;
  error: string | null;
  created_at: string;
}

export interface MediaSummary {
  media_id: string;
  filename: string;
  duration_ms: number;
  file_url: string;
}

export interface MediaDetails extends MediaSummary {
  processing_runs: ProcessingRun[];
}

export interface Evidence {
  run_id: string;
  segment_id: string;
  media_id: string;
  start_ms: number;
  end_ms: number;
  modality: Modality;
  type: string;
  content: string;
  attributes: Record<string, unknown>;
  confidence: number | null;
  processor: {
    model: string;
    version: string;
  };
}

export interface SegmentResult {
  segment: {
    segment_id: string;
    media_id: string;
    start_ms: number;
    end_ms: number;
  };
  evidence: Evidence[];
}

export interface ProcessingError {
  run_id: string;
  segment_id: string;
  modality: Modality;
  message: string;
  created_at: string;
}
