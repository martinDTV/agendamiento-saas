import * as Location from 'expo-location';
import { useCallback, useState } from 'react';

export interface UserLocation {
  lat: number;
  lng: number;
}

type Status =
  | 'idle'
  | 'requesting'
  | 'granted'
  | 'denied'
  | 'error';

interface UseUserLocationResult {
  status: Status;
  location: UserLocation | null;
  error: string | null;
  /**
   * Solicita permiso y obtiene ubicación. Si ya hay permiso concedido,
   * solo refresca. Devuelve la ubicación o null si el usuario denegó.
   */
  request: () => Promise<UserLocation | null>;
  /** Olvida la ubicación obtenida (sin revocar permisos del SO). */
  clear: () => void;
}

/**
 * Hook para obtener la ubicación del usuario con expo-location.
 *
 * Flujo:
 *   1. Llamas `request()` al tocar "Cerca de mí"
 *   2. iOS/Android muestran el diálogo de permiso si no estaba concedido
 *   3. Si lo concede, regresamos {lat, lng}
 *   4. Si lo niega, status = 'denied' — la UI puede mostrar un mensaje
 *
 * NO se pide al montar — solo cuando el usuario lo activa explícitamente,
 * porque pedir el permiso sin contexto suele resultar en denegación.
 */
export function useUserLocation(): UseUserLocationResult {
  const [status, setStatus] = useState<Status>('idle');
  const [location, setLocation] = useState<UserLocation | null>(null);
  const [error, setError] = useState<string | null>(null);

  const request = useCallback(async (): Promise<UserLocation | null> => {
    setStatus('requesting');
    setError(null);
    try {
      // 1. Pedir permiso
      const { status: permStatus } = await Location.requestForegroundPermissionsAsync();
      if (permStatus !== 'granted') {
        setStatus('denied');
        return null;
      }
      // 2. Obtener posición. Accuracy.Balanced es buena para ~50m de error
      //    y mucho más rápido que High (que enciende GPS).
      const pos = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });
      const loc: UserLocation = {
        lat: pos.coords.latitude,
        lng: pos.coords.longitude,
      };
      setLocation(loc);
      setStatus('granted');
      return loc;
    } catch (e) {
      setStatus('error');
      setError(e instanceof Error ? e.message : 'Error desconocido');
      return null;
    }
  }, []);

  const clear = useCallback(() => {
    setLocation(null);
    setStatus('idle');
  }, []);

  return { status, location, error, request, clear };
}
