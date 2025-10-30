/**
 * Reusable Metric Card Component
 * Displays key metrics with icons, values, and trends
 */

import { Card, CardContent, Box, Typography, Chip, alpha } from '@mui/material';
import { SvgIconComponent } from '@mui/icons-material';
import { motion } from 'framer-motion';
import { colors } from '@/theme';

export interface MetricCardProps {
  icon: SvgIconComponent;
  title: string;
  value: string | number;
  subtitle?: string;
  badge?: {
    label: string;
    color: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  };
  trend?: {
    value: number;
    label: string;
  };
  gradient?: string;
  iconColor?: string;
  delay?: number;
}

export default function MetricCard({
  icon: Icon,
  title,
  value,
  subtitle,
  badge,
  trend,
  gradient,
  iconColor = colors.primaryMain,
  delay = 0,
}: MetricCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      whileHover={{
        y: -8,
        transition: { duration: 0.2 },
      }}
      style={{ height: '100%' }}
    >
      <Card
        sx={{
          height: '100%',
          position: 'relative',
          overflow: 'hidden',
          '&::before': gradient
            ? {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: '4px',
                background: gradient,
              }
            : undefined,
        }}
      >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
          {/* Icon */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 48,
              height: 48,
              borderRadius: 2,
              backgroundColor: alpha(iconColor, 0.1),
              color: iconColor,
            }}
          >
            <Icon sx={{ fontSize: 28 }} />
          </Box>

          {/* Badge */}
          {badge && (
            <Chip
              label={badge.label}
              color={badge.color}
              size="small"
              sx={{ fontWeight: 600 }}
            />
          )}
        </Box>

        {/* Title */}
        <Typography variant="body2" color="text.secondary" gutterBottom fontWeight={500}>
          {title}
        </Typography>

        {/* Value */}
        <Typography
          variant="h3"
          sx={{
            fontWeight: 700,
            background: gradient || 'inherit',
            ...(gradient && {
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }),
            mb: subtitle || trend ? 1 : 0,
          }}
        >
          {value}
        </Typography>

        {/* Subtitle */}
        {subtitle && (
          <Typography variant="body2" color="text.secondary">
            {subtitle}
          </Typography>
        )}

        {/* Trend Indicator */}
        {trend && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              mt: 1,
              pt: 1,
              borderTop: `1px solid ${colors.divider}`,
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 0.5,
                px: 1,
                py: 0.5,
                borderRadius: 1,
                backgroundColor:
                  trend.value > 0
                    ? alpha(colors.successMain, 0.1)
                    : trend.value < 0
                    ? alpha(colors.errorMain, 0.1)
                    : alpha(colors.textSecondary, 0.1),
                color:
                  trend.value > 0
                    ? colors.successMain
                    : trend.value < 0
                    ? colors.errorMain
                    : colors.textSecondary,
              }}
            >
              <Typography variant="caption" fontWeight={600}>
                {trend.value > 0 ? '+' : ''}
                {trend.value}%
              </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary">
              {trend.label}
            </Typography>
          </Box>
        )}
      </CardContent>
      </Card>
    </motion.div>
  );
}
