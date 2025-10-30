import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Divider,
  Link,
  alpha,
} from '@mui/material';
import {
  Info as InfoIcon,
  Science as ScienceIcon,
  LocalPharmacy as PharmacyIcon,
  Biotech as BiotechIcon,
  Warning as WarningIcon,
  MedicalServices as MedicalServicesIcon,
} from '@mui/icons-material';
import { useState } from 'react';
import type { DrugBankData } from '@/types';
import { colors } from '@/theme';

interface DrugBankInfoProps {
  data: DrugBankData;
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
      id={`drugbank-tabpanel-${index}`}
      aria-labelledby={`drugbank-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function DrugBankInfo({ data }: DrugBankInfoProps) {
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Paper elevation={2} sx={{ p: 0 }}>
      <Box sx={{
        p: 3,
        pb: 2,
        bgcolor: colors.primaryAccessibleBg,
        color: colors.textPrimary,
        border: `2px solid ${colors.primaryMain}`,
        borderBottom: 'none'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <MedicalServicesIcon sx={{ color: colors.primaryMain }} />
          <Typography variant="h5" fontWeight={700}>DrugBank Information</Typography>
        </Box>
        <Typography variant="body2" sx={{ mt: 1, color: colors.textSecondary }}>
          Comprehensive drug data from DrugBank v5.1 database
        </Typography>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          aria-label="drugbank info tabs"
        >
          <Tab label="Overview" icon={<InfoIcon />} iconPosition="start" />
          <Tab label="Pharmacology" icon={<ScienceIcon />} iconPosition="start" />
          <Tab label="Dosages" icon={<PharmacyIcon />} iconPosition="start" />
          <Tab label="Targets & Enzymes" icon={<BiotechIcon />} iconPosition="start" />
          <Tab label="Pharmacogenomics" icon={<BiotechIcon />} iconPosition="start" />
          <Tab label="Interactions" icon={<WarningIcon />} iconPosition="start" />
        </Tabs>
      </Box>

      {/* Tab 0: Overview */}
      <TabPanel value={tabValue} index={0}>
        <Typography variant="h6" gutterBottom>
          Basic Information
        </Typography>

        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            <strong>DrugBank ID:</strong> {data.drugbank_id}
          </Typography>
          {data.cas_number && (
            <Typography variant="body2" color="text.secondary">
              <strong>CAS Number:</strong> {data.cas_number}
            </Typography>
          )}
          {data.groups && (
            <Typography variant="body2" color="text.secondary">
              <strong>Groups:</strong> {data.groups}
            </Typography>
          )}
          {data.pharmgkb_id && (
            <Typography variant="body2" color="text.secondary">
              <strong>PharmGKB ID:</strong>{' '}
              <Link href={`https://www.pharmgkb.org/chemical/${data.pharmgkb_id}`} target="_blank">
                {data.pharmgkb_id}
              </Link>
            </Typography>
          )}
        </Box>

        {data.synonyms && data.synonyms.length > 0 && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="h6" gutterBottom>
              Synonyms
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {data.synonyms.slice(0, 15).map((synonym, idx) => (
                <Chip key={idx} label={synonym} size="small" variant="outlined" />
              ))}
              {data.synonyms.length > 15 && (
                <Typography variant="caption" color="text.secondary">
                  +{data.synonyms.length - 15} more
                </Typography>
              )}
            </Box>
          </>
        )}

        {data.description && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="h6" gutterBottom>
              Description
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {data.description}
            </Typography>
          </>
        )}

        {data.indication && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="h6" gutterBottom>
              Indication
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {data.indication}
            </Typography>
          </>
        )}

        {data.categories && data.categories.length > 0 && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="h6" gutterBottom>
              Categories
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {data.categories.map((cat, idx) => (
                <Chip key={idx} label={cat.category} size="small" color="primary" variant="outlined" />
              ))}
            </Box>
          </>
        )}
      </TabPanel>

      {/* Tab 1: Pharmacology */}
      <TabPanel value={tabValue} index={1}>
        {data.mechanism_of_action && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Mechanism of Action
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {data.mechanism_of_action}
            </Typography>
          </Box>
        )}

        {data.pharmacodynamics && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Pharmacodynamics
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {data.pharmacodynamics}
            </Typography>
          </Box>
        )}

        {data.absorption && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Absorption
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {data.absorption}
            </Typography>
          </Box>
        )}

        {data.metabolism && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Metabolism
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {data.metabolism}
            </Typography>
          </Box>
        )}

        {data.half_life && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Half-Life
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {data.half_life}
            </Typography>
          </Box>
        )}

        {data.protein_binding && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Protein Binding
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {data.protein_binding}
            </Typography>
          </Box>
        )}

        {data.volume_of_distribution && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Volume of Distribution
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {data.volume_of_distribution}
            </Typography>
          </Box>
        )}

        {data.clearance && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Clearance
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {data.clearance}
            </Typography>
          </Box>
        )}

        {data.route_of_elimination && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Route of Elimination
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {data.route_of_elimination}
            </Typography>
          </Box>
        )}

        {data.toxicity && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Toxicity
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {data.toxicity}
            </Typography>
          </Box>
        )}
      </TabPanel>

      {/* Tab 2: Dosages */}
      <TabPanel value={tabValue} index={2}>
        {data.dosages && data.dosages.length > 0 ? (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Form</strong></TableCell>
                  <TableCell><strong>Route</strong></TableCell>
                  <TableCell><strong>Strength</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.dosages.map((dosage, idx) => (
                  <TableRow key={idx}>
                    <TableCell>{dosage.form || '-'}</TableCell>
                    <TableCell>{dosage.route || '-'}</TableCell>
                    <TableCell>{dosage.strength || '-'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Typography color="text.secondary">No dosage information available.</Typography>
        )}
      </TabPanel>

      {/* Tab 3: Targets & Enzymes */}
      <TabPanel value={tabValue} index={3}>
        {data.targets && data.targets.length > 0 && (
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              Drug Targets
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Target Name</strong></TableCell>
                    <TableCell><strong>Gene</strong></TableCell>
                    <TableCell><strong>Actions</strong></TableCell>
                    <TableCell><strong>Organism</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.targets.map((target, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{target.target_name || '-'}</TableCell>
                      <TableCell>
                        {target.gene_name ? (
                          <Chip label={target.gene_name} size="small" />
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell>{target.actions || '-'}</TableCell>
                      <TableCell>{target.organism || '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {data.enzymes && data.enzymes.length > 0 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Metabolizing Enzymes
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Enzyme Name</strong></TableCell>
                    <TableCell><strong>Gene</strong></TableCell>
                    <TableCell><strong>Inhibition</strong></TableCell>
                    <TableCell><strong>Induction</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.enzymes.map((enzyme, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{enzyme.enzyme_name || '-'}</TableCell>
                      <TableCell>
                        {enzyme.gene_name ? (
                          <Chip label={enzyme.gene_name} size="small" color="secondary" />
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell>{enzyme.inhibition_strength || '-'}</TableCell>
                      <TableCell>{enzyme.induction_strength || '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {(!data.targets || data.targets.length === 0) &&
          (!data.enzymes || data.enzymes.length === 0) && (
            <Typography color="text.secondary">
              No target or enzyme information available.
            </Typography>
          )}
      </TabPanel>

      {/* Tab 4: Pharmacogenomics */}
      <TabPanel value={tabValue} index={4}>
        {data.snp_effects && data.snp_effects.length > 0 && (
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              SNP Effects on Drug Response
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Gene</strong></TableCell>
                    <TableCell><strong>rsID</strong></TableCell>
                    <TableCell><strong>Allele</strong></TableCell>
                    <TableCell><strong>Effect</strong></TableCell>
                    <TableCell><strong>PubMed</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.snp_effects.map((snp, idx) => (
                    <TableRow key={idx}>
                      <TableCell>
                        <Chip label={snp.gene_symbol || '-'} size="small" color="primary" />
                      </TableCell>
                      <TableCell>
                        {snp.rs_id ? (
                          <Link
                            href={`https://www.ncbi.nlm.nih.gov/snp/${snp.rs_id}`}
                            target="_blank"
                          >
                            {snp.rs_id}
                          </Link>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell>{snp.allele || '-'}</TableCell>
                      <TableCell>{snp.description || '-'}</TableCell>
                      <TableCell>
                        {snp.pubmed_id ? (
                          <Link
                            href={`https://pubmed.ncbi.nlm.nih.gov/${snp.pubmed_id}`}
                            target="_blank"
                          >
                            {snp.pubmed_id}
                          </Link>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {data.snp_adverse_reactions && data.snp_adverse_reactions.length > 0 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              SNP-Associated Adverse Reactions
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Gene</strong></TableCell>
                    <TableCell><strong>rsID</strong></TableCell>
                    <TableCell><strong>Allele</strong></TableCell>
                    <TableCell><strong>Adverse Reaction</strong></TableCell>
                    <TableCell><strong>PubMed</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.snp_adverse_reactions.map((snp, idx) => (
                    <TableRow key={idx}>
                      <TableCell>
                        <Chip label={snp.gene_symbol || '-'} size="small" color="error" />
                      </TableCell>
                      <TableCell>
                        {snp.rs_id ? (
                          <Link
                            href={`https://www.ncbi.nlm.nih.gov/snp/${snp.rs_id}`}
                            target="_blank"
                          >
                            {snp.rs_id}
                          </Link>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell>{snp.allele || '-'}</TableCell>
                      <TableCell>{snp.adverse_reaction || snp.description || '-'}</TableCell>
                      <TableCell>
                        {snp.pubmed_id ? (
                          <Link
                            href={`https://pubmed.ncbi.nlm.nih.gov/${snp.pubmed_id}`}
                            target="_blank"
                          >
                            {snp.pubmed_id}
                          </Link>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {(!data.snp_effects || data.snp_effects.length === 0) &&
          (!data.snp_adverse_reactions || data.snp_adverse_reactions.length === 0) && (
            <Typography color="text.secondary">
              No pharmacogenomic data available.
            </Typography>
          )}
      </TabPanel>

      {/* Tab 5: Interactions */}
      <TabPanel value={tabValue} index={5}>
        {data.interactions && data.interactions.length > 0 ? (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {data.interactions.length} known drug-drug interactions
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Interacting Drug</strong></TableCell>
                    <TableCell><strong>Description</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.interactions.slice(0, 50).map((interaction, idx) => (
                    <TableRow key={idx}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {interaction.interacting_drug_name || '-'}
                        </Typography>
                        {interaction.interacting_drugbank_id && (
                          <Typography variant="caption" color="text.secondary">
                            {interaction.interacting_drugbank_id}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>{interaction.description || '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            {data.interactions.length > 50 && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                Showing 50 of {data.interactions.length} interactions
              </Typography>
            )}
          </>
        ) : (
          <Typography color="text.secondary">No drug interaction data available.</Typography>
        )}
      </TabPanel>
    </Paper>
  );
}
