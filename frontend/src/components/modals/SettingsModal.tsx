import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogFooter, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { getSettings, saveSettings } from "@/lib/api";
import type { Settings } from "@/types";

const BROWSER_NAMES: Record<string, string> = {
  firefox: "Firefox",
  chrome: "Chrome",
  edge: "Edge",
  brave: "Brave",
  opera: "Opera",
  vivaldi: "Vivaldi",
  chromium: "Chromium",
};

// Radix Select no admite un valor vacío
const NONE = "none";

interface SettingsModalProps {
  open: boolean;
  onClose: () => void;
  onSaved: (message: string) => void;
}

export function SettingsModal({ open, onClose, onSaved }: SettingsModalProps) {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [browser, setBrowser] = useState(NONE);
  const [metadata, setMetadata] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    getSettings()
      .then((data) => {
        if (cancelled) return;
        setSettings(data);
        setBrowser(data.cookies_browser || NONE);
        setMetadata(data.music_metadata);
        setError("");
      })
      .catch(() => !cancelled && setError("no se pudieron cargar los ajustes."));
    return () => {
      cancelled = true;
    };
  }, [open]);

  async function handleSave(ev: React.FormEvent) {
    ev.preventDefault();
    setSaving(true);
    try {
      const res = await saveSettings({ cookies_browser: browser === NONE ? "" : browser, music_metadata: metadata });
      if (!res.ok) {
        setError(res.error || "no se pudieron guardar los ajustes.");
        return;
      }
      onSaved("ajustes guardados.");
      onClose();
    } catch {
      setError("error de red al guardar los ajustes.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent aria-label="Ajustes">
        <DialogTitle>Ajustes</DialogTitle>
        <form className="flex flex-col gap-5" onSubmit={handleSave}>
          <div className="flex flex-col gap-2">
            <Label htmlFor="cookies-browser">Usar cookies del navegador</Label>
            <Select value={browser} onValueChange={setBrowser} disabled={!settings}>
              <SelectTrigger id="cookies-browser">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={NONE}>No usar</SelectItem>
                {(settings?.cookie_browsers || []).map((b) => (
                  <SelectItem key={b} value={b}>
                    {BROWSER_NAMES[b] || b}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="m-0 text-[0.78rem] leading-snug text-text-muted">
              Soluciona el error «confirma que no eres un bot» y permite descargar videos con restricción de edad. Inicia
              sesión en YouTube con ese navegador. En Windows, Firefox es el que mejor funciona: Chrome y Edge cifran sus
              cookies y a veces hay que cerrarlos por completo.
            </p>
          </div>

          <label className="flex cursor-pointer items-start gap-3">
            <Checkbox checked={metadata} onCheckedChange={(c) => setMetadata(c === true)} disabled={!settings} />
            <span className="flex flex-col gap-1">
              <span className="text-sm">Buscar los datos oficiales en YouTube Music</span>
              <span className="text-[0.78rem] leading-snug text-text-muted">
                Al descargar canciones sueltas, usa el artista, el título, el álbum, el año y la portada oficiales cuando
                los encuentra.
              </span>
            </span>
          </label>

          {error && <div className="text-sm text-danger">{error}</div>}

          <DialogFooter>
            <Button type="button" variant="ghost" size="sm" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" size="sm" disabled={!settings || saving}>
              Guardar
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
