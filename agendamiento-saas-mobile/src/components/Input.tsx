import { forwardRef } from 'react';
import { Text, TextInput, TextInputProps, View } from 'react-native';

interface Props extends TextInputProps {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<TextInput, Props>(function Input(
  { label, error, hint, className, ...rest },
  ref,
) {
  return (
    <View className="gap-1.5">
      {label ? <Text className="text-sm font-medium text-slate-700">{label}</Text> : null}
      <TextInput
        ref={ref}
        placeholderTextColor="#94A3B8"
        className={[
          'rounded-xl border bg-white px-4 py-3 text-base text-slate-900',
          error ? 'border-red-400' : 'border-slate-200 focus:border-brand-500',
          className ?? '',
        ].join(' ')}
        {...rest}
      />
      {error ? (
        <Text className="text-xs text-red-600">{error}</Text>
      ) : hint ? (
        <Text className="text-xs text-slate-500">{hint}</Text>
      ) : null}
    </View>
  );
});
