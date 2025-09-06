import React from 'react';
import { clsx } from 'clsx';

export interface ContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  center?: boolean;
}

export const Container: React.FC<ContainerProps> = ({
  children,
  size = 'lg',
  center = true,
  className,
  ...props
}) => {
  const sizeClasses = {
    sm: 'max-w-2xl',
    md: 'max-w-4xl',
    lg: 'max-w-6xl',
    xl: 'max-w-7xl',
    full: 'max-w-none',
  };

  return (
    <div
      className={clsx(
        'w-full px-4 sm:px-6 lg:px-8',
        sizeClasses[size],
        center && 'mx-auto',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
