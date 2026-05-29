import { ActivityIndicator, Pressable, PressableProps, Text, View } from 'react-native';
import Animated from 'react-native-reanimated';
import { cssInterop } from 'nativewind';

import { COLORS } from '@/config/theme';
import { usePressScale } from '@/hooks/usePressScale';

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';
type Size = 'sm' | 'md' | 'lg';

interface Props extends Omit<PressableProps, 'children' | 'style'> {
  label: string;
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  fullWidth?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const baseByVariant: Record<Variant, string> = {
  primary: 'bg-brand-600 active:bg-brand-700',
  secondary: 'bg-brand-100 active:bg-brand-200',
  ghost: 'bg-transparent active:bg-slate-100',
  danger: 'bg-red-600 active:bg-red-700',
};

const textByVariant: Record<Variant, string> = {
  primary: 'text-white',
  secondary: 'text-brand-800',
  ghost: 'text-slate-800',
  danger: 'text-white',
};

const padBySize: Record<Size, string> = {
  sm: 'px-3 py-2',
  md: 'px-4 py-3',
  lg: 'px-5 py-4',
};

const textBySize: Record<Size, string> = {
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-lg',
};

export function Button({
  label,
  variant = 'primary',
  size = 'md',
  loading,
  disabled,
  fullWidth,
  leftIcon,
  rightIcon,
  className,
  ...rest
}: Props & { className?: string }) {
  const isDisabled = disabled || loading;
  const { animatedStyle, onPressIn, onPressOut } = usePressScale(0.97);
  return (
    <AnimatedPressable
      accessibilityRole="button"
      disabled={isDisabled}
      onPressIn={onPressIn}
      onPressOut={onPressOut}
      style={animatedStyle}
      className={[
        'flex-row items-center justify-center rounded-xl',
        baseByVariant[variant],
        padBySize[size],
        fullWidth ? 'w-full' : '',
        isDisabled ? 'opacity-60' : '',
        className ?? '',
      ].join(' ')}
      {...rest}
    >
      {loading ? (
        <ActivityIndicator color={variant === 'primary' || variant === 'danger' ? COLORS.white : COLORS.brand} />
      ) : (
        <View className="flex-row items-center gap-2">
          {leftIcon}
          <Text className={`font-semibold ${textByVariant[variant]} ${textBySize[size]}`}>
            {label}
          </Text>
          {rightIcon}
        </View>
      )}
    </AnimatedPressable>
  );
}

// Permite className en Pressable bajo Nativewind v4
cssInterop(Pressable, { className: 'style' });
