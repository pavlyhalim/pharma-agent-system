/**
 * TypeScript types for the frontend.
 */

export interface DrugQuery {
  drug: string;
  indication?: string;
  population?: string;
  article_count?: number;
  clinical_trials_count?: number;
}

export interface ConfidenceInterval {
  lower: number;
  upper: number;
}

export interface NonResponseMetric {
  rate: number;
  ci: ConfidenceInterval;
  n: number;
  n_studies?: number;
  contributing_studies?: Array<{
    id: string;
    url?: string;
    n: number;
    rate: number;
  }>;
}

export interface SubgroupMetrics {
  overall: NonResponseMetric;
  by_subgroup: Record<string, NonResponseMetric>;
}

export interface Variant {
  rs_id: string;
  gene: string;
  allele?: string;
  effect: string;
  frequency: Record<string, number>;
  citations: string[];
}

export interface Hypothesis {
  rank: number;
  title: string;
  rationale: string;
  evidence: string[];
  confidence: 'high' | 'moderate' | 'low';
  implementation?: string;
}

export interface AnalysisMetadata {
  studies_analyzed: number;
  total_patients: number;
  data_quality: 'high' | 'moderate' | 'low' | 'insufficient';
  last_updated?: string;
  warnings?: string[];
}

export interface DrugBankSNPEffect {
  protein_name?: string;
  gene_symbol?: string;
  uniprot_id?: string;
  rs_id?: string;
  allele?: string;
  defining_change?: string;
  description?: string;
  pubmed_id?: string;
}

export interface DrugBankSNPAdverseReaction {
  protein_name?: string;
  gene_symbol?: string;
  uniprot_id?: string;
  rs_id?: string;
  allele?: string;
  adverse_reaction?: string;
  description?: string;
  pubmed_id?: string;
}

export interface DrugBankTarget {
  target_id?: string;
  target_name?: string;
  organism?: string;
  actions?: string;
  known_action?: string;
  gene_name?: string;
  uniprot_id?: string;
}

export interface DrugBankEnzyme {
  enzyme_id?: string;
  enzyme_name?: string;
  organism?: string;
  inhibition_strength?: string;
  induction_strength?: string;
  gene_name?: string;
  uniprot_id?: string;
}

export interface DrugBankInteraction {
  interacting_drugbank_id?: string;
  interacting_drug_name?: string;
  description?: string;
}

export interface DrugBankCategory {
  category?: string;
  mesh_id?: string;
}

export interface DrugBankDosage {
  form?: string;
  route?: string;
  strength?: string;
}

export interface DrugBankData {
  drugbank_id: string;
  name: string;
  description?: string;
  cas_number?: string;
  groups?: string;
  indication?: string;
  pharmacodynamics?: string;
  mechanism_of_action?: string;
  toxicity?: string;
  metabolism?: string;
  absorption?: string;
  half_life?: string;
  protein_binding?: string;
  route_of_elimination?: string;
  volume_of_distribution?: string;
  clearance?: string;
  pharmgkb_id?: string;
  synonyms?: string[];
  dosages?: DrugBankDosage[];
  snp_effects?: DrugBankSNPEffect[];
  snp_adverse_reactions?: DrugBankSNPAdverseReaction[];
  targets?: DrugBankTarget[];
  enzymes?: DrugBankEnzyme[];
  interactions?: DrugBankInteraction[];
  categories?: DrugBankCategory[];
}

export interface DrugAnalysisResult {
  drug: string;
  indication?: string;
  population: string;
  non_response_rate: SubgroupMetrics;
  variants: Variant[];
  hypotheses: Hypothesis[];
  drugbank_data?: DrugBankData | null;
  metadata: AnalysisMetadata;
  citations: string[];
}

export interface AutocompleteOption {
  name: string;
  type: 'generic' | 'brand' | 'mechanism';
  description?: string;
}
