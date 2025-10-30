/**
 * Real-time progress display for drug analysis with stunning animations
 */

import {
  Box,
  LinearProgress,
  Alert,
  Stepper,
  Step,
  StepLabel,
  Typography,
  Paper,
  Chip,
  alpha,
} from '@mui/material';
import {
  CheckCircle,
  RadioButtonUnchecked,
  AccessTime,
  Speed,
  Science as ScienceIcon,
  Article as ArticleIcon,
  Biotech as BiotechIcon,
  Analytics as AnalyticsIcon,
  Lightbulb as LightbulbIcon,
} from '@mui/icons-material';
import type { ProgressUpdate } from '@/hooks/useSSE';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { colors } from '@/theme';

interface AnalysisProgressProps {
  progress: ProgressUpdate | null;
  error: string | null;
}

const STEPS = [
  {
    key: 'starting',
    label: 'Initializing',
    description: 'Preparing analysis pipeline',
    icon: ScienceIcon,
    color: colors.infoMain,
  },
  {
    key: 'literature_mining',
    label: 'Literature Mining',
    description: 'Searching medical databases',
    icon: ArticleIcon,
    color: colors.primaryMain,
  },
  {
    key: 'genetics_analysis',
    label: 'Genetics Analysis',
    description: 'Analyzing genetic variants',
    icon: BiotechIcon,
    color: colors.secondaryMain,
  },
  {
    key: 'normalizing',
    label: 'Data Processing',
    description: 'Computing metrics & statistics',
    icon: AnalyticsIcon,
    color: colors.accentMain,
  },
  {
    key: 'generating_hypotheses',
    label: 'AI Recommendations',
    description: 'Generating evidence-based hypotheses',
    icon: LightbulbIcon,
    color: colors.successMain,
  },
];

function getActiveStep(step: string | undefined): number {
  if (!step) return 0;

  const stepMap: Record<string, number> = {
    starting: 0,
    fetching_drugbank: 0,
    literature_mining: 1,
    extracting_article: 1,
    literature_complete: 1,
    genetics_analysis: 2,
    genetics_complete: 2,
    normalizing: 3,
    normalization_complete: 3,
    generating_hypotheses: 4,
    hypotheses_complete: 4,
  };

  return stepMap[step] ?? 0;
}

function formatTime(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${minutes}m ${secs}s`;
}

export default function AnalysisProgress({ progress, error }: AnalysisProgressProps) {
  const [startTime, setStartTime] = useState<number | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    if (progress && startTime === null) {
      setStartTime(Date.now());
    }
  }, [progress, startTime]);

  useEffect(() => {
    if (!startTime || !progress) return;

    const timer = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    return () => clearInterval(timer);
  }, [startTime, progress]);

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        <Paper elevation={3} sx={{ p: 4, mt: 3, borderRadius: 3 }}>
          <Alert severity="error" sx={{ borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>
              Analysis Failed
            </Typography>
            {error}
          </Alert>
        </Paper>
      </motion.div>
    );
  }

  if (!progress) {
    return null;
  }

  const activeStep = getActiveStep(progress.step);
  const progressValue = progress.progress;
  const currentStepConfig = STEPS[activeStep];

  const estimatedTotalTime = elapsedTime > 0 && progressValue > 0
    ? (elapsedTime / progressValue) * 100
    : 120;
  const estimatedRemaining = Math.max(0, estimatedTotalTime - elapsedTime);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Paper
        elevation={3}
        sx={{
          p: 4,
          mt: 3,
          borderRadius: 3,
          background: `linear-gradient(135deg, ${alpha(colors.primaryMain, 0.03)} 0%, ${alpha(colors.secondaryMain, 0.03)} 100%)`,
          border: `1px solid ${alpha(colors.primaryMain, 0.1)}`,
        }}
      >
        {/* Header with Time Tracking */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 48,
                height: 48,
                borderRadius: '50%',
                background: colors.primaryGradient,
                color: 'white',
              }}
            >
              <currentStepConfig.icon />
            </motion.div>
            <Box>
              <Typography variant="h6" fontWeight={700}>
                Analysis in Progress
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {currentStepConfig.description}
              </Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', gap: 1 }}>
            <Chip
              icon={<AccessTime />}
              label={`${formatTime(elapsedTime)}`}
              size="small"
              sx={{
                fontWeight: 600,
                bgcolor: alpha(colors.primaryMain, 0.1),
                color: colors.primaryMain,
              }}
            />
            {progressValue < 95 && (
              <Chip
                icon={<Speed />}
                label={`~${formatTime(estimatedRemaining)}`}
                size="small"
                sx={{
                  fontWeight: 600,
                  bgcolor: alpha(colors.secondaryMain, 0.1),
                  color: colors.secondaryMain,
                }}
              />
            )}
          </Box>
        </Box>

        {/* Status Message */}
        <Alert
          severity="info"
          icon={<RadioButtonUnchecked />}
          sx={{
            mb: 3,
            borderRadius: 2,
            bgcolor: alpha(colors.infoMain, 0.08),
            border: `1px solid ${alpha(colors.infoMain, 0.2)}`,
          }}
        >
          <Typography variant="body1" fontWeight={600}>
            {progress.message}
          </Typography>
        </Alert>

        {/* Animated Stepper */}
        <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 4 }}>
          {STEPS.map((step, index) => {
            const isCompleted = activeStep > index;
            const isActive = activeStep === index;
            const StepIcon = step.icon;

            return (
              <Step key={step.key} completed={isCompleted}>
                <StepLabel
                  StepIconComponent={() => (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ duration: 0.3, delay: index * 0.1 }}
                    >
                      <Box
                        sx={{
                          width: 40,
                          height: 40,
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          bgcolor: isCompleted
                            ? step.color
                            : isActive
                            ? alpha(step.color, 0.2)
                            : alpha(colors.textSecondary, 0.1),
                          color: isCompleted || isActive ? 'white' : colors.textSecondary,
                          transition: 'all 0.3s',
                          ...(isActive && {
                            animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                            '@keyframes pulse': {
                              '0%, 100%': { boxShadow: `0 0 0 0 ${alpha(step.color, 0.7)}` },
                              '50%': { boxShadow: `0 0 0 8px ${alpha(step.color, 0)}` },
                            },
                          }),
                        }}
                      >
                        {isCompleted ? <CheckCircle /> : <StepIcon fontSize="small" />}
                      </Box>
                    </motion.div>
                  )}
                >
                  <Typography
                    variant="caption"
                    fontWeight={isActive ? 700 : 500}
                    color={isActive ? 'primary' : 'text.secondary'}
                    sx={{ mt: 1 }}
                  >
                    {step.label}
                  </Typography>
                </StepLabel>
              </Step>
            );
          })}
        </Stepper>

        {/* Enhanced Progress Bar */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" fontWeight={600} color="text.secondary">
              Overall Progress
            </Typography>
            <Typography variant="h6" fontWeight={700} color="primary">
              {progressValue}%
            </Typography>
          </Box>
          <Box sx={{ position: 'relative' }}>
            <LinearProgress
              variant="determinate"
              value={progressValue}
              sx={{
                height: 16,
                borderRadius: 8,
                bgcolor: alpha(colors.primaryMain, 0.1),
              }}
            />
            <Typography
              variant="caption"
              sx={{
                position: 'absolute',
                left: '50%',
                top: '50%',
                transform: 'translate(-50%, -50%)',
                fontWeight: 700,
                color: progressValue > 50 ? 'white' : colors.textPrimary,
              }}
            >
              {STEPS[activeStep]?.label}
            </Typography>
          </Box>
        </Box>

        {/* Fun Fact or Tip */}
        <Box
          sx={{
            mt: 3,
            p: 2,
            borderRadius: 2,
            bgcolor: alpha(colors.accentMain, 0.05),
            border: `1px dashed ${alpha(colors.accentMain, 0.3)}`,
          }}
        >
          <Typography variant="caption" color="text.secondary" fontWeight={500}>
            Did you know? Our AI analyzes thousands of research papers and clinical trials to provide you with the most comprehensive pharmacogenomic insights.
          </Typography>
        </Box>
      </Paper>
    </motion.div>
  );
}
