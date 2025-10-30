import { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Card,
  CardContent,
  Divider,
  Alert,
  Link,
  Tabs,
  Tab,
  alpha,
  LinearProgress,
} from '@mui/material';
import {
  Assessment as MetricsIcon,
  Science as GeneIcon,
  Lightbulb as HypothesisIcon,
  Info as InfoIcon,
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import type { DrugAnalysisResult } from '@/types';
import DrugBankInfo from './DrugBankInfo';
import MetricCard from './MetricCard';
import ConfidenceIndicator from './ConfidenceIndicator';
import { colors } from '@/theme';

interface ResultsDisplayProps {
  results: DrugAnalysisResult;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`results-tabpanel-${index}`}
      aria-labelledby={`results-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function ResultsDisplay({ results }: ResultsDisplayProps) {
  const [tabValue, setTabValue] = useState(0);
  const overallMetric = results.non_response_rate.overall;
  const subgroups = results.non_response_rate.by_subgroup;

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const formatPercentage = (rate: number | null | undefined) => {
    if (rate === null || rate === undefined) return 'N/A';
    return (rate * 100).toFixed(1) + '%';
  };

  const formatCI = (lower: number | null | undefined, upper: number | null | undefined) => {
    if (lower === null || lower === undefined || upper === null || upper === undefined) {
      return 'N/A';
    }
    return `${formatPercentage(lower)} - ${formatPercentage(upper)}`;
  };

  const getDataQualityColor = (quality: string) => {
    switch (quality) {
      case 'high':
        return colors.successMain;
      case 'moderate':
        return colors.warningMain;
      default:
        return colors.errorMain;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* Hero Header */}
      <Box
        sx={{
          mb: 4,
          p: 4,
          borderRadius: 4,
          background: colors.primaryAccessibleBg,
          color: colors.textPrimary,
          border: `2px solid ${colors.primaryMain}`,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <Box sx={{ position: 'relative', zIndex: 1 }}>
          <Typography variant="h3" gutterBottom fontWeight={800}>
            {results.drug}
          </Typography>
          {results.indication && (
            <Typography variant="h6" sx={{ color: colors.textSecondary, mb: 2 }}>
              Indication: {results.indication}
            </Typography>
          )}
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, alignItems: 'center' }}>
            <Chip
              label={`Quality: ${results.metadata.data_quality.toUpperCase()}`}
              sx={{
                bgcolor: alpha(getDataQualityColor(results.metadata.data_quality), 0.1),
                color: getDataQualityColor(results.metadata.data_quality),
                border: `1px solid ${getDataQualityColor(results.metadata.data_quality)}`,
                fontWeight: 700,
              }}
            />
            <Chip
              label={`${results.metadata.studies_analyzed} Studies`}
              sx={{
                bgcolor: alpha(colors.primaryMain, 0.1),
                color: colors.primaryMain,
                border: `1px solid ${colors.primaryMain}`,
                fontWeight: 600
              }}
            />
            <Chip
              label={`${results.metadata.total_patients.toLocaleString()} Patients`}
              sx={{
                bgcolor: alpha(colors.primaryMain, 0.1),
                color: colors.primaryMain,
                border: `1px solid ${colors.primaryMain}`,
                fontWeight: 600
              }}
            />
          </Box>
        </Box>
      </Box>

      {/* Warnings */}
      {results.metadata.warnings && results.metadata.warnings.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Alert severity="warning" sx={{ mb: 3, borderRadius: 2 }}>
            {results.metadata.warnings.join('; ')}
          </Alert>
        </motion.div>
      )}

      {/* Tabs Navigation */}
      <Paper elevation={0} sx={{ mb: 3, borderRadius: 3, border: `1px solid ${colors.divider}` }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{ borderBottom: `1px solid ${colors.divider}` }}
        >
          <Tab icon={<MetricsIcon />} label="Non-Response Metrics" iconPosition="start" />
          <Tab icon={<GeneIcon />} label="Genetic Variants" iconPosition="start" />
          <Tab icon={<HypothesisIcon />} label="Recommendations" iconPosition="start" />
          <Tab icon={<InfoIcon />} label="Drug Information" iconPosition="start" />
        </Tabs>

        {/* Tab 1: Non-Response Metrics */}
        <TabPanel value={tabValue} index={0}>
          <AnimatePresence mode="wait">
            <motion.div
              key="metrics"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <Grid container spacing={3}>
                {/* Overall Metric Card */}
                <Grid item xs={12}>
                  {overallMetric && overallMetric.rate !== null ? (
                    <MetricCard
                      icon={TrendingUpIcon}
                      title="Overall Non-Response Rate"
                      value={formatPercentage(overallMetric.rate)}
                      subtitle={`95% CI: ${formatCI(overallMetric.ci?.lower, overallMetric.ci?.upper)} | n = ${overallMetric.n?.toLocaleString() || 0}`}
                      gradient={colors.primaryGradient}
                      badge={{ label: 'Population-Wide', color: 'primary' }}
                    />
                  ) : (
                    <Alert severity="info" icon={<InfoIcon />} sx={{ borderRadius: 2 }}>
                      <Typography variant="body2" fontWeight={600} gutterBottom>
                        Insufficient Clinical Data
                      </Typography>
                      <Typography variant="body2">
                        No valid response rate data could be extracted from the literature for this drug.
                        The analysis includes genetic and mechanistic data in other tabs.
                      </Typography>
                    </Alert>
                  )}
                </Grid>

                {/* Subgroups */}
                {subgroups && Object.keys(subgroups).length > 0 && (
                  <>
                    <Grid item xs={12}>
                      <Typography variant="h5" gutterBottom fontWeight={700} sx={{ mt: 2 }}>
                        Subgroup Analysis
                      </Typography>
                    </Grid>
                    {Object.entries(subgroups).map(([name, metrics], index) => (
                      <Grid item xs={12} md={6} lg={4} key={name}>
                        <MetricCard
                          icon={PeopleIcon}
                          title={name}
                          value={formatPercentage(metrics.rate)}
                          subtitle={`95% CI: ${formatCI(metrics.ci?.lower, metrics.ci?.upper)}`}
                          iconColor={colors.secondaryMain}
                          delay={index * 0.1}
                        />
                      </Grid>
                    ))}
                  </>
                )}

                {/* Contributing Studies */}
                {overallMetric && overallMetric.contributing_studies && overallMetric.contributing_studies.length > 0 && (
                  <Grid item xs={12}>
                    <Paper sx={{ p: 3, borderRadius: 2, bgcolor: alpha(colors.infoMain, 0.05) }}>
                      <Typography variant="h6" gutterBottom fontWeight={600}>
                        Data Sources ({overallMetric.n_studies} {overallMetric.n_studies === 1 ? 'study' : 'studies'})
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 2 }}>
                        {overallMetric.contributing_studies.slice(0, 5).map((study: any, idx: number) => (
                          <Box
                            key={idx}
                            sx={{
                              p: 2,
                              borderRadius: 1,
                              bgcolor: 'white',
                              border: `1px solid ${colors.divider}`,
                            }}
                          >
                            <Link
                              href={study.url || `#${study.id}`}
                              target="_blank"
                              rel="noopener"
                              sx={{ fontWeight: 600 }}
                            >
                              {study.id}
                            </Link>
                            <Typography variant="body2" color="text.secondary">
                              n={study.n} | Rate: {formatPercentage(study.rate)}
                            </Typography>
                          </Box>
                        ))}
                        {overallMetric.contributing_studies.length > 5 && (
                          <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                            +{overallMetric.contributing_studies.length - 5} more studies
                          </Typography>
                        )}
                      </Box>
                    </Paper>
                  </Grid>
                )}
              </Grid>
            </motion.div>
          </AnimatePresence>
        </TabPanel>

        {/* Tab 2: Genetic Variants */}
        <TabPanel value={tabValue} index={1}>
          <AnimatePresence mode="wait">
            <motion.div
              key="variants"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              {results.variants.length > 0 ? (
                <TableContainer component={Paper} sx={{ borderRadius: 2 }}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell><strong>rsID</strong></TableCell>
                        <TableCell><strong>Gene</strong></TableCell>
                        <TableCell><strong>Allele</strong></TableCell>
                        <TableCell><strong>Effect</strong></TableCell>
                        <TableCell><strong>Frequency</strong></TableCell>
                        <TableCell><strong>Citations</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {results.variants.map((variant, index) => (
                        <TableRow
                          key={variant.rs_id}
                          component={motion.tr}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.05 }}
                          sx={{ '&:hover': { bgcolor: alpha(colors.primaryMain, 0.03) } }}
                        >
                          <TableCell>
                            <Link
                              href={`https://www.ncbi.nlm.nih.gov/snp/${variant.rs_id}`}
                              target="_blank"
                              rel="noopener"
                              sx={{ fontWeight: 600 }}
                            >
                              {variant.rs_id}
                            </Link>
                          </TableCell>
                          <TableCell>
                            <Chip label={variant.gene} size="small" color="primary" />
                          </TableCell>
                          <TableCell>{variant.allele || '-'}</TableCell>
                          <TableCell>
                            <Typography variant="body2">{variant.effect}</Typography>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                              {variant.frequency && Object.keys(variant.frequency).length > 0 ? (
                                Object.entries(variant.frequency).map(([pop, freq]) => (
                                  <Box key={pop} sx={{ minWidth: 60 }}>
                                    <Typography variant="caption" fontWeight={600}>
                                      {pop}
                                    </Typography>
                                    <LinearProgress
                                      variant="determinate"
                                      value={freq * 100}
                                      sx={{
                                        height: 6,
                                        borderRadius: 3,
                                        mt: 0.5,
                                        bgcolor: alpha(colors.secondaryMain, 0.1),
                                      }}
                                    />
                                    <Typography variant="caption" color="text.secondary">
                                      {(freq * 100).toFixed(0)}%
                                    </Typography>
                                  </Box>
                                ))
                              ) : (
                                <Typography variant="caption" color="text.secondary">
                                  No data
                                </Typography>
                              )}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                              {variant.citations.slice(0, 3).map((cite, i) => {
                                let url: string;
                                if (cite.startsWith('http://') || cite.startsWith('https://')) {
                                  url = cite;
                                } else if (cite.startsWith('PMID:')) {
                                  url = `https://pubmed.ncbi.nlm.nih.gov/${cite.replace('PMID:', '')}`;
                                } else {
                                  url = cite;
                                }

                                return (
                                  <Link
                                    key={i}
                                    href={url}
                                    target="_blank"
                                    rel="noopener"
                                    sx={{ fontSize: '0.75rem' }}
                                  >
                                    {cite}
                                  </Link>
                                );
                              })}
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Alert severity="info" icon={<InfoIcon />}>
                  <Typography>No genetic variants identified in the analysis.</Typography>
                </Alert>
              )}
            </motion.div>
          </AnimatePresence>
        </TabPanel>

        {/* Tab 3: Recommendations */}
        <TabPanel value={tabValue} index={2}>
          <AnimatePresence mode="wait">
            <motion.div
              key="hypotheses"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              {results.hypotheses && results.hypotheses.length > 0 ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  {results.hypotheses.map((hypothesis, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <Card
                        sx={{
                          borderLeft: `4px solid ${colors.primaryMain}`,
                        }}
                      >
                      <CardContent sx={{ p: 3 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                          <Chip
                            label={`#${hypothesis.rank}`}
                            color="primary"
                            size="small"
                            sx={{ fontWeight: 700 }}
                          />
                          <ConfidenceIndicator level={hypothesis.confidence} size="small" />
                        </Box>

                        <Typography variant="h6" gutterBottom fontWeight={700}>
                          {hypothesis.title}
                        </Typography>

                        <Typography variant="body1" paragraph color="text.secondary">
                          {hypothesis.rationale}
                        </Typography>

                        {hypothesis.implementation && (
                          <>
                            <Divider sx={{ my: 2 }} />
                            <Typography variant="body2" gutterBottom>
                              <strong>Implementation:</strong> {hypothesis.implementation}
                            </Typography>
                          </>
                        )}

                        {hypothesis.evidence.length > 0 && (
                          <>
                            <Divider sx={{ my: 2 }} />
                            <Typography variant="body2" gutterBottom fontWeight={600}>
                              Evidence:
                            </Typography>
                            <Box component="ul" sx={{ m: 0, pl: 3 }}>
                              {hypothesis.evidence.map((ev, i) => (
                                <li key={i}>
                                  <Typography variant="body2" color="text.secondary">
                                    {ev}
                                  </Typography>
                                </li>
                              ))}
                            </Box>
                          </>
                        )}
                      </CardContent>
                      </Card>
                    </motion.div>
                  ))}
                </Box>
              ) : (
                <Alert severity="info" icon={<InfoIcon />}>
                  <Typography>No recommendations generated for this analysis.</Typography>
                </Alert>
              )}
            </motion.div>
          </AnimatePresence>
        </TabPanel>

        {/* Tab 4: Drug Information */}
        <TabPanel value={tabValue} index={3}>
          <AnimatePresence mode="wait">
            <motion.div
              key="drugbank"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              {results.drugbank_data ? (
                <DrugBankInfo data={results.drugbank_data} />
              ) : (
                <Alert severity="info" icon={<InfoIcon />}>
                  <Typography>No DrugBank information available for this drug.</Typography>
                </Alert>
              )}
            </motion.div>
          </AnimatePresence>
        </TabPanel>
      </Paper>

      {/* Citations Footer */}
      <Paper elevation={1} sx={{ p: 3, borderRadius: 3, bgcolor: alpha(colors.primaryMain, 0.03) }}>
        <Typography variant="subtitle1" gutterBottom fontWeight={700}>
          Citations ({results.citations.length})
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 2 }}>
          {results.citations.slice(0, 20).map((citation, i) => {
            let url: string;
            let label: string;

            if (citation.startsWith('http://') || citation.startsWith('https://')) {
              url = citation;
              const match = citation.match(/NCT\d+/);
              label = match ? match[0] : citation.split('/').pop() || citation;
            } else if (citation.startsWith('PMID:')) {
              const pmid = citation.replace('PMID:', '');
              url = `https://pubmed.ncbi.nlm.nih.gov/${pmid}`;
              label = citation;
            } else {
              url = citation;
              label = citation;
            }

            return (
              <Chip
                key={i}
                label={label}
                size="small"
                component="a"
                href={url}
                target="_blank"
                clickable
                sx={{
                  '&:hover': {
                    bgcolor: alpha(colors.primaryMain, 0.15),
                    transform: 'translateY(-2px)',
                  },
                  transition: 'all 0.2s',
                }}
              />
            );
          })}
          {results.citations.length > 20 && (
            <Typography variant="caption" color="text.secondary">
              +{results.citations.length - 20} more
            </Typography>
          )}
        </Box>
      </Paper>
    </motion.div>
  );
}
