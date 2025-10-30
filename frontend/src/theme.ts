/**
 * Professional Medical Theme for Pharmacogenomics Platform
 * Based on 2025 healthcare UI/UX research
 */

import { createTheme } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';

// Modern Medical Color Palette
const colors = {
  // Primary - Medical Blue with gradient
  primaryMain: '#0A7AFF',
  primaryLight: '#4D9FFF',
  primaryDark: '#0056B3',
  primaryGradient: 'linear-gradient(135deg, #0A7AFF 0%, #0056B3 100%)',

  // Secondary - Health Green
  secondaryMain: '#10B981',
  secondaryLight: '#34D399',
  secondaryDark: '#059669',
  secondaryGradient: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',

  // Accent - Warm Orange for warnings/attention
  accentMain: '#F59E0B',
  accentLight: '#FBBF24',
  accentDark: '#D97706',

  // Error - Medical Red
  errorMain: '#EF4444',
  errorLight: '#F87171',
  errorDark: '#DC2626',

  // Success - Vibrant Green
  successMain: '#10B981',
  successLight: '#34D399',
  successDark: '#059669',

  // Warning - Amber
  warningMain: '#F59E0B',
  warningLight: '#FBBF24',
  warningDark: '#D97706',

  // Info - Cyan
  infoMain: '#06B6D4',
  infoLight: '#22D3EE',
  infoDark: '#0891B2',

  // Neutral/Background Colors
  backgroundDefault: '#F8FAFC',
  backgroundPaper: '#FFFFFF',
  backgroundElevated: '#FFFFFF',

  // Text Colors
  textPrimary: '#0F172A',
  textSecondary: '#475569',
  textDisabled: '#94A3B8',

  // Divider
  divider: '#E2E8F0',

  // Confidence Badge Colors
  confidenceHigh: '#10B981',
  confidenceModerate: '#F59E0B',
  confidenceLow: '#EF4444',

  // WCAG AA Accessible Backgrounds (12:1+ contrast with dark text)
  primaryAccessibleBg: '#E3F2FF',  // Light blue background
  secondaryAccessibleBg: '#ECFDF5',  // Light green background
  infoAccessibleBg: '#ECFEFF',  // Light cyan background
};

// Create theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: colors.primaryMain,
      light: colors.primaryLight,
      dark: colors.primaryDark,
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: colors.secondaryMain,
      light: colors.secondaryLight,
      dark: colors.secondaryDark,
      contrastText: '#FFFFFF',
    },
    error: {
      main: colors.errorMain,
      light: colors.errorLight,
      dark: colors.errorDark,
    },
    warning: {
      main: colors.warningMain,
      light: colors.warningLight,
      dark: colors.warningDark,
    },
    info: {
      main: colors.infoMain,
      light: colors.infoLight,
      dark: colors.infoDark,
    },
    success: {
      main: colors.successMain,
      light: colors.successLight,
      dark: colors.successDark,
    },
    background: {
      default: colors.backgroundDefault,
      paper: colors.backgroundPaper,
    },
    text: {
      primary: colors.textPrimary,
      secondary: colors.textSecondary,
      disabled: colors.textDisabled,
    },
    divider: colors.divider,
  },

  // Typography System
  typography: {
    fontFamily: '"Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',

    // Display Typography
    h1: {
      fontSize: '3.5rem',
      fontWeight: 800,
      lineHeight: 1.2,
      letterSpacing: '-0.02em',
      color: colors.textPrimary,
    },
    h2: {
      fontSize: '2.5rem',
      fontWeight: 700,
      lineHeight: 1.3,
      letterSpacing: '-0.01em',
      color: colors.textPrimary,
    },
    h3: {
      fontSize: '2rem',
      fontWeight: 700,
      lineHeight: 1.4,
      letterSpacing: '-0.01em',
      color: colors.textPrimary,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.5,
      color: colors.textPrimary,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.5,
      color: colors.textPrimary,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.5,
      color: colors.textPrimary,
    },

    // Body Typography
    body1: {
      fontSize: '1rem',
      fontWeight: 400,
      lineHeight: 1.6,
      color: colors.textPrimary,
    },
    body2: {
      fontSize: '0.875rem',
      fontWeight: 400,
      lineHeight: 1.6,
      color: colors.textSecondary,
    },

    // Utility Typography
    subtitle1: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.5,
      color: colors.textPrimary,
    },
    subtitle2: {
      fontSize: '0.875rem',
      fontWeight: 500,
      lineHeight: 1.5,
      color: colors.textSecondary,
    },
    caption: {
      fontSize: '0.75rem',
      fontWeight: 400,
      lineHeight: 1.5,
      color: colors.textSecondary,
    },
    overline: {
      fontSize: '0.75rem',
      fontWeight: 600,
      lineHeight: 1.5,
      letterSpacing: '0.08em',
      textTransform: 'uppercase',
      color: colors.textSecondary,
    },
    button: {
      fontSize: '0.875rem',
      fontWeight: 600,
      lineHeight: 1.5,
      letterSpacing: '0.02em',
      textTransform: 'none',
    },
  },

  // Spacing System (8px grid)
  spacing: 8,

  // Shape
  shape: {
    borderRadius: 12,
  },

  // Shadows - Enhanced depth system
  shadows: [
    'none',
    '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 30px 60px -15px rgba(0, 0, 0, 0.3)',
    '0 35px 70px -15px rgba(0, 0, 0, 0.35)',
    '0 40px 80px -15px rgba(0, 0, 0, 0.4)',
    '0 45px 90px -15px rgba(0, 0, 0, 0.45)',
    '0 50px 100px -15px rgba(0, 0, 0, 0.5)',
    '0 55px 110px -15px rgba(0, 0, 0, 0.55)',
    '0 60px 120px -15px rgba(0, 0, 0, 0.6)',
    '0 65px 130px -15px rgba(0, 0, 0, 0.65)',
    '0 70px 140px -15px rgba(0, 0, 0, 0.7)',
    '0 75px 150px -15px rgba(0, 0, 0, 0.75)',
    '0 80px 160px -15px rgba(0, 0, 0, 0.8)',
    '0 85px 170px -15px rgba(0, 0, 0, 0.85)',
    '0 90px 180px -15px rgba(0, 0, 0, 0.9)',
    '0 95px 190px -15px rgba(0, 0, 0, 0.95)',
    '0 100px 200px -15px rgba(0, 0, 0, 1)',
    '0 105px 210px -15px rgba(0, 0, 0, 1)',
    '0 110px 220px -15px rgba(0, 0, 0, 1)',
    '0 115px 230px -15px rgba(0, 0, 0, 1)',
  ],

  // Component Overrides
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          padding: '10px 24px',
          fontSize: '0.9375rem',
          fontWeight: 600,
          textTransform: 'none',
          boxShadow: 'none',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            transform: 'translateY(-1px)',
          },
        },
        contained: {
          background: colors.primaryGradient,
          '&:hover': {
            background: colors.primaryGradient,
            filter: 'brightness(1.1)',
          },
        },
        containedPrimary: {
          background: colors.primaryGradient,
        },
        containedSecondary: {
          background: colors.secondaryGradient,
        },
        sizeLarge: {
          padding: '14px 32px',
          fontSize: '1rem',
        },
      },
    },

    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
        rounded: {
          borderRadius: 16,
        },
        elevation0: {
          boxShadow: 'none',
        },
        elevation1: {
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        },
        elevation2: {
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        },
        elevation3: {
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        },
      },
    },

    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            boxShadow: '0 10px 20px rgba(0, 0, 0, 0.12)',
            transform: 'translateY(-4px)',
          },
        },
      },
    },

    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 500,
          borderRadius: 8,
          height: 28,
        },
        filled: {
          fontWeight: 600,
        },
        colorPrimary: {
          background: alpha(colors.primaryMain, 0.1),
          color: colors.primaryMain,
          '&:hover': {
            background: alpha(colors.primaryMain, 0.2),
          },
        },
        colorSecondary: {
          background: alpha(colors.secondaryMain, 0.1),
          color: colors.secondaryMain,
          '&:hover': {
            background: alpha(colors.secondaryMain, 0.2),
          },
        },
      },
    },

    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
            backgroundColor: colors.backgroundPaper,
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              backgroundColor: alpha(colors.primaryMain, 0.02),
            },
            '&.Mui-focused': {
              backgroundColor: colors.backgroundPaper,
              boxShadow: `0 0 0 3px ${alpha(colors.primaryMain, 0.1)}`,
            },
          },
        },
      },
    },

    MuiAutocomplete: {
      styleOverrides: {
        paper: {
          borderRadius: 12,
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.15)',
          marginTop: 8,
        },
        option: {
          padding: 12,
          '&[aria-selected="true"]': {
            backgroundColor: alpha(colors.primaryMain, 0.1),
          },
          '&.Mui-focused': {
            backgroundColor: alpha(colors.primaryMain, 0.05),
          },
        },
      },
    },

    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          padding: '12px 16px',
        },
        standardInfo: {
          backgroundColor: alpha(colors.infoMain, 0.1),
          color: colors.textPrimary,
        },
        standardSuccess: {
          backgroundColor: alpha(colors.successMain, 0.1),
          color: colors.textPrimary,
        },
        standardWarning: {
          backgroundColor: alpha(colors.warningMain, 0.1),
          color: colors.textPrimary,
        },
        standardError: {
          backgroundColor: alpha(colors.errorMain, 0.1),
          color: colors.textPrimary,
        },
      },
    },

    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          height: 12,
          backgroundColor: alpha(colors.primaryMain, 0.1),
        },
        bar: {
          borderRadius: 10,
          background: colors.primaryGradient,
        },
      },
    },

    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${colors.divider}`,
        },
        head: {
          fontWeight: 600,
          backgroundColor: alpha(colors.primaryMain, 0.05),
          color: colors.textPrimary,
        },
      },
    },

    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: colors.textPrimary,
          fontSize: '0.875rem',
          padding: '8px 12px',
          borderRadius: 8,
        },
        arrow: {
          color: colors.textPrimary,
        },
      },
    },

    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          fontSize: '0.9375rem',
          minHeight: 48,
          '&.Mui-selected': {
            color: colors.primaryMain,
          },
        },
      },
    },

    MuiTabs: {
      styleOverrides: {
        indicator: {
          height: 3,
          borderRadius: 3,
          background: colors.primaryGradient,
        },
      },
    },
  },
});

// Export colors for use in styled components
export { colors };
export default theme;
