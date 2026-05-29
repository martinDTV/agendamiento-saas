import { Ionicons } from '@expo/vector-icons';
import { Image, Pressable, Text, View } from 'react-native';
import Animated from 'react-native-reanimated';
import { cssInterop } from 'nativewind';

import { Button } from '@/components/Button';
import { COLORS } from '@/config/theme';
import { usePressScale } from '@/hooks/usePressScale';
import type { Doctor } from '@/types/api';

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

interface Props {
  doctor: Doctor;
  /** Toca el card → ir a detalle. */
  onPress: () => void;
  /** Toca el botón "Agendar" → iniciar wizard directo. */
  onBook: () => void;
}

/**
 * Card vertical rica para un doctor en la lista.
 *
 * Jerarquía visual (de mayor a menor):
 *   1. Foto grande (avatar circular)
 *   2. Nombre del doctor
 *   3. Especialidad como chip outline
 *   4. Rating con estrellas + (n reseñas)
 *   5. Clínica como texto pequeño
 *   6. Próxima disponibilidad ("Disponible mañana 9:00")
 *   7. Botón "Agendar" como CTA primario
 *
 * Diseñado para que al ver una card el paciente pueda decidir reservar SIN
 * abrir detalle — patrón estándar Doctoralia/Practo.
 */
export function DoctorCard({ doctor, onPress, onBook }: Props) {
  const hasRating = doctor.avg_rating != null && doctor.review_count > 0;
  const { animatedStyle, onPressIn, onPressOut } = usePressScale(0.98);

  return (
    <AnimatedPressable
      onPress={onPress}
      onPressIn={onPressIn}
      onPressOut={onPressOut}
      style={animatedStyle}
      className="overflow-hidden rounded-2xl border border-slate-100 bg-white active:bg-slate-50"
    >
      {/* Header con foto + nombre + clínica */}
      <View className="flex-row gap-4 p-4">
        <Avatar uri={doctor.photo_url} />

        <View className="flex-1 gap-1">
          <Text className="text-base font-bold text-slate-900" numberOfLines={1}>
            Dr. {doctor.full_name}
          </Text>

          {/* Especialidad como chip outline */}
          {doctor.specialty ? (
            <View className="self-start rounded-full border border-brand-200 bg-brand-50 px-2 py-0.5">
              <Text className="text-xs font-semibold text-brand-700">{doctor.specialty}</Text>
            </View>
          ) : null}

          {/* Rating */}
          <View className="mt-1 flex-row items-center gap-1">
            {hasRating ? (
              <>
                <RatingStars rating={doctor.avg_rating!} />
                <Text className="text-sm font-semibold text-slate-900">
                  {doctor.avg_rating!.toFixed(1)}
                </Text>
                <Text className="text-xs text-slate-500">({doctor.review_count})</Text>
              </>
            ) : (
              <Text className="text-xs text-slate-400">Sin reseñas todavía</Text>
            )}
          </View>

          {/* Clínica + distancia (si está cerca de mí activo) */}
          <View className="mt-0.5 flex-row items-center gap-1">
            <Ionicons name="business-outline" size={12} color="#64748B" />
            <Text className="flex-1 text-xs text-slate-500" numberOfLines={1}>
              {doctor.tenant_name}
            </Text>
            {doctor.distance_km != null ? (
              <View className="flex-row items-center gap-0.5">
                <Ionicons name="location" size={11} color={COLORS.brand} />
                <Text className="text-xs font-semibold text-brand-700">
                  {formatDistance(doctor.distance_km)}
                </Text>
              </View>
            ) : null}
          </View>
        </View>
      </View>

      {/* Footer con próxima disponibilidad + botón */}
      <View className="flex-row items-center justify-between gap-3 border-t border-slate-100 bg-slate-50 px-4 py-3">
        <View className="flex-1">
          {doctor.next_available ? (
            <>
              <Text className="text-xs uppercase tracking-wider text-slate-500">
                Próxima cita
              </Text>
              <Text className="text-sm font-semibold text-slate-800" numberOfLines={1}>
                {formatNextAvailable(doctor.next_available)}
              </Text>
            </>
          ) : (
            <Text className="text-xs text-slate-500">Ver disponibilidad</Text>
          )}
        </View>

        <Button label="Agendar" size="sm" onPress={onBook} />
      </View>
    </AnimatedPressable>
  );
}

// ── Subcomponentes ─────────────────────────────────────────────────────────

function Avatar({ uri }: { uri?: string | null }) {
  const size = 72;
  if (uri) {
    return (
      <Image
        source={{ uri }}
        style={{ width: size, height: size, borderRadius: size / 2, backgroundColor: COLORS.brandLight }}
        accessibilityIgnoresInvertColors
      />
    );
  }
  return (
    <View
      style={{
        width: size, height: size, borderRadius: size / 2,
        backgroundColor: COLORS.brandLight,
        alignItems: 'center', justifyContent: 'center',
      }}
    >
      <Ionicons name="person" size={36} color={COLORS.brand} />
    </View>
  );
}

function RatingStars({ rating }: { rating: number }) {
  const fullStars = Math.floor(rating);
  const hasHalfStar = rating - fullStars >= 0.5;
  const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

  return (
    <View className="flex-row items-center">
      {Array.from({ length: fullStars }).map((_, i) => (
        <Ionicons key={`f-${i}`} name="star" size={12} color="#F59E0B" />
      ))}
      {hasHalfStar ? <Ionicons name="star-half" size={12} color="#F59E0B" /> : null}
      {Array.from({ length: emptyStars }).map((_, i) => (
        <Ionicons key={`e-${i}`} name="star-outline" size={12} color="#CBD5E1" />
      ))}
    </View>
  );
}

/**
 * Convierte {date: '2026-06-03', start: '09:00'} a una etiqueta amigable:
 *   Hoy 9:00 a. m.
 *   Mañana 9:00 a. m.
 *   Mié 3 jun, 9:00 a. m.
 */
function formatNextAvailable(slot: { date: string; start: string }): string {
  const [year, month, day] = slot.date.split('-').map(Number);
  const target = new Date(year, month - 1, day);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const tomorrow = new Date(today);
  tomorrow.setDate(today.getDate() + 1);

  const time = formatTime12h(slot.start);

  if (target.getTime() === today.getTime()) return `Hoy ${time}`;
  if (target.getTime() === tomorrow.getTime()) return `Mañana ${time}`;

  const days = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'];
  const months = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
  return `${days[target.getDay()]} ${target.getDate()} ${months[target.getMonth()]}, ${time}`;
}

function formatTime12h(hhmm: string): string {
  const [hStr, mStr] = hhmm.split(':');
  const h = parseInt(hStr, 10);
  const m = mStr;
  const period = h >= 12 ? 'p. m.' : 'a. m.';
  const h12 = ((h + 11) % 12) + 1;
  return `${h12}:${m} ${period}`;
}

/** Distancia legible: <1km en metros, ≥1km con 1 decimal. */
function formatDistance(km: number): string {
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km.toFixed(1)} km`;
}

cssInterop(Pressable, { className: 'style' });
