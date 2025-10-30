/**
 * Confidence Indicator Component
 * Visual badges for high/moderate/low confidence with tooltips
 */

import { Box, Chip, Tooltip, alpha } from '@mui/material';
import {
  CheckCircle,
  Warning,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { colors } from '@/theme';

export type ConfidenceLevel = 'high' | 'moderate' | 'low';

interface ConfidenceIndicatorProps {
  level: ConfidenceLevel;
  size?: 'small' | 'medium' | 'large';
  showLabel?: boolean;
  showIcon?: boolean;
  animate?: boolean;
}

const confidenceConfig = {
  high: {
    color: colors.confidenceHigh,
    icon: CheckCircle,
    label: 'High Confidence',
    tooltip: 'Strong evidence from multiple high-quality studies',
    backgroundColor: alpha(colors.confidenceHigh, 0.1),
  },
  moderate: {
    color: colors.confidenceModerate,
    icon: Warning,
    label: 'Moderate Confidence',
    tooltip: 'Some evidence available, but additional validation recommended',
    backgroundColor: alpha(colors.confidenceModerate, 0.1),
  },
  low: {
    color: colors.confidenceLow,
    icon: ErrorIcon,
    label: 'Low Confidence',
    tooltip: 'Limited evidence available, preliminary findings only',
    backgroundColor: alpha(colors.confidenceLow, 0.1),
  },
};

export default function ConfidenceIndicator({
  level,
  size = 'medium',
  showLabel = true,
  showIcon = true,
  animate = true,
}: ConfidenceIndicatorProps) {
  const config = confidenceConfig[level];
  const Icon = config.icon;

  // Size configuration
  const sizeConfig = {
    small: { chipSize: 'small' as const, height: 24, fontSize: '0.75rem', iconSize: 16 },
    medium: { chipSize: 'medium' as const, height: 28, fontSize: '0.8125rem', iconSize: 18 },
    large: { chipSize: 'medium' as const, height: 32, fontSize: '0.875rem', iconSize: 20 },
  };

  const { chipSize, height, fontSize, iconSize } = sizeConfig[size];

  const chipContent = animate ? (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.3 }}
      whileHover={{ scale: 1.05 }}
      style={{ display: 'inline-block' }}
    >
      <Chip
        icon={showIcon ? <Icon sx={{ fontSize: iconSize }} /> : undefined}
        label={showLabel ? config.label : level.toUpperCase()}
        size={chipSize}
        sx={{
          height,
          fontSize,
          fontWeight: 600,
          backgroundColor: config.backgroundColor,
          color: config.color,
          border: `1.5px solid ${config.color}`,
          '& .MuiChip-icon': {
            color: config.color,
            marginLeft: '6px',
          },
          '&:hover': {
            backgroundColor: alpha(config.color, 0.2),
          },
        }}
      />
    </motion.div>
  ) : (
    <Chip
      icon={showIcon ? <Icon sx={{ fontSize: iconSize }} /> : undefined}
      label={showLabel ? config.label : level.toUpperCase()}
      size={chipSize}
      sx={{
        height,
        fontSize,
        fontWeight: 600,
        backgroundColor: config.backgroundColor,
        color: config.color,
        border: `1.5px solid ${config.color}`,
        '& .MuiChip-icon': {
          color: config.color,
          marginLeft: '6px',
        },
        '&:hover': {
          backgroundColor: alpha(config.color, 0.2),
        },
      }}
    />
  );

  return (
    <Tooltip title={config.tooltip} arrow placement="top">
      <Box sx={{ display: 'inline-block' }}>{chipContent}</Box>
    </Tooltip>
  );
}
