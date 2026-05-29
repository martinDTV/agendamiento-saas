import { Ionicons } from '@expo/vector-icons';
import { Image, View } from 'react-native';

import { COLORS } from '@/config/theme';

interface Props {
  uri?: string | null;
  /** Tamaño en px (cuadrado, redondeado a círculo). */
  size?: number;
  /** Ícono fallback cuando no hay foto. */
  fallbackIcon?: keyof typeof Ionicons.glyphMap;
}

/**
 * Avatar circular para doctores/pacientes.
 *
 * - Si `uri` tiene URL → muestra la imagen.
 * - Si no → muestra ícono Ionicons sobre fondo brand-100.
 *
 * No usamos className para los tamaños porque Nativewind no resuelve bien
 * width/height dinámicos vía clase, mejor estilo inline.
 */
export function Avatar({ uri, size = 56, fallbackIcon = 'person' }: Props) {
  const radius = size / 2;
  const iconSize = Math.round(size * 0.5);

  if (uri) {
    return (
      <Image
        source={{ uri }}
        style={{ width: size, height: size, borderRadius: radius, backgroundColor: COLORS.brandLight }}
        accessibilityIgnoresInvertColors
      />
    );
  }

  return (
    <View
      style={{
        width: size,
        height: size,
        borderRadius: radius,
        backgroundColor: COLORS.brandLight,
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <Ionicons name={fallbackIcon} size={iconSize} color={COLORS.brand} />
    </View>
  );
}
