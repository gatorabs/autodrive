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
    <section className="overflow-hidden rounded-2xl border border-border bg-surface shadow-lg shadow-black/10">
      <div className="flex flex-col gap-3 border-b border-border px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-center gap-2">
          <Camera className="h-4 w-4 shrink-0 text-muted-foreground" />
          <h2 className="truncate font-semibold text-foreground">{title}</h2>
        </div>
        <div className="flex items-center justify-between gap-2 sm:justify-end">
          <StatusPill label={failed ? "Stream error" : connected ? "Live" : "Waiting"} tone={failed ? "bad" : connected ? "good" : "warn"} />
          <button
            type="button"
            onClick={() => {
              setFailed(false);
              setVersion((current) => current + 1);
            }}
            className="rounded-xl border border-border bg-background p-2 text-muted-foreground transition hover:bg-surface-alt hover:text-foreground"
            aria-label={`Refresh ${title}`}
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="relative aspect-video bg-background">
        {failed ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-destructive">
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
