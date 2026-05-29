import axios from 'axios';

/**
 * Convierte un error de Axios con respuesta tipo DRF en un mapa de errores
 * por campo, listo para mostrar al lado de cada input.
 *
 * Ej: `{phone: ["Teléfono inválido..."], curp: ["CURP inválido..."]}` →
 *     `{phone: "Teléfono inválido...", curp: "CURP inválido..."}`
 *
 * Si la respuesta no es por-campo (ej. `{detail: "..."}` o un 500), devuelve
 * un objeto con la clave especial `_general` para que la UI lo muestre
 * en una banda global.
 */
export type FieldErrors = Record<string, string>;

export function parseFieldErrors(err: unknown): FieldErrors {
  if (!axios.isAxiosError(err) || !err.response) {
    return { _general: err instanceof Error ? err.message : 'Error desconocido.' };
  }
  const { data, status } = err.response;

  if (status === 429) return { _general: 'Demasiados intentos. Espera unos segundos.' };
  if (typeof data === 'string') return { _general: data };

  if (data && typeof data === 'object') {
    const obj = data as Record<string, unknown>;

    // {detail: "..."} o {error: "..."} → general
    if (typeof obj.detail === 'string') return { _general: obj.detail };
    if (typeof obj.error === 'string') return { _general: obj.error };

    // Por-campo: {campo: ["msg"]} o {campo: "msg"}
    const out: FieldErrors = {};
    for (const [field, value] of Object.entries(obj)) {
      if (Array.isArray(value) && typeof value[0] === 'string') {
        out[field] = value[0];
      } else if (typeof value === 'string') {
        out[field] = value;
      }
    }
    if (Object.keys(out).length > 0) return out;
  }

  return { _general: `Error ${status}.` };
}
