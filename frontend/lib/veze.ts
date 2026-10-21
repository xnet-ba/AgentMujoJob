export type Prozor = {
  __TAURI__?: { core?: { invoke: (komanda: string, args?: Record<string, unknown>) => Promise<unknown> } };
  open?: (url: string, target?: string, features?: string) => unknown;
};

/**
 * Otvara link u sistemskom pregledaču.
 * U Tauri (WebView2) `target="_blank"` je blokiran, pa ide preko Rust komande `otvori_url`.
 * U browseru (dev) koristi običan window.open.
 */
export function otvoriSpolja(url: string, w: Prozor): void {
  if (w.__TAURI__?.core?.invoke) {
    void w.__TAURI__.core
      .invoke("otvori_url", { url })
      .catch(() => { w.open?.(url, "_blank", "noopener"); });
    return;
  }
  w.open?.(url, "_blank", "noopener");
}
