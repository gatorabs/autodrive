import { useMemo, useState } from "react";
import { Camera, RefreshCw, TriangleAlert } from "lucide-react";
import { endpoints } from "@/config/api";

interface VideoFeedCardProps {
  title: string;
  frameKey: string;
  connected: boolean;
}

function CornerBrackets() {
  const base = "pointer-events-none absolute h-4 w-4 border-primary/70";
  return (
    <>
      <span className={`${base} left-2 top-2 border-l-2 border-t-2`} />
      <span className={`${base} right-2 top-2 border-r-2 border-t-2`} />
      <span className={`${base} bottom-2 left-2 border-b-2 border-l-2`} />
      <span className={`${base} bottom-2 right-2 border-b-2 border-r-2`} />
    </>
  );
}

export function VideoFeedCard({ title, frameKey, connected }: VideoFeedCardProps) {
  const [version, setVersion] = useState(0);
  const [failed, setFailed] = useState(false);
  const source = useMemo(() => `${endpoints.videoFeed(frameKey)}?v=${version}`, [frameKey, version]);
  const live = connected && !failed;

  return (
    <section className="overflow-hidden border border-border bg-surface shadow-lg shadow-black/20">
      <div className="flex items-center justify-between gap-2 border-b border-border bg-surface-alt/60 px-3 py-2">
        <div className="flex min-w-0 items-center gap-2">
          <Camera className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          <h2 className="truncate font-mono text-xs font-semibold uppercase tracking-[0.14em] text-foreground">
            {title}
          </h2>
        </div>
        <button
          type="button"
          onClick={() => {
            setFailed(false);
            setVersion((current) => current + 1);
          }}
          className="border border-border p-1.5 text-muted-foreground transition hover:bg-surface-soft hover:text-foreground"
          aria-label={`Refresh ${title}`}
        >
          <RefreshCw className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="relative aspect-video bg-background">
        {failed ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-destructive">
            <TriangleAlert className="h-8 w-8" />
            <span className="font-mono text-xs uppercase tracking-wide">Signal lost</span>
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
        <CornerBrackets />
        <div
          className={`absolute bottom-2 left-2 flex items-center gap-1.5 border px-2 py-0.5 font-mono text-[0.65rem] font-bold uppercase tracking-wider ${
            live
              ? "border-destructive/40 bg-black/60 text-destructive"
              : "border-border bg-black/60 text-muted-foreground"
          }`}
        >
          <span className={`h-1.5 w-1.5 rounded-full bg-current ${live ? "animate-pulse-dot" : ""}`} />
          {live ? "Live" : failed ? "Error" : "Waiting"}
        </div>
      </div>
    </section>
  );
}
