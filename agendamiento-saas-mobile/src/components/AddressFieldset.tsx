import { Ionicons } from '@expo/vector-icons';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, Text, View } from 'react-native';

import { Input } from '@/components/Input';
import { Select } from '@/components/Select';
import { COLORS } from '@/config/theme';
import { fetchPostalCode } from '@/lib/queries';
import type { PostalCodeInfo } from '@/types/api';

interface AddressValue {
  address_street?: string;
  address_neighborhood?: string;
  address_city?: string;
  address_state?: string;
  address_zip?: string;
  address_country?: string;
}

interface Props {
  value: AddressValue;
  /** Llamado con un patch parcial del valor. */
  onChange: (patch: AddressValue) => void;
  /** Errores por campo (para mostrar inline). */
  fieldError?: (key: keyof AddressValue) => string | undefined;
}

type LookupState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'ok'; data: PostalCodeInfo }
  | { status: 'notfound' }
  | { status: 'error' };


/**
 * Sección de Dirección con autocomplete por código postal.
 *
 * Comportamiento:
 *   - Al montar, si ya hay un CP guardado (perfil cargado del backend),
 *     se dispara un lookup automático para poblar el Select de colonias.
 *   - Cuando el usuario cambia el CP, espera 400ms y dispara lookup nuevo.
 *   - Estado: SOLO si el provider la sabe. Si no, queda vacío (no inventa).
 *   - Ciudad: igual — no usar la colonia como ciudad.
 *   - Colonia: si hay >0 colonias del provider → Select. Si hay 0 → Input.
 *     El paciente puede escribir libremente si no le gustan las opciones.
 */
export function AddressFieldset({ value, onChange, fieldError }: Props) {
  const [state, setState] = useState<LookupState>({ status: 'idle' });
  // Si el usuario decide ignorar las opciones del Select y escribir su colonia
  // manualmente, esta flag fuerza modo Input local sin tocar el modelo.
  const [manualNeighborhood, setManualNeighborhood] = useState(false);
  const lastFetchedCpRef = useRef<string>('');
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const cp = (value.address_zip ?? '').trim();

  // Efecto: cuando el CP llega a 5 dígitos válidos, autocompletar.
  // Esto se ejecuta también al montar si ya viene un CP del backend.
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!/^\d{5}$/.test(cp)) {
      setState({ status: 'idle' });
      return;
    }
    if (cp === lastFetchedCpRef.current) return;

    setState({ status: 'loading' });
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await fetchPostalCode(cp);
        lastFetchedCpRef.current = cp;
        // Auto-llenado conservador: solo escribimos campos vacíos.
        const patch: AddressValue = {};
        if (!value.address_state && data.state) {
          patch.address_state = data.state;
        }
        if (!value.address_city && data.city) {
          patch.address_city = data.city;
        }
        // Si hay UNA sola colonia, la pre-seleccionamos. Si hay varias,
        // el paciente elige del Select (no auto-asumimos cuál).
        if (!value.address_neighborhood && data.neighborhoods.length === 1) {
          patch.address_neighborhood = data.neighborhoods[0];
        }
        if (Object.keys(patch).length > 0) onChange(patch);
        setState({ status: 'ok', data });
      } catch (err: unknown) {
        const status = (err as { response?: { status?: number } })?.response?.status;
        setState({ status: status === 404 ? 'notfound' : 'error' });
      }
    }, 400);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cp]);

  const lookupNeighborhoods = state.status === 'ok' ? state.data.neighborhoods : [];

  // Si el usuario tiene una colonia guardada que NO está en la lista del
  // provider (caso común con datos viejos o capturados a mano), la
  // agregamos arriba del dropdown para que no se pierda al elegir.
  const allNeighborhoods = (() => {
    const saved = value.address_neighborhood?.trim();
    if (saved && !lookupNeighborhoods.includes(saved)) {
      return [saved, ...lookupNeighborhoods];
    }
    return lookupNeighborhoods;
  })();

  return (
    <View className="gap-3">
      {/* CP primero — es el campo que dispara todo */}
      <Input
        label="Código postal"
        keyboardType="number-pad"
        value={value.address_zip ?? ''}
        onChangeText={(v) => onChange({ address_zip: v.replace(/\D/g, '').slice(0, 5) })}
        maxLength={5}
        placeholder="06600"
        hint="Escribe 5 dígitos y autocompletamos los demás campos."
        error={fieldError?.('address_zip')}
      />

      {/* Estado de la búsqueda */}
      {state.status === 'loading' ? (
        <View className="flex-row items-center gap-2 px-1">
          <ActivityIndicator size="small" color={COLORS.brand} />
          <Text className="text-sm text-slate-500">Buscando dirección…</Text>
        </View>
      ) : state.status === 'notfound' ? (
        <View className="flex-row items-center gap-2 px-1">
          <Ionicons name="information-circle-outline" size={16} color="#92400E" />
          <Text className="text-sm text-amber-700">
            No encontramos ese CP. Llena los datos a mano.
          </Text>
        </View>
      ) : state.status === 'error' ? (
        <View className="flex-row items-center gap-2 px-1">
          <Ionicons name="warning-outline" size={16} color="#92400E" />
          <Text className="text-sm text-amber-700">
            Servicio no disponible. Llena los datos a mano.
          </Text>
        </View>
      ) : state.status === 'ok' ? (
        <View className="flex-row items-center gap-2 px-1">
          <Ionicons name="checkmark-circle" size={16} color="#10B981" />
          <Text className="text-sm text-emerald-700">
            {state.data.neighborhoods.length > 1
              ? `${state.data.neighborhoods.length} colonias disponibles para este CP.`
              : 'Datos autocompletados. Puedes editarlos si hace falta.'}
          </Text>
        </View>
      ) : null}

      {/* Estado + Ciudad — autocompletados pero editables */}
      <View className="flex-row gap-3">
        <View className="flex-1">
          <Input
            label="Estado"
            value={value.address_state ?? ''}
            onChangeText={(v) => onChange({ address_state: v })}
            autoCapitalize="words"
            error={fieldError?.('address_state')}
          />
        </View>
        <View className="flex-1">
          <Input
            label="Ciudad / municipio"
            value={value.address_city ?? ''}
            onChangeText={(v) => onChange({ address_city: v })}
            autoCapitalize="words"
            placeholder="Ciudad Valles"
            error={fieldError?.('address_city')}
          />
        </View>
      </View>

      {/* Colonia */}
      {allNeighborhoods.length > 0 && !manualNeighborhood ? (
        // Tenemos colonias del provider O una guardada → Select
        <>
          <Select<string>
            label="Colonia"
            placeholder="Elige tu colonia"
            value={value.address_neighborhood ?? ''}
            options={allNeighborhoods.map((n) => ({ value: n, label: n }))}
            onChange={(v) => onChange({ address_neighborhood: v })}
            error={fieldError?.('address_neighborhood')}
          />
          {/* Escape hatch: si el provider no tiene la colonia real */}
          <Pressable
            onPress={() => {
              setManualNeighborhood(true);
              onChange({ address_neighborhood: '' });
            }}
            className="-mt-1 px-1"
          >
            <Text className="text-xs text-brand-700">
              ¿No está tu colonia? Toca para escribirla manualmente.
            </Text>
          </Pressable>
        </>
      ) : (
        // Sin colonias del provider, o el usuario eligió modo manual.
        <>
          <Input
            label="Colonia"
            value={value.address_neighborhood ?? ''}
            onChangeText={(v) => onChange({ address_neighborhood: v })}
            autoCapitalize="words"
            placeholder="Palo de Rosa"
            error={fieldError?.('address_neighborhood')}
          />
          {/* Si tenemos opciones del provider pero estamos en modo manual,
              ofrecer volver al Select */}
          {allNeighborhoods.length > 0 && manualNeighborhood ? (
            <Pressable
              onPress={() => setManualNeighborhood(false)}
              className="-mt-1 px-1"
            >
              <Text className="text-xs text-brand-700">
                Ver las {allNeighborhoods.length} colonias del CP.
              </Text>
            </Pressable>
          ) : null}
        </>
      )}

      {/* Calle y número exterior/interior — siempre manual, lo último */}
      <Input
        label="Calle, número exterior e interior"
        value={value.address_street ?? ''}
        onChangeText={(v) => onChange({ address_street: v })}
        autoCapitalize="words"
        placeholder="Av. Reforma 222, depto 5B"
        hint="Incluye número exterior y, si aplica, interior."
        error={fieldError?.('address_street')}
      />
    </View>
  );
}

