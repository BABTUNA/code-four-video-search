import Link from "next/link";

import { VideoWorkspace } from "@/components/video-workspace";
import { API_BASE_URL, getVideo } from "@/lib/api";


interface VideoPageProperties {
  params: Promise<{ mediaId: string }>;
}


export default async function VideoPage({ params }: VideoPageProperties) {
  const { mediaId } = await params;
  const video = await getVideo(mediaId);

  return (
    <main className="mx-auto max-w-7xl px-6 py-8">
      <Link className="text-sm text-[var(--muted)] hover:text-white" href="/">
        ← Video library
      </Link>
      <VideoWorkspace apiBaseUrl={API_BASE_URL} initialVideo={video} />
    </main>
  );
}

