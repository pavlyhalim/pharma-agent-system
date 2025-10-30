import { useState, useMemo, useCallback } from 'react';
import {
  Box,
  Typography,
  AppBar,
  Toolbar,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  useMediaQuery,
  useTheme,
  Divider,
  Avatar,
  Fade,
  Chip,
  alpha,
  Tooltip,
  Button,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Science as ScienceIcon,
  Dashboard as DashboardIcon,
  Info as InfoIcon,
  Settings as SettingsIcon,
  Close as CloseIcon,
  LocalHospital as HospitalIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import DrugSearch from './components/DrugSearch';
import ResultsDisplay from './components/ResultsDisplay';
import AnalysisProgress from './components/AnalysisProgress';
import { apiClient } from './services/api';
import { useSSE } from './hooks/useSSE';
import type { DrugQuery, DrugAnalysisResult } from './types';
import { colors } from './theme';

const DRAWER_WIDTH = 280;

function App() {
  const [results, setResults] = useState<DrugAnalysisResult | null>(null);
  const [currentQuery, setCurrentQuery] = useState<DrugQuery | null>(null);
  const [sseEnabled, setSSEEnabled] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(true);

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Stabilize SSE URL to prevent multiple connections
  const sseUrl = useMemo(() => {
    return currentQuery ? apiClient.getAnalyzeStreamURL(currentQuery) : '';
  }, [currentQuery]);

  // Stabilize SSE body to prevent multiple connections
  const sseBody = useMemo(() => {
    return currentQuery ? apiClient.getAnalyzeStreamBody(currentQuery) : undefined;
  }, [currentQuery]);

  // Stabilize callbacks to prevent multiple connections
  const handleComplete = useCallback((result: DrugAnalysisResult) => {
    // Validation logging for debugging
    console.log('[Analysis Complete] Validating results...');

    if (!result) {
      console.error('[Analysis Complete] ERROR: Result is null or undefined');
      setResults(null);
      setSSEEnabled(false);
      return;
    }

    // Log result structure
    console.log('[Analysis Complete] Result structure:', {
      hasDrug: !!result.drug,
      hasIndication: !!result.indication,
      hasNonResponseRate: !!result.non_response_rate,
      overallRate: result.non_response_rate?.overall?.rate,
      variantsCount: result.variants?.length || 0,
      hypothesesCount: result.hypotheses?.length || 0,
      citationsCount: result.citations?.length || 0,
      hasDrugBankData: !!result.drugbank_data,
      hasMetadata: !!result.metadata
    });

    // Validate critical fields
    const warnings: string[] = [];
    if (!result.drug) warnings.push('Missing drug name');
    if (!result.non_response_rate) warnings.push('Missing non-response rate data');
    if (!result.variants || result.variants.length === 0) warnings.push('No genetic variants found');
    if (!result.hypotheses || result.hypotheses.length === 0) warnings.push('No recommendations generated');
    if (!result.citations || result.citations.length === 0) warnings.push('No citations found');

    if (warnings.length > 0) {
      console.warn('[Analysis Complete] Data warnings:', warnings);
    } else {
      console.log('[Analysis Complete] ✓ All critical fields present');
    }

    setResults(result);
    setSSEEnabled(false);
  }, []);

  const handleError = useCallback((errorMsg: string) => {
    console.error('Analysis failed:', errorMsg);
    setSSEEnabled(false);
  }, []);

  // SSE connection for real-time progress
  const { data: progress, isComplete, error } = useSSE(
    sseUrl,
    {
      enabled: sseEnabled && currentQuery !== null,
      body: sseBody,
      onComplete: handleComplete,
      onError: handleError
    }
  );

  const handleSearch = (query: DrugQuery) => {
    setResults(null);
    setCurrentQuery(query);
    setSSEEnabled(true);
  };

  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };

  // Drawer content
  const drawerContent = (
    <Box sx={{ width: DRAWER_WIDTH, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Drawer Header */}
      <Box
        sx={{
          p: 3,
          background: colors.primaryAccessibleBg,
          color: colors.textPrimary,
          borderBottom: `2px solid ${colors.primaryMain}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Avatar
            sx={{
              bgcolor: colors.primaryMain,
              color: 'white',
              width: 40,
              height: 40,
            }}
          >
            <HospitalIcon />
          </Avatar>
          <Box>
            <Typography variant="subtitle1" fontWeight={700} color={colors.textPrimary}>
              PharmaGenix
            </Typography>
            <Typography variant="caption" sx={{ color: colors.textSecondary }}>
              v1.0.0
            </Typography>
          </Box>
        </Box>
        {isMobile && (
          <IconButton onClick={toggleDrawer} sx={{ color: colors.primaryMain }}>
            <CloseIcon />
          </IconButton>
        )}
      </Box>

      <Divider />

      {/* Navigation */}
      <List sx={{ flex: 1, p: 2 }}>
        <ListItem disablePadding sx={{ mb: 1 }}>
          <ListItemButton
            selected
            sx={{
              borderRadius: 2,
              '&.Mui-selected': {
                background: alpha(colors.primaryMain, 0.1),
                color: colors.primaryMain,
                '& .MuiListItemIcon-root': {
                  color: colors.primaryMain,
                },
              },
            }}
          >
            <ListItemIcon>
              <DashboardIcon />
            </ListItemIcon>
            <ListItemText
              primary="Analysis"
              primaryTypographyProps={{ fontWeight: 600 }}
            />
          </ListItemButton>
        </ListItem>

        <Tooltip title="Coming Soon - Research Database" arrow placement="right">
          <ListItem disablePadding sx={{ mb: 1 }}>
            <ListItemButton disabled sx={{ borderRadius: 2 }}>
              <ListItemIcon>
                <ScienceIcon />
              </ListItemIcon>
              <ListItemText
                primary="Research"
                secondary="Coming Soon"
                secondaryTypographyProps={{ variant: 'caption' }}
              />
            </ListItemButton>
          </ListItem>
        </Tooltip>

        <Tooltip title="Coming Soon - About & Documentation" arrow placement="right">
          <ListItem disablePadding sx={{ mb: 1 }}>
            <ListItemButton disabled sx={{ borderRadius: 2 }}>
              <ListItemIcon>
                <InfoIcon />
              </ListItemIcon>
              <ListItemText
                primary="About"
                secondary="Coming Soon"
                secondaryTypographyProps={{ variant: 'caption' }}
              />
            </ListItemButton>
          </ListItem>
        </Tooltip>

        <Tooltip title="Coming Soon - User Preferences" arrow placement="right">
          <ListItem disablePadding>
            <ListItemButton disabled sx={{ borderRadius: 2 }}>
              <ListItemIcon>
                <SettingsIcon />
              </ListItemIcon>
              <ListItemText
                primary="Settings"
                secondary="Coming Soon"
                secondaryTypographyProps={{ variant: 'caption' }}
              />
            </ListItemButton>
          </ListItem>
        </Tooltip>
      </List>

      <Divider />

      {/* Footer */}
      <Box sx={{ p: 2 }}>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
          Powered by AI
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
          <Chip label="Gemini 2.5" size="small" variant="outlined" />
          <Chip label="LangGraph" size="small" variant="outlined" />
        </Box>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          background: 'white',
          borderBottom: `1px solid ${colors.divider}`,
          zIndex: theme.zIndex.drawer + 1,
        }}
      >
        <Toolbar>
          <IconButton
            edge="start"
            color="primary"
            onClick={toggleDrawer}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flex: 1 }}>
            <Avatar
              sx={{
                bgcolor: alpha(colors.primaryMain, 0.1),
                color: colors.primaryMain,
                width: 36,
                height: 36,
              }}
            >
              <HospitalIcon fontSize="small" />
            </Avatar>
            <Box>
              <Typography
                variant="h6"
                component="div"
                sx={{
                  fontWeight: 700,
                  background: colors.primaryGradient,
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                }}
              >
                PharmaGenix Analysis Platform
              </Typography>
              <Typography variant="caption" color="text.secondary">
                AI-Powered Pharmacogenomics
              </Typography>
            </Box>
          </Box>

          {sseEnabled && !isComplete && (
            <Chip
              label="Analysis Running"
              color="primary"
              size="small"
              sx={{
                animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                '@keyframes pulse': {
                  '0%, 100%': { opacity: 1 },
                  '50%': { opacity: 0.5 },
                },
              }}
            />
          )}
        </Toolbar>
      </AppBar>

      {/* Drawer */}
      <Drawer
        variant={isMobile ? 'temporary' : 'permanent'}
        open={isMobile ? drawerOpen : true}
        onClose={toggleDrawer}
        ModalProps={{
          keepMounted: true, // Better mobile performance
        }}
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: DRAWER_WIDTH,
            boxSizing: 'border-box',
            border: 'none',
            borderRight: `1px solid ${colors.divider}`,
            ...(isMobile ? {
              // Mobile: Full height overlay
              zIndex: theme.zIndex.drawer,
            } : {
              // Desktop: Start below AppBar
              top: 64, // Standard Material-UI Toolbar height
              height: 'calc(100% - 64px)',
              zIndex: theme.zIndex.drawer - 1,
            }),
          },
        }}
      >
        {drawerContent}
      </Drawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          pt: 10,
          pb: 4,
          minHeight: '100vh',
        }}
      >
        <Box
          sx={{
            maxWidth: { xs: '100%', sm: '100%', md: '1400px', lg: '1536px' },
            mx: 'auto', // Center horizontally with equal margins
            px: 0, // NO padding - each section controls its own spacing
            width: '100%',
          }}
        >
          {/* Hero Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Box
              sx={{
                mb: 4,
                mx: { xs: 2, sm: 3, md: 4, lg: 6 }, // Horizontal margins for spacing
                p: 4,
                borderRadius: 4,
                background: colors.primaryAccessibleBg,
                color: colors.textPrimary,
                border: `2px solid ${colors.primaryMain}`,
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  right: 0,
                  width: '300px',
                  height: '300px',
                  background: `radial-gradient(circle, ${alpha(colors.primaryMain, 0.08)} 0%, transparent 70%)`,
                  borderRadius: '50%',
                  transform: 'translate(50%, -50%)',
                },
              }}
            >
              <Box sx={{ position: 'relative', zIndex: 1 }}>
                <Typography variant="h3" component="h1" gutterBottom fontWeight={800}>
                  Drug Non-Response Analysis
                </Typography>
                <Typography variant="h6" sx={{ color: colors.textSecondary, maxWidth: '800px' }}>
                  Advanced AI-powered pharmacogenomic analysis to quantify non-response rates,
                  identify genetic drivers, and propose evidence-based solutions
                </Typography>
              </Box>
            </Box>
          </motion.div>

          {/* Search Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <Box
              sx={{
                mb: 4,
                mx: { xs: 2, sm: 3, md: 4, lg: 6 }, // Same horizontal margins as hero
                // Grid spacing={3} creates -12px negative margin, compensate with padding
                p: { xs: 2, sm: 3, md: '44px' }, // 32px + 12px to offset Grid's -12px margin
                borderRadius: 3,
                bgcolor: 'white',
                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
              }}
            >
              <DrugSearch onSearch={handleSearch} isLoading={sseEnabled && !isComplete} />
            </Box>
          </motion.div>

          {/* Progress Display */}
          <AnimatePresence>
            {sseEnabled && !isComplete && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
              >
                <AnalysisProgress progress={progress} error={error} />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Results */}
          <AnimatePresence>
            {results && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.5 }}
              >
                <ResultsDisplay results={results} />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Empty Results State */}
          {isComplete && !results && currentQuery && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <Box
                sx={{
                  p: 4,
                  borderRadius: 3,
                  bgcolor: 'white',
                  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
                  textAlign: 'center',
                }}
              >
                <Box
                  sx={{
                    width: 80,
                    height: 80,
                    borderRadius: '50%',
                    bgcolor: alpha(colors.warningMain, 0.1),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 24px',
                  }}
                >
                  <InfoIcon sx={{ fontSize: 40, color: colors.warningMain }} />
                </Box>
                <Typography variant="h5" gutterBottom fontWeight={700}>
                  Analysis Completed with No Results
                </Typography>
                <Typography variant="body1" color="text.secondary" paragraph sx={{ maxWidth: 600, margin: '0 auto' }}>
                  The analysis for <strong>{currentQuery.drug}</strong> completed, but no meaningful data could be extracted.
                  This may occur if:
                </Typography>
                <Box component="ul" sx={{ textAlign: 'left', maxWidth: 500, margin: '16px auto', color: 'text.secondary' }}>
                  <li>The drug has very limited published research</li>
                  <li>Non-response data is not well-documented in the literature</li>
                  <li>The backend services encountered temporary issues</li>
                  <li>The search parameters were too restrictive</li>
                </Box>
                <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'center' }}>
                  <Button
                    variant="contained"
                    size="large"
                    onClick={() => {
                      setResults(null);
                      setCurrentQuery(null);
                      setSSEEnabled(false);
                    }}
                  >
                    Try Another Drug
                  </Button>
                  <Button
                    variant="outlined"
                    size="large"
                    onClick={() => {
                      if (currentQuery) {
                        handleSearch(currentQuery);
                      }
                    }}
                  >
                    Retry Analysis
                  </Button>
                </Box>
              </Box>
            </motion.div>
          )}

          {/* Error State */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <Box
                sx={{
                  p: 4,
                  borderRadius: 3,
                  bgcolor: 'white',
                  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: '50%',
                      bgcolor: alpha(colors.errorMain, 0.1),
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Box sx={{ fontSize: 24 }}>⚠️</Box>
                  </Box>
                  <Box>
                    <Typography variant="h6" fontWeight={700} color="error">
                      Analysis Error
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      The analysis encountered an error
                    </Typography>
                  </Box>
                </Box>
                <Typography variant="body2" sx={{ p: 2, bgcolor: alpha(colors.errorMain, 0.05), borderRadius: 2, fontFamily: 'monospace' }}>
                  {error}
                </Typography>
                <Button
                  variant="contained"
                  size="large"
                  fullWidth
                  sx={{ mt: 3 }}
                  onClick={() => {
                    if (currentQuery) {
                      handleSearch(currentQuery);
                    }
                  }}
                >
                  Retry Analysis
                </Button>
              </Box>
            </motion.div>
          )}

          {/* Footer */}
          <Fade in timeout={1000}>
            <Box sx={{ mt: 8, textAlign: 'center' }}>
              <Divider sx={{ mb: 3 }} />
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Powered by Google Gemini 2.5 Flash, LangGraph, PubMed, ClinicalTrials.gov, GWAS Catalog, PharmGKB
              </Typography>
              <Typography variant="caption" color="text.secondary">
                © 2025 PharmaGenix. All rights reserved.
              </Typography>
            </Box>
          </Fade>
        </Box>
      </Box>
    </Box>
  );
}

export default App;
