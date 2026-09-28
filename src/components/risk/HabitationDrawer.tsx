import { FeatureInspector } from '../inspector/FeatureInspector';
import type { Habitation } from '../../types';

interface HabitationDrawerProps {
  habitation: Habitation | null;
  onClose: () => void;
}

export function HabitationDrawer({ habitation, onClose }: HabitationDrawerProps) {
  if (!habitation) return null;
  return (
    <FeatureInspector
      feature={{ type: 'HABITATION', data: habitation }}
      onClose={onClose}
    />
  );
}
