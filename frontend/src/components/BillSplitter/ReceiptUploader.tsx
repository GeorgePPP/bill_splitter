import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/UI/Card';
import { Button } from '@/components/UI/Button';
import { Loader } from '@/components/UI/Loader';
import { Upload, FileImage, AlertCircle, CheckCircle } from 'lucide-react';
import { validateFile } from '@/utils/fileHelpers';
import { formatFileSize } from '@/utils/formatters';
import { ReceiptValidationModal } from './ReceiptValidationModal';

export interface ReceiptUploaderProps {
  onReceiptUploaded: (file: File) => void;
  onReceiptProcessed: (receiptData: any) => void;
  onValidationCorrection: (correctedData: any) => void;
  isLoading?: boolean;
  uploadProgress?: number;
  error?: string | null;
  validationError?: any;
  needsValidation?: boolean;
  extractedData?: any;
  disabled?: boolean;
}

export const ReceiptUploader: React.FC<ReceiptUploaderProps> = ({
  onReceiptUploaded,
  onReceiptProcessed,
  onValidationCorrection,
  isLoading = false,
  uploadProgress = 0,
  error = null,
  validationError = null,
  needsValidation = false,
  extractedData = null,
  disabled = false,
}) => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [shouldShowValidationModal, setShouldShowValidationModal] = useState(false);

  // Update modal visibility when needsValidation changes
  React.useEffect(() => {
    console.log('[ReceiptUploader] Validation state changed:', {
      needsValidation,
      extractedData,
      preview,
      validationError
    });
    
    if (needsValidation && extractedData && preview) {
      setShouldShowValidationModal(true);
    }
  }, [needsValidation, extractedData, preview]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    const validation = validateFile(file);
    if (!validation.isValid) {
      // Handle validation error
      return;
    }

    setUploadedFile(file);
    
    // Create preview and keep it
    const reader = new FileReader();
    reader.onload = (e) => {
      const previewUrl = e.target?.result as string;
      setPreview(previewUrl);
      console.log('[ReceiptUploader] Preview created');
    };
    reader.readAsDataURL(file);

    onReceiptUploaded(file);
  }, [onReceiptUploaded]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.tiff', '.bmp']
    },
    multiple: false,
    disabled: disabled || isLoading,
  });

  const handleRetry = () => {
    setUploadedFile(null);
    setPreview(null);
  };

  return (
    <>
      <Card className="max-w-2xl mx-auto">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
            <FileImage className="h-8 w-8 text-primary-600" />
          </div>
          <CardTitle>Upload Receipt</CardTitle>
          <CardDescription>
            Take a photo or upload an image of your receipt
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {!uploadedFile ? (
            <div
              {...getRootProps()}
              className={`
                border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
                ${isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300'}
                ${disabled || isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:border-primary-400'}
              `}
            >
              <input {...getInputProps()} />
              <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              {isDragActive ? (
                <p className="text-lg font-medium text-primary-600">
                  Drop the receipt here...
                </p>
              ) : (
                <div>
                  <p className="text-lg font-medium text-gray-900 mb-2">
                    Drag & drop your receipt here
                  </p>
                  <p className="text-gray-500 mb-4">
                    or click to browse files
                  </p>
                  <p className="text-sm text-gray-400">
                    Supports: JPEG, PNG, TIFF, BMP (max 10MB)
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    {preview ? (
                      <img
                        src={preview}
                        alt="Receipt preview"
                        className="h-16 w-16 object-cover rounded"
                      />
                    ) : (
                      <div className="h-16 w-16 bg-gray-100 rounded flex items-center justify-center">
                        <FileImage className="h-8 w-8 text-gray-400" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {uploadedFile.name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {formatFileSize(uploadedFile.size)}
                    </p>
                  </div>
                  <div className="flex-shrink-0">
                    {isLoading ? (
                      <Loader size="sm" />
                    ) : (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    )}
                  </div>
                </div>
              </div>

              {isLoading && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Processing receipt...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <AlertCircle className="h-5 w-5 text-red-500" />
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                  <div className="mt-3">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleRetry}
                      className="text-red-600 border-red-300 hover:bg-red-50"
                    >
                      Try Again
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="text-center">
            <Button
              onClick={() => onReceiptProcessed({})}
              disabled={!uploadedFile || isLoading || !!error}
              size="lg"
              className="w-full"
            >
              {isLoading ? 'Processing...' : 'Process Receipt'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Validation Modal */}
      {needsValidation && extractedData && preview && (
        <ReceiptValidationModal
          isOpen={needsValidation}
          onClose={() => {}}
          imageUrl={preview}
          extractedData={extractedData}
          validationErrors={validationError}
          onValidate={onValidationCorrection}
        />
      )}
    </>
  );
};