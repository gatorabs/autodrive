import { useMemo, useState } from "react";
import { Camera, RefreshCw, TriangleAlert } from "lucide-react";
import { endpoints } from "@/config/api";
import { StatusPill } from "@/components/common/StatusPill";

interface VideoFeedCardProps {
  title: string;
  frameKey: string;
  connected: boolean;
}

export function VideoFeedCard({ title, frameKey, connected }: VideoFeedCardProps) {
  const [version, setVersion] = useState(0);
  const [failed, setFailed] = useState(false);
  const source = useMemo(() => `${endpoints.videoFeed(frameKey)}?v=${version}`, [frameKey, version]);

  return (
    <section className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900 shadow-xl shadow-black/10">
      <div className="flex items-center justify-between gap-3 border-b border-white/10 px-4 py-3">
        <div className="flex items-center gap-2">
          <Camera className="h-4 w-4 text-blue-300" />
          <h2 className="font-semibold text-white">{title}</h2>
        </div>
        <div className="flex items-center gap-2">
          <StatusPill label={failed ? "Stream error" : connected ? "Live" : "Waiting"} tone={failed ? "bad" : connected ? "good" : "warn"} />
          <button
            type="button"
            onClick={() => {
              setFailed(false);
              setVersion((current) => current + 1);
            }}
            className="rounded-full border border-white/10 bg-white/5 p-2 text-slate-300 transition hover:bg-white/10 hover:text-white"
            aria-label={`Refresh ${title}`}
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="relative aspect-video bg-slate-950">
        {failed ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-red-300">
            <TriangleAlert className="h-8 w-8" />
            <span className="text-sm">Unable to load this stream</span>
          </div>
        ) : (
          <img
            src={source}
            alt={`${title} video feed`}
            className="h-full w-full object-contain"
            onError={() => setFailed(true)}
            onLoad={() => setFailed(false)}
          />
        )}
      </div>
    </section>
  );
}
