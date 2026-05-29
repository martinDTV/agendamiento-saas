import { Pressable, PressableProps, View, ViewProps } from 'react-native';
import Animated from 'react-native-reanimated';
import { cssInterop } from 'nativewind';

import { usePressScale } from '@/hooks/usePressScale';

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

interface CardProps extends ViewProps {
  className?: string;
}

export function Card({ className, children, ...rest }: CardProps) {
  return (
    <View
      className={`rounded-2xl border border-slate-100 bg-white p-4 ${className ?? ''}`}
      {...rest}
    >
      {children}
    </View>
  );
}

interface PressableCardProps extends Omit<PressableProps, 'children' | 'style'> {
  className?: string;
  children: React.ReactNode;
}

export function PressableCard({ className, children, ...rest }: PressableCardProps) {
  const { animatedStyle, onPressIn, onPressOut } = usePressScale(0.98);
  return (
    <AnimatedPressable
      onPressIn={onPressIn}
      onPressOut={onPressOut}
      style={animatedStyle}
      className={`rounded-2xl border border-slate-100 bg-white p-4 active:bg-slate-50 ${className ?? ''}`}
      {...rest}
    >
      {children}
    </AnimatedPressable>
  );
}

cssInterop(Pressable, { className: 'style' });
