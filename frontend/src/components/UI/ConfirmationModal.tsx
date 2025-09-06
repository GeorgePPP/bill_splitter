import React from 'react';
import { Modal } from './Modal';
import { Button } from './Button';
import { AlertTriangle } from 'lucide-react';

export interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'warning' | 'danger' | 'info';
  details?: string[];
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'warning',
  details = [],
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'danger':
        return {
          iconColor: 'text-red-500',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          buttonColor: 'bg-red-600 hover:bg-red-700',
        };
      case 'warning':
        return {
          iconColor: 'text-yellow-500',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          buttonColor: 'bg-yellow-600 hover:bg-yellow-700',
        };
      case 'info':
        return {
          iconColor: 'text-blue-500',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          buttonColor: 'bg-blue-600 hover:bg-blue-700',
        };
      default:
        return {
          iconColor: 'text-yellow-500',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          buttonColor: 'bg-yellow-600 hover:bg-yellow-700',
        };
    }
  };

  const styles = getVariantStyles();

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="">
      <div className="text-center">
        {/* Icon */}
        <div className={`mx-auto flex items-center justify-center h-12 w-12 rounded-full ${styles.bgColor} mb-4`}>
          <AlertTriangle className={`h-6 w-6 ${styles.iconColor}`} />
        </div>

        {/* Title */}
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          {title}
        </h3>

        {/* Message */}
        <p className="text-sm text-gray-500 mb-4">
          {message}
        </p>

        {/* Details */}
        {details.length > 0 && (
          <div className={`text-left rounded-lg p-3 mb-4 ${styles.bgColor} ${styles.borderColor} border`}>
            <ul className="text-sm text-gray-700 space-y-1">
              {details.map((detail, index) => (
                <li key={index} className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>{detail}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Buttons */}
        <div className="flex justify-center space-x-3">
          <Button
            variant="outline"
            onClick={onClose}
            className="px-4 py-2"
          >
            {cancelText}
          </Button>
          <Button
            onClick={onConfirm}
            className={`px-4 py-2 text-white ${styles.buttonColor} focus:ring-2 focus:ring-offset-2`}
          >
            {confirmText}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
