import { useState, useCallback } from 'react';
import {
  Box,
  Autocomplete,
  TextField,
  Button,
  Grid,
  Chip,
  Typography,
  Slider,
  alpha,
  Collapse,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Search as SearchIcon,
  Medication as MedicationIcon,
  LocalHospital as HospitalIcon,
  People as PeopleIcon,
  Article as ArticleIcon,
  Science as ScienceIcon,
  ExpandMore as ExpandMoreIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { apiClient } from '@/services/api';
import type { DrugQuery, AutocompleteOption } from '@/types';
import { debounce } from '@mui/material/utils';
import { colors } from '@/theme';

interface DrugSearchProps {
  onSearch: (query: DrugQuery) => void;
  isLoading: boolean;
}

export default function DrugSearch({ onSearch, isLoading }: DrugSearchProps) {
  const [drugInput, setDrugInput] = useState('');
  const [selectedDrug, setSelectedDrug] = useState<AutocompleteOption | null>(null);
  const [indication, setIndication] = useState('');
  const [population, setPopulation] = useState('all');
  const [articleCount, setArticleCount] = useState(5);
  const [clinicalTrialsCount, setClinicalTrialsCount] = useState(5);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Autocomplete query
  const { data: drugOptions = [], isLoading: isAutocompleteLoading } = useQuery({
    queryKey: ['autocomplete', drugInput],
    queryFn: () => apiClient.autocomplete(drugInput),
    enabled: drugInput.length >= 2,
    staleTime: 60000,
  });

  const handleDrugInputChange = useCallback(
    debounce((value: string) => {
      setDrugInput(value);
    }, 300),
    []
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const drugName = selectedDrug?.name || drugInput;

    if (!drugName) {
      return;
    }

    const query: DrugQuery = {
      drug: drugName,
      indication: indication || undefined,
      population: population || 'all',
      article_count: articleCount,
      clinical_trials_count: clinicalTrialsCount,
    };

    onSearch(query);
  };

  const populationOptions = [
    { value: 'all', label: 'All Populations', icon: '🌍' },
    { value: 'EUR', label: 'European', icon: '🇪🇺' },
    { value: 'EAS', label: 'East Asian', icon: '🌏' },
    { value: 'AFR', label: 'African', icon: '🌍' },
    { value: 'SAS', label: 'South Asian', icon: '🇮🇳' },
    { value: 'AMR', label: 'American', icon: '🌎' },
  ];

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <Grid container spacing={3}>
        {/* Drug Search */}
        <Grid item xs={12}>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4 }}
          >
            <Box
              sx={{
                p: 3,
                borderRadius: 2,
                border: `1px solid ${colors.divider}`,
                height: '100%',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 40,
                    height: 40,
                    borderRadius: 2,
                    bgcolor: alpha(colors.primaryMain, 0.1),
                    color: colors.primaryMain,
                  }}
                >
                  <MedicationIcon />
                </Box>
                <Typography variant="h6" fontWeight={600}>
                  Search Drug
                </Typography>
                <Tooltip title="Search by generic name, brand name, or mechanism of action">
                  <IconButton size="small">
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>

              <Autocomplete
                options={drugOptions}
                getOptionLabel={(option) =>
                  typeof option === 'string' ? option : option.name
                }
                renderOption={(props, option) => {
                  const { key, ...otherProps } = props;
                  return (
                    <Box component="li" key={key} {...otherProps} sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            width: 36,
                            height: 36,
                            borderRadius: 1.5,
                            bgcolor: alpha(colors.primaryMain, 0.1),
                            color: colors.primaryMain,
                          }}
                        >
                          <MedicationIcon fontSize="small" />
                        </Box>
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="body1" fontWeight={600}>
                            {option.name}
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                            <Chip
                              label={option.type}
                              size="small"
                              sx={{ height: 20, fontSize: '0.7rem' }}
                            />
                            <Typography variant="caption" color="text.secondary">
                              {option.description}
                            </Typography>
                          </Box>
                        </Box>
                      </Box>
                    </Box>
                  );
                }}
                loading={isAutocompleteLoading}
                onInputChange={(_, value) => {
                  handleDrugInputChange(value);
                }}
                onChange={(_, value) => {
                  if (typeof value === 'string') {
                    setSelectedDrug(null);
                  } else {
                    setSelectedDrug(value);
                  }
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Drug Name"
                    placeholder="Type a drug name (e.g., clopidogrel, Plavix, warfarin)"
                    required
                    InputProps={{
                      ...params.InputProps,
                      startAdornment: (
                        <>
                          <SearchIcon sx={{ color: 'text.secondary', ml: 1, mr: 0.5 }} />
                          {params.InputProps.startAdornment}
                        </>
                      ),
                    }}
                  />
                )}
                freeSolo
              />
            </Box>
          </motion.div>
        </Grid>

        {/* Indication and Population */}
        <Grid item xs={12} md={6}>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
          >
            <Box sx={{ p: 3, borderRadius: 2, border: `1px solid ${colors.divider}`, height: '100%' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 40,
                    height: 40,
                    borderRadius: 2,
                    bgcolor: alpha(colors.secondaryMain, 0.1),
                    color: colors.secondaryMain,
                  }}
                >
                  <HospitalIcon />
                </Box>
                <Typography variant="h6" fontWeight={600}>
                  Indication
                </Typography>
                <Chip label="Optional" size="small" variant="outlined" />
              </Box>

              <TextField
                fullWidth
                label="Disease/Condition"
                placeholder="e.g., acute coronary syndrome, stroke prevention"
                value={indication}
                onChange={(e) => setIndication(e.target.value)}
                helperText="Narrow analysis to specific indication"
              />
            </Box>
          </motion.div>
        </Grid>

        <Grid item xs={12} md={6}>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 0.15 }}
          >
            <Box sx={{ p: 3, borderRadius: 2, border: `1px solid ${colors.divider}`, height: '100%' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 40,
                    height: 40,
                    borderRadius: 2,
                    bgcolor: alpha(colors.secondaryMain, 0.1),
                    color: colors.secondaryMain,
                  }}
                >
                  <PeopleIcon />
                </Box>
                <Typography variant="h6" fontWeight={600}>
                  Population
                </Typography>
                <Chip label="Optional" size="small" variant="outlined" />
              </Box>

              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {populationOptions.map((pop) => (
                  <Chip
                    key={pop.value}
                    icon={<span style={{ fontSize: '1rem' }}>{pop.icon}</span>}
                    label={pop.label}
                    onClick={() => setPopulation(pop.value)}
                    color={population === pop.value ? 'primary' : 'default'}
                    variant={population === pop.value ? 'filled' : 'outlined'}
                    sx={{
                      fontWeight: population === pop.value ? 600 : 400,
                      transition: 'all 0.2s',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                      },
                    }}
                  />
                ))}
              </Box>
            </Box>
          </motion.div>
        </Grid>

        {/* Advanced Settings Toggle */}
        <Grid item xs={12}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
            }}
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            <Button
              variant="outlined"
              endIcon={
                <ExpandMoreIcon
                  sx={{
                    transform: showAdvanced ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 0.3s',
                  }}
                />
              }
            >
              {showAdvanced ? 'Hide' : 'Show'} Advanced Settings
            </Button>
          </Box>
        </Grid>

        {/* Advanced Settings */}
        <Grid item xs={12}>
          <Collapse in={showAdvanced}>
            <Grid container spacing={3}>
              {/* Article Count Slider */}
              <Grid item xs={12} md={6}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4 }}
                >
                  <Box sx={{ p: 3, borderRadius: 2, bgcolor: alpha(colors.infoMain, 0.05), border: `1px solid ${alpha(colors.infoMain, 0.2)}` }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <ArticleIcon sx={{ color: colors.infoMain }} />
                      <Typography variant="h6" fontWeight={600}>
                        PubMed Articles
                      </Typography>
                    </Box>
                    <Box sx={{ px: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Typography fontWeight={500}>
                          Articles to analyze:
                        </Typography>
                        <Chip label={articleCount} size="small" color="primary" />
                      </Box>
                      <Slider
                        value={articleCount}
                        onChange={(_, value) => setArticleCount(value as number)}
                        min={1}
                        max={20}
                        marks={[
                          { value: 1, label: '1' },
                          { value: 5, label: '5' },
                          { value: 10, label: '10' },
                          { value: 20, label: '20' },
                        ]}
                        valueLabelDisplay="auto"
                        disabled={isLoading}
                      />
                      <Typography variant="caption" color="text.secondary">
                        More articles = better data quality but longer analysis time
                      </Typography>
                    </Box>
                  </Box>
                </motion.div>
              </Grid>

              {/* Clinical Trials Count Slider */}
              <Grid item xs={12} md={6}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: 0.05 }}
                >
                  <Box sx={{ p: 3, borderRadius: 2, bgcolor: alpha(colors.infoMain, 0.05), border: `1px solid ${alpha(colors.infoMain, 0.2)}` }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <ScienceIcon sx={{ color: colors.infoMain }} />
                      <Typography variant="h6" fontWeight={600}>
                        Clinical Trials
                      </Typography>
                    </Box>
                    <Box sx={{ px: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Typography fontWeight={500}>
                          Trials to analyze:
                        </Typography>
                        <Chip label={clinicalTrialsCount} size="small" color="primary" />
                      </Box>
                      <Slider
                        value={clinicalTrialsCount}
                        onChange={(_, value) => setClinicalTrialsCount(value as number)}
                        min={1}
                        max={20}
                        marks={[
                          { value: 1, label: '1' },
                          { value: 5, label: '5' },
                          { value: 10, label: '10' },
                          { value: 20, label: '20' },
                        ]}
                        valueLabelDisplay="auto"
                        disabled={isLoading}
                      />
                      <Typography variant="caption" color="text.secondary">
                        More trials = better data quality but longer analysis time
                      </Typography>
                    </Box>
                  </Box>
                </motion.div>
              </Grid>
            </Grid>
          </Collapse>
        </Grid>

        {/* Submit Button */}
        <Grid item xs={12}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Button
              type="submit"
              variant="contained"
              size="large"
              fullWidth
              startIcon={<SearchIcon />}
              disabled={isLoading || !drugInput}
              sx={{
                py: 2,
                fontSize: '1.1rem',
                fontWeight: 700,
                borderRadius: 2,
                boxShadow: '0 8px 24px rgba(10, 122, 255, 0.3)',
                '&:hover': {
                  boxShadow: '0 12px 32px rgba(10, 122, 255, 0.4)',
                },
              }}
            >
              {isLoading ? 'Analyzing...' : 'Analyze Non-Response'}
            </Button>
          </motion.div>
        </Grid>
      </Grid>
    </Box>
  );
}
