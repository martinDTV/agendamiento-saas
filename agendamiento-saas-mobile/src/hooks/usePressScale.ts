import { useCallback } from 'react';
import { useAnimatedStyle, useSharedValue, withSpring } from 'react-native-reanimated';

// Spring estilo Apple: settle rápido, sin bounce para UI funcional.
const SPRING = { mass: 0.5, stiffness: 320, damping: 26 };

/**
 * Feedback de presión con scale + spring para cualquier Pressable.
 * El release mantiene velocidad (interrumpible), a diferencia de un keyframe.
 */
export function usePressScale(pressedScale = 0.97) {
  const scale = useSharedValue(1);

  const onPressIn = useCallback(() => {
    scale.value = withSpring(pressedScale, SPRING);
  }, [pressedScale, scale]);

  const onPressOut = useCallback(() => {
    scale.value = withSpring(1, SPRING);
  }, [scale]);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  return { animatedStyle, onPressIn, onPressOut };
}
