import { ReactNode } from 'react';
import { ScrollView, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

interface Props {
  children: ReactNode;
  scroll?: boolean;
  className?: string;
}

/**
 * Wrapper de pantalla — safe area + fondo + opcional scroll.
 * Mantiene la consistencia visual entre todas las screens.
 */
export function Screen({ children, scroll = true, className = '' }: Props) {
  const Inner = scroll ? ScrollView : View;
  return (
    <SafeAreaView className="flex-1 bg-slate-50" edges={['top', 'left', 'right']}>
      <Inner
        className={`flex-1 ${className}`}
        contentContainerClassName={scroll ? 'p-5 gap-4' : undefined}
      >
        {children}
      </Inner>
    </SafeAreaView>
  );
}
