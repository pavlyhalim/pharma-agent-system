"""
DrugBank XML Parser and SQLite Database Builder

Parses the DrugBank full database XML (1.5GB) and creates a fast SQLite database
for drug information, pharmacogenomics, and dosing data.
"""

import xml.etree.ElementTree as ET
import sqlite3
import logging
from pathlib import Path
from typing import Iterator, Dict, Any, List
import json

logger = logging.getLogger(__name__)


class DrugBankParser:
    """Parse DrugBank XML and build SQLite database."""

    NAMESPACE = "{http://www.drugbank.ca}"

    def __init__(self, xml_path: str, db_path: str):
        """
        Initialize parser.

        Args:
            xml_path: Path to DrugBank full database.xml
            db_path: Path to output SQLite database
        """
        self.xml_path = Path(xml_path)
        self.db_path = Path(db_path)

    def build_database(self):
        """Build complete SQLite database from DrugBank XML."""
        logger.info(f"Building DrugBank database from {self.xml_path}")

        # Create database schema
        conn = sqlite3.connect(self.db_path)
        self._create_schema(conn)

        # Parse XML and insert data (using streaming to handle 1.5GB file)
        drug_count = 0
        for drug_data in self._parse_drugs_streaming():
            self._insert_drug(conn, drug_data)
            drug_count += 1

            if drug_count % 100 == 0:
                logger.info(f"Processed {drug_count} drugs...")
                conn.commit()

        # Final commit and indexing
        conn.commit()
        self._create_indexes(conn)
        conn.close()

        logger.info(f"Database built successfully: {drug_count} drugs processed")

    def _create_schema(self, conn: sqlite3.Connection):
        """Create database schema."""
        cursor = conn.cursor()

        # Main drugs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS drugs (
            drugbank_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            cas_number TEXT,
            unii TEXT,
            indication TEXT,
            pharmacodynamics TEXT,
            mechanism_of_action TEXT,
            toxicity TEXT,
            metabolism TEXT,
            absorption TEXT,
            half_life TEXT,
            protein_binding TEXT,
            drug_type TEXT,
            state TEXT,
            groups TEXT,
            pharmgkb_id TEXT
        )
        """)

        # Synonyms/brand names
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS drug_synonyms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drugbank_id TEXT NOT NULL,
            synonym TEXT NOT NULL,
            language TEXT,
            FOREIGN KEY (drugbank_id) REFERENCES drugs(drugbank_id)
        )
        """)

        # Dosages
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS drug_dosages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drugbank_id TEXT NOT NULL,
            form TEXT,
            route TEXT,
            strength TEXT,
            FOREIGN KEY (drugbank_id) REFERENCES drugs(drugbank_id)
        )
        """)

        # SNP effects (PHARMACOGENOMICS)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS snp_effects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drugbank_id TEXT NOT NULL,
            protein_name TEXT,
            gene_symbol TEXT,
            uniprot_id TEXT,
            rs_id TEXT,
            allele TEXT,
            defining_change TEXT,
            description TEXT,
            pubmed_id TEXT,
            FOREIGN KEY (drugbank_id) REFERENCES drugs(drugbank_id)
        )
        """)

        # SNP adverse reactions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS snp_adverse_reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drugbank_id TEXT NOT NULL,
            protein_name TEXT,
            gene_symbol TEXT,
            uniprot_id TEXT,
            rs_id TEXT,
            allele TEXT,
            adverse_reaction TEXT,
            description TEXT,
            pubmed_id TEXT,
            FOREIGN KEY (drugbank_id) REFERENCES drugs(drugbank_id)
        )
        """)

        # Drug targets (enzymes involved in drug action)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS drug_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drugbank_id TEXT NOT NULL,
            target_id TEXT,
            target_name TEXT,
            organism TEXT,
            actions TEXT,
            known_action TEXT,
            gene_name TEXT,
            uniprot_id TEXT,
            FOREIGN KEY (drugbank_id) REFERENCES drugs(drugbank_id)
        )
        """)

        # Enzymes (metabolism)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS drug_enzymes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drugbank_id TEXT NOT NULL,
            enzyme_id TEXT,
            enzyme_name TEXT,
            organism TEXT,
            inhibition_strength TEXT,
            induction_strength TEXT,
            gene_name TEXT,
            uniprot_id TEXT,
            FOREIGN KEY (drugbank_id) REFERENCES drugs(drugbank_id)
        )
        """)

        # Drug interactions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS drug_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drugbank_id TEXT NOT NULL,
            interacting_drugbank_id TEXT,
            interacting_drug_name TEXT,
            description TEXT,
            FOREIGN KEY (drugbank_id) REFERENCES drugs(drugbank_id)
        )
        """)

        # Categories
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS drug_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drugbank_id TEXT NOT NULL,
            category TEXT,
            mesh_id TEXT,
            FOREIGN KEY (drugbank_id) REFERENCES drugs(drugbank_id)
        )
        """)

        conn.commit()

    def _create_indexes(self, conn: sqlite3.Connection):
        """Create indexes for fast queries."""
        cursor = conn.cursor()

        logger.info("Creating database indexes...")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_drugs_name ON drugs(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_drugs_pharmgkb ON drugs(pharmgkb_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_synonyms_name ON drug_synonyms(synonym)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_synonyms_drug ON drug_synonyms(drugbank_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snp_gene ON snp_effects(gene_symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snp_rs ON snp_effects(rs_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snp_drug ON snp_effects(drugbank_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_targets_gene ON drug_targets(gene_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_enzymes_gene ON drug_enzymes(gene_name)")

        conn.commit()

    def _parse_drugs_streaming(self) -> Iterator[Dict[str, Any]]:
        """
        Stream-parse DrugBank XML to avoid loading 1.5GB into memory.

        Yields:
            Drug data dictionaries
        """
        # Use iterparse for memory-efficient streaming
        context = ET.iterparse(self.xml_path, events=("start", "end"))
        context = iter(context)
        event, root = next(context)

        for event, elem in context:
            if event == "end" and elem.tag == f"{self.NAMESPACE}drug":
                # Parse this drug entry
                drug_data = self._parse_drug_element(elem)
                yield drug_data

                # Clear element to free memory
                elem.clear()
                root.clear()

    def _parse_drug_element(self, drug_elem) -> Dict[str, Any]:
        """Parse a single drug XML element."""
        ns = self.NAMESPACE

        # Extract primary drugbank ID
        drugbank_ids = drug_elem.findall(f"{ns}drugbank-id")
        primary_id = None
        for db_id in drugbank_ids:
            if db_id.get("primary") == "true":
                primary_id = db_id.text
                break
        if not primary_id and drugbank_ids:
            primary_id = drugbank_ids[0].text

        # Basic drug info
        drug_data = {
            "drugbank_id": primary_id,
            "name": self._get_text(drug_elem, f"{ns}name"),
            "description": self._get_text(drug_elem, f"{ns}description"),
            "cas_number": self._get_text(drug_elem, f"{ns}cas-number"),
            "unii": self._get_text(drug_elem, f"{ns}unii"),
            "indication": self._get_text(drug_elem, f"{ns}indication"),
            "pharmacodynamics": self._get_text(drug_elem, f"{ns}pharmacodynamics"),
            "mechanism_of_action": self._get_text(drug_elem, f"{ns}mechanism-of-action"),
            "toxicity": self._get_text(drug_elem, f"{ns}toxicity"),
            "metabolism": self._get_text(drug_elem, f"{ns}metabolism"),
            "absorption": self._get_text(drug_elem, f"{ns}absorption"),
            "half_life": self._get_text(drug_elem, f"{ns}half-life"),
            "protein_binding": self._get_text(drug_elem, f"{ns}protein-binding"),
            "drug_type": drug_elem.get("type"),
            "state": self._get_text(drug_elem, f"{ns}state"),
            "groups": self._get_groups(drug_elem, ns),
            "pharmgkb_id": self._get_pharmgkb_id(drug_elem, ns),
            "synonyms": self._get_synonyms(drug_elem, ns),
            "dosages": self._get_dosages(drug_elem, ns),
            "snp_effects": self._get_snp_effects(drug_elem, ns),
            "snp_adverse_reactions": self._get_snp_adverse_reactions(drug_elem, ns),
            "targets": self._get_targets(drug_elem, ns),
            "enzymes": self._get_enzymes(drug_elem, ns),
            "interactions": self._get_interactions(drug_elem, ns),
            "categories": self._get_categories(drug_elem, ns)
        }

        return drug_data

    def _get_text(self, elem, path: str) -> str:
        """Safely extract text from XML element."""
        child = elem.find(path)
        return child.text if child is not None and child.text else ""

    def _get_groups(self, elem, ns: str) -> str:
        """Extract drug approval groups (approved, experimental, etc.)."""
        groups_elem = elem.find(f"{ns}groups")
        if groups_elem is None:
            return ""
        groups = [g.text for g in groups_elem.findall(f"{ns}group") if g.text]
        return ",".join(groups)

    def _get_pharmgkb_id(self, elem, ns: str) -> str:
        """Extract PharmGKB ID from external identifiers."""
        ext_ids = elem.find(f"{ns}external-identifiers")
        if ext_ids is None:
            return ""

        for ext_id in ext_ids.findall(f"{ns}external-identifier"):
            resource = self._get_text(ext_id, f"{ns}resource")
            if resource == "PharmGKB":
                return self._get_text(ext_id, f"{ns}identifier")
        return ""

    def _get_synonyms(self, elem, ns: str) -> List[Dict[str, str]]:
        """Extract drug synonyms/brand names."""
        synonyms_elem = elem.find(f"{ns}synonyms")
        if synonyms_elem is None:
            return []

        synonyms = []
        for syn in synonyms_elem.findall(f"{ns}synonym"):
            if syn.text:
                synonyms.append({
                    "synonym": syn.text,
                    "language": syn.get("language", "")
                })
        return synonyms

    def _get_dosages(self, elem, ns: str) -> List[Dict[str, str]]:
        """Extract dosage information."""
        dosages_elem = elem.find(f"{ns}dosages")
        if dosages_elem is None:
            return []

        dosages = []
        for dosage in dosages_elem.findall(f"{ns}dosage"):
            dosages.append({
                "form": self._get_text(dosage, f"{ns}form"),
                "route": self._get_text(dosage, f"{ns}route"),
                "strength": self._get_text(dosage, f"{ns}strength")
            })
        return dosages

    def _get_snp_effects(self, elem, ns: str) -> List[Dict[str, str]]:
        """Extract SNP pharmacogenomic effects."""
        snp_effects_elem = elem.find(f"{ns}snp-effects")
        if snp_effects_elem is None:
            return []

        effects = []
        for effect in snp_effects_elem.findall(f"{ns}effect"):
            effects.append({
                "protein_name": self._get_text(effect, f"{ns}protein-name"),
                "gene_symbol": self._get_text(effect, f"{ns}gene-symbol"),
                "uniprot_id": self._get_text(effect, f"{ns}uniprot-id"),
                "rs_id": self._get_text(effect, f"{ns}rs-id"),
                "allele": self._get_text(effect, f"{ns}allele"),
                "defining_change": self._get_text(effect, f"{ns}defining-change"),
                "description": self._get_text(effect, f"{ns}description"),
                "pubmed_id": self._get_text(effect, f"{ns}pubmed-id")
            })
        return effects

    def _get_snp_adverse_reactions(self, elem, ns: str) -> List[Dict[str, str]]:
        """Extract SNP adverse drug reactions."""
        snp_adr_elem = elem.find(f"{ns}snp-adverse-drug-reactions")
        if snp_adr_elem is None:
            return []

        reactions = []
        for reaction in snp_adr_elem.findall(f"{ns}reaction"):
            reactions.append({
                "protein_name": self._get_text(reaction, f"{ns}protein-name"),
                "gene_symbol": self._get_text(reaction, f"{ns}gene-symbol"),
                "uniprot_id": self._get_text(reaction, f"{ns}uniprot-id"),
                "rs_id": self._get_text(reaction, f"{ns}rs-id"),
                "allele": self._get_text(reaction, f"{ns}allele"),
                "adverse_reaction": self._get_text(reaction, f"{ns}adverse-reaction"),
                "description": self._get_text(reaction, f"{ns}description"),
                "pubmed_id": self._get_text(reaction, f"{ns}pubmed-id")
            })
        return reactions

    def _get_targets(self, elem, ns: str) -> List[Dict[str, str]]:
        """Extract drug targets."""
        targets_elem = elem.find(f"{ns}targets")
        if targets_elem is None:
            return []

        targets = []
        for target in targets_elem.findall(f"{ns}target"):
            # Extract polypeptide info
            polypeptides = target.findall(f"{ns}polypeptide")
            gene_name = ""
            uniprot_id = ""
            if polypeptides:
                poly = polypeptides[0]
                gene_name = self._get_text(poly, f"{ns}gene-name")
                uniprot_id = poly.get("id", "")

            actions_elem = target.find(f"{ns}actions")
            actions = []
            if actions_elem is not None:
                actions = [a.text for a in actions_elem.findall(f"{ns}action") if a.text]

            targets.append({
                "target_id": self._get_text(target, f"{ns}id"),
                "target_name": self._get_text(target, f"{ns}name"),
                "organism": self._get_text(target, f"{ns}organism"),
                "actions": ",".join(actions),
                "known_action": self._get_text(target, f"{ns}known-action"),
                "gene_name": gene_name,
                "uniprot_id": uniprot_id
            })
        return targets

    def _get_enzymes(self, elem, ns: str) -> List[Dict[str, str]]:
        """Extract drug metabolizing enzymes."""
        enzymes_elem = elem.find(f"{ns}enzymes")
        if enzymes_elem is None:
            return []

        enzymes = []
        for enzyme in enzymes_elem.findall(f"{ns}enzyme"):
            # Extract polypeptide info
            polypeptides = enzyme.findall(f"{ns}polypeptide")
            gene_name = ""
            uniprot_id = ""
            if polypeptides:
                poly = polypeptides[0]
                gene_name = self._get_text(poly, f"{ns}gene-name")
                uniprot_id = poly.get("id", "")

            enzymes.append({
                "enzyme_id": self._get_text(enzyme, f"{ns}id"),
                "enzyme_name": self._get_text(enzyme, f"{ns}name"),
                "organism": self._get_text(enzyme, f"{ns}organism"),
                "inhibition_strength": self._get_text(enzyme, f"{ns}inhibition-strength"),
                "induction_strength": self._get_text(enzyme, f"{ns}induction-strength"),
                "gene_name": gene_name,
                "uniprot_id": uniprot_id
            })
        return enzymes

    def _get_interactions(self, elem, ns: str) -> List[Dict[str, str]]:
        """Extract drug-drug interactions."""
        interactions_elem = elem.find(f"{ns}drug-interactions")
        if interactions_elem is None:
            return []

        interactions = []
        for interaction in interactions_elem.findall(f"{ns}drug-interaction"):
            interactions.append({
                "interacting_drugbank_id": self._get_text(interaction, f"{ns}drugbank-id"),
                "interacting_drug_name": self._get_text(interaction, f"{ns}name"),
                "description": self._get_text(interaction, f"{ns}description")
            })
        return interactions

    def _get_categories(self, elem, ns: str) -> List[Dict[str, str]]:
        """Extract drug categories."""
        categories_elem = elem.find(f"{ns}categories")
        if categories_elem is None:
            return []

        categories = []
        for category in categories_elem.findall(f"{ns}category"):
            categories.append({
                "category": self._get_text(category, f"{ns}category"),
                "mesh_id": self._get_text(category, f"{ns}mesh-id")
            })
        return categories

    def _insert_drug(self, conn: sqlite3.Connection, drug_data: Dict[str, Any]):
        """Insert drug data into database."""
        cursor = conn.cursor()

        # Insert main drug record
        cursor.execute("""
        INSERT OR REPLACE INTO drugs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            drug_data["drugbank_id"],
            drug_data["name"],
            drug_data["description"],
            drug_data["cas_number"],
            drug_data["unii"],
            drug_data["indication"],
            drug_data["pharmacodynamics"],
            drug_data["mechanism_of_action"],
            drug_data["toxicity"],
            drug_data["metabolism"],
            drug_data["absorption"],
            drug_data["half_life"],
            drug_data["protein_binding"],
            drug_data["drug_type"],
            drug_data["state"],
            drug_data["groups"],
            drug_data["pharmgkb_id"]
        ))

        # Insert synonyms
        for syn in drug_data.get("synonyms", []):
            cursor.execute("""
            INSERT INTO drug_synonyms (drugbank_id, synonym, language) VALUES (?, ?, ?)
            """, (drug_data["drugbank_id"], syn["synonym"], syn["language"]))

        # Insert dosages
        for dosage in drug_data.get("dosages", []):
            cursor.execute("""
            INSERT INTO drug_dosages (drugbank_id, form, route, strength) VALUES (?, ?, ?, ?)
            """, (drug_data["drugbank_id"], dosage["form"], dosage["route"], dosage["strength"]))

        # Insert SNP effects
        for effect in drug_data.get("snp_effects", []):
            cursor.execute("""
            INSERT INTO snp_effects (drugbank_id, protein_name, gene_symbol, uniprot_id, rs_id, allele, defining_change, description, pubmed_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                drug_data["drugbank_id"],
                effect["protein_name"],
                effect["gene_symbol"],
                effect["uniprot_id"],
                effect["rs_id"],
                effect["allele"],
                effect["defining_change"],
                effect["description"],
                effect["pubmed_id"]
            ))

        # Insert SNP adverse reactions
        for reaction in drug_data.get("snp_adverse_reactions", []):
            cursor.execute("""
            INSERT INTO snp_adverse_reactions (drugbank_id, protein_name, gene_symbol, uniprot_id, rs_id, allele, adverse_reaction, description, pubmed_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                drug_data["drugbank_id"],
                reaction["protein_name"],
                reaction["gene_symbol"],
                reaction["uniprot_id"],
                reaction["rs_id"],
                reaction["allele"],
                reaction["adverse_reaction"],
                reaction["description"],
                reaction["pubmed_id"]
            ))

        # Insert targets
        for target in drug_data.get("targets", []):
            cursor.execute("""
            INSERT INTO drug_targets (drugbank_id, target_id, target_name, organism, actions, known_action, gene_name, uniprot_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                drug_data["drugbank_id"],
                target["target_id"],
                target["target_name"],
                target["organism"],
                target["actions"],
                target["known_action"],
                target["gene_name"],
                target["uniprot_id"]
            ))

        # Insert enzymes
        for enzyme in drug_data.get("enzymes", []):
            cursor.execute("""
            INSERT INTO drug_enzymes (drugbank_id, enzyme_id, enzyme_name, organism, inhibition_strength, induction_strength, gene_name, uniprot_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                drug_data["drugbank_id"],
                enzyme["enzyme_id"],
                enzyme["enzyme_name"],
                enzyme["organism"],
                enzyme["inhibition_strength"],
                enzyme["induction_strength"],
                enzyme["gene_name"],
                enzyme["uniprot_id"]
            ))

        # Insert interactions
        for interaction in drug_data.get("interactions", []):
            cursor.execute("""
            INSERT INTO drug_interactions (drugbank_id, interacting_drugbank_id, interacting_drug_name, description)
            VALUES (?, ?, ?, ?)
            """, (
                drug_data["drugbank_id"],
                interaction["interacting_drugbank_id"],
                interaction["interacting_drug_name"],
                interaction["description"]
            ))

        # Insert categories
        for category in drug_data.get("categories", []):
            cursor.execute("""
            INSERT INTO drug_categories (drugbank_id, category, mesh_id)
            VALUES (?, ?, ?)
            """, (drug_data["drugbank_id"], category["category"], category["mesh_id"]))


if __name__ == "__main__":
    # Command-line usage
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    if len(sys.argv) < 3:
        print("Usage: python drugbank_parser.py <xml_path> <db_path>")
        sys.exit(1)

    xml_path = sys.argv[1]
    db_path = sys.argv[2]

    parser = DrugBankParser(xml_path, db_path)
    parser.build_database()
