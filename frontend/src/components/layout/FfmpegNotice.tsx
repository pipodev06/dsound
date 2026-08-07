interface FfmpegNoticeProps {
  visible: boolean;
  message: string;
}

export function FfmpegNotice({ visible, message }: FfmpegNoticeProps) {
  if (!visible) return null;

  return (
    <div className="fixed bottom-4 left-4 z-[5] flex max-w-[min(300px,calc(100vw-2rem))] items-start gap-2 rounded-md border border-border bg-surface p-3 font-sans text-[0.78rem] leading-snug text-text-muted">
      <span className="shrink-0 font-bold text-warn">[!]</span>
      <span>{message}</span>
    </div>
  );
}
