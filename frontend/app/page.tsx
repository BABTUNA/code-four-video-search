import Link from "next/link";

import { getVideos } from "@/lib/api";


function formatDuration(durationMs: number): string {
  const totalSeconds = Math.round(durationMs / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}


export default async function VideoLibraryPage() {
  const videos = await getVideos();

  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <div className="mb-8">
        <p className="mb-2 text-sm font-medium uppercase tracking-[0.2em] text-[var(--accent)]">
          Phase 1
        </p>
        <h1 className="text-4xl font-semibold tracking-tight">Video library</h1>
        <p className="mt-3 max-w-2xl text-[var(--muted)]">
          Open a video to configure segmentation and inspect its modality evidence.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {videos.map((video) => (
          <Link
            className="rounded-xl border border-[var(--border)] bg-[var(--panel)] p-5 transition hover:border-[var(--accent)]"
            href={`/videos/${video.media_id}`}
            key={video.media_id}
          >
            <div className="mb-8 flex h-32 items-center justify-center rounded-lg bg-[var(--panel-light)] text-4xl">
              ▶
            </div>
            <h2 className="font-medium">{video.filename}</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Duration {formatDuration(video.duration_ms)}
            </p>
          </Link>
        ))}
      </div>

      {videos.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--border)] p-10 text-center text-[var(--muted)]">
          No complete MP4 videos were discovered in c4-videos.
        </div>
      )}
    </main>
  );
}

