import { Ionicons } from '@expo/vector-icons';
import { Pressable, View } from 'react-native';

interface Props {
  value: number; // 0 = sin elegir, 1-5
  onChange: (rating: number) => void;
  size?: number;
}

/**
 * Selector de rating con estrellas grandes para tocar.
 * Optimizado para móvil — estrellas de 48px por default (touch target 48x48 ✓).
 */
export function RatingPicker({ value, onChange, size = 48 }: Props) {
  return (
    <View className="flex-row items-center justify-center gap-2">
      {[1, 2, 3, 4, 5].map((n) => {
        const filled = n <= value;
        return (
          <Pressable
            key={n}
            onPress={() => onChange(n)}
            hitSlop={8}
            accessibilityRole="button"
            accessibilityLabel={`${n} estrellas`}
          >
            <Ionicons
              name={filled ? 'star' : 'star-outline'}
              size={size}
              color={filled ? '#F59E0B' : '#CBD5E1'}
            />
          </Pressable>
        );
      })}
    </View>
  );
}
