export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const validatePhone = (phone: string): boolean => {
  const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
  const digitsOnly = phone.replace(/\D/g, '');
  return phoneRegex.test(digitsOnly) && digitsOnly.length >= 10;
};

export const validateName = (name: string): boolean => {
  return name.trim().length >= 2 && /^[a-zA-Z\s\-']+$/.test(name.trim());
};

export const validateCurrency = (amount: string): { isValid: boolean; value?: number } => {
  const cleaned = amount.replace(/[^\d.,]/g, '');
  const parsed = parseFloat(cleaned.replace(',', '.'));
  
  if (isNaN(parsed) || parsed < 0) {
    return { isValid: false };
  }
  
  return { isValid: true, value: parsed };
};

export const validateQuantity = (quantity: string): { isValid: boolean; value?: number } => {
  const parsed = parseInt(quantity);
  
  if (isNaN(parsed) || parsed <= 0) {
    return { isValid: false };
  }
  
  return { isValid: true, value: parsed };
};

export const validateFileType = (file: File, allowedTypes: string[]): boolean => {
  return allowedTypes.includes(file.type);
};

export const validateFileSize = (file: File, maxSizeInMB: number): boolean => {
  const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
  return file.size <= maxSizeInBytes;
};

export const validateRequired = (value: any): boolean => {
  if (typeof value === 'string') {
    return value.trim().length > 0;
  }
  if (typeof value === 'number') {
    return !isNaN(value);
  }
  if (Array.isArray(value)) {
    return value.length > 0;
  }
  return value !== null && value !== undefined;
};

export const validateMinLength = (value: string, minLength: number): boolean => {
  return value.length >= minLength;
};

export const validateMaxLength = (value: string, maxLength: number): boolean => {
  return value.length <= maxLength;
};
