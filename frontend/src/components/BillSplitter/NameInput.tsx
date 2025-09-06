import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/UI/Card';
import { Button } from '@/components/UI/Button';
import { Input } from '@/components/UI/Input';
import { Person } from '@/types/person.types';
import { User, Mail, Phone, Plus, Trash2 } from 'lucide-react';

export interface NameInputProps {
  participants: Person[];
  onParticipantsChange: (participants: Person[]) => void;
  onNext: () => void;
  onBack: () => void;
  disabled?: boolean;
}

export const NameInput: React.FC<NameInputProps> = ({
  participants,
  onParticipantsChange,
  onNext,
  onBack,
  disabled = false,
}) => {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [tempPerson, setTempPerson] = useState<Partial<Person>>({});

  const handleAddPerson = () => {
    const newPerson: Person = {
      id: `person_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name: '',
      email: '',
      phone: '',
    };
    onParticipantsChange([...participants, newPerson]);
    setEditingIndex(participants.length);
    setTempPerson(newPerson);
  };

  const handleEditPerson = (index: number) => {
    setEditingIndex(index);
    setTempPerson(participants[index]);
  };

  const handleSavePerson = () => {
    if (tempPerson.name?.trim()) {
      const updatedParticipants = [...participants];
      if (editingIndex !== null) {
        updatedParticipants[editingIndex] = { ...participants[editingIndex], ...tempPerson };
      }
      onParticipantsChange(updatedParticipants);
    }
    setEditingIndex(null);
    setTempPerson({});
  };

  const handleCancelEdit = () => {
    setEditingIndex(null);
    setTempPerson({});
  };

  const handleRemovePerson = (index: number) => {
    const updatedParticipants = participants.filter((_, i) => i !== index);
    onParticipantsChange(updatedParticipants);
  };

  const handleInputChange = (field: keyof Person, value: string) => {
    setTempPerson(prev => ({ ...prev, [field]: value }));
  };

  const canProceed = participants.length > 0 && participants.every(p => p.name.trim() !== '');

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader className="text-center">
        <div className="mx-auto w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
          <User className="h-8 w-8 text-primary-600" />
        </div>
        <CardTitle>Enter participant names</CardTitle>
        <CardDescription>
          Add the names of everyone who will be splitting the bill
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-6">
        <div className="space-y-4">
          {participants.map((person, index) => (
            <div key={person.id} className="border border-gray-200 rounded-lg p-4">
              {editingIndex === index ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Input
                      label="Name *"
                      value={tempPerson.name || ''}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      placeholder="Enter name"
                      leftIcon={<User className="h-4 w-4" />}
                    />
                    <Input
                      label="Email"
                      type="email"
                      value={tempPerson.email || ''}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      placeholder="Enter email (optional)"
                      leftIcon={<Mail className="h-4 w-4" />}
                    />
                    <Input
                      label="Phone"
                      value={tempPerson.phone || ''}
                      onChange={(e) => handleInputChange('phone', e.target.value)}
                      placeholder="Enter phone (optional)"
                      leftIcon={<Phone className="h-4 w-4" />}
                    />
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      onClick={handleSavePerson}
                      disabled={!tempPerson.name?.trim()}
                      size="sm"
                    >
                      Save
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleCancelEdit}
                      size="sm"
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{person.name}</h4>
                    {person.email && (
                      <p className="text-sm text-gray-500">{person.email}</p>
                    )}
                    {person.phone && (
                      <p className="text-sm text-gray-500">{person.phone}</p>
                    )}
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEditPerson(index)}
                      disabled={disabled}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemovePerson(index)}
                      disabled={disabled}
                      leftIcon={<Trash2 className="h-4 w-4" />}
                    >
                      Remove
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="text-center">
          <Button
            variant="outline"
            onClick={handleAddPerson}
            disabled={disabled}
            leftIcon={<Plus className="h-4 w-4" />}
          >
            Add Person
          </Button>
        </div>

        <div className="flex justify-between pt-4">
          <Button
            variant="outline"
            onClick={onBack}
            disabled={disabled}
          >
            Back
          </Button>
          <Button
            onClick={onNext}
            disabled={!canProceed || disabled}
          >
            Continue to Receipt
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
