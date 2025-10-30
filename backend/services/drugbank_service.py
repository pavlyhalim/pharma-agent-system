"""
DrugBank SQLite Service

Fast queries against local DrugBank database for drug information,
pharmacogenomics (SNPs), dosing, and drug interactions.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DrugBankService:
    """Service for querying DrugBank SQLite database."""

    def __init__(self, db_path: str = None):
        """
        Initialize DrugBank service.

        Args:
            db_path: Path to DrugBank SQLite database
        """
        if db_path is None:
            # Default path relative to backend directory
            backend_dir = Path(__file__).parent.parent
            db_path = backend_dir.parent / "db" / "drugbank.db"

        self.db_path = Path(db_path)

        if not self.db_path.exists():
            raise FileNotFoundError(
                f"DrugBank database not found at {self.db_path}. "
                f"Run drugbank_parser.py to build the database first."
            )

        logger.info(f"DrugBank service initialized with database: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn

    def search_drugs(
        self,
        query: str,
        limit: int = 20,
        approved_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for drugs by name or synonym.

        Args:
            query: Drug name or partial name
            limit: Maximum results
            approved_only: Only return approved drugs

        Returns:
            List of drug dictionaries with name, drugbank_id, description
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query_lower = query.lower()

        # Search in both drug names and synonyms
        sql = """
        SELECT DISTINCT
            d.drugbank_id,
            d.name,
            d.description,
            d.indication,
            d.groups,
            d.pharmgkb_id
        FROM drugs d
        LEFT JOIN drug_synonyms s ON d.drugbank_id = s.drugbank_id
        WHERE (LOWER(d.name) LIKE ? OR LOWER(s.synonym) LIKE ?)
        """

        params = [f"%{query_lower}%", f"%{query_lower}%"]

        if approved_only:
            sql += " AND d.groups LIKE '%approved%'"

        sql += " ORDER BY d.name LIMIT ?"
        params.append(limit)

        results = cursor.execute(sql, params).fetchall()

        drugs = []
        for row in results:
            drugs.append({
                "drugbank_id": row["drugbank_id"],
                "name": row["name"],
                "description": row["description"][:200] if row["description"] else "",
                "indication": row["indication"][:200] if row["indication"] else "",
                "groups": row["groups"],
                "pharmgkb_id": row["pharmgkb_id"]
            })

        conn.close()
        logger.info(f"Found {len(drugs)} drugs matching '{query}'")
        return drugs

    def get_drug_by_id(self, drugbank_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete drug information by DrugBank ID.

        Args:
            drugbank_id: DrugBank ID (e.g., DB00758)

        Returns:
            Complete drug information dictionary
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        drug_row = cursor.execute(
            "SELECT * FROM drugs WHERE drugbank_id = ?",
            (drugbank_id,)
        ).fetchone()

        if not drug_row:
            conn.close()
            return None

        # Convert row to dict
        drug = dict(drug_row)

        # Add related data
        drug["synonyms"] = self._get_drug_synonyms(cursor, drugbank_id)
        drug["dosages"] = self._get_drug_dosages(cursor, drugbank_id)
        drug["snp_effects"] = self._get_drug_snp_effects(cursor, drugbank_id)
        drug["snp_adverse_reactions"] = self._get_drug_snp_adverse_reactions(cursor, drugbank_id)
        drug["targets"] = self._get_drug_targets(cursor, drugbank_id)
        drug["enzymes"] = self._get_drug_enzymes(cursor, drugbank_id)
        drug["interactions"] = self._get_drug_interactions(cursor, drugbank_id)
        drug["categories"] = self._get_drug_categories(cursor, drugbank_id)

        conn.close()
        logger.info(f"Retrieved complete data for {drug['name']} ({drugbank_id})")
        return drug

    def get_drug_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get complete drug information by name (searches synonyms too).

        Args:
            name: Drug name

        Returns:
            Complete drug information dictionary
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Try exact match first
        drug_row = cursor.execute(
            "SELECT drugbank_id FROM drugs WHERE LOWER(name) = ?",
            (name.lower(),)
        ).fetchone()

        if not drug_row:
            # Try synonym match
            drug_row = cursor.execute("""
                SELECT d.drugbank_id FROM drugs d
                JOIN drug_synonyms s ON d.drugbank_id = s.drugbank_id
                WHERE LOWER(s.synonym) = ?
                LIMIT 1
            """, (name.lower(),)).fetchone()

        conn.close()

        if drug_row:
            return self.get_drug_by_id(drug_row["drugbank_id"])
        return None

    def get_snp_effects(
        self,
        drug: str = None,
        gene: str = None,
        rs_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get SNP pharmacogenomic effects.

        Args:
            drug: Drug name or DrugBank ID
            gene: Gene symbol (e.g., CYP2C19)
            rs_id: dbSNP rs ID (e.g., rs4244285)

        Returns:
            List of SNP effect dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        sql = """
        SELECT
            s.*,
            d.name as drug_name,
            d.drugbank_id
        FROM snp_effects s
        JOIN drugs d ON s.drugbank_id = d.drugbank_id
        WHERE 1=1
        """
        params = []

        if drug:
            # Check if it's a DrugBank ID or name
            if drug.startswith("DB"):
                sql += " AND s.drugbank_id = ?"
                params.append(drug)
            else:
                # Search by drug name or synonym
                drugbank_ids = cursor.execute("""
                    SELECT DISTINCT d.drugbank_id FROM drugs d
                    LEFT JOIN drug_synonyms syn ON d.drugbank_id = syn.drugbank_id
                    WHERE LOWER(d.name) LIKE ? OR LOWER(syn.synonym) LIKE ?
                """, (f"%{drug.lower()}%", f"%{drug.lower()}%")).fetchall()

                if drugbank_ids:
                    ids = [row["drugbank_id"] for row in drugbank_ids]
                    placeholders = ",".join("?" * len(ids))
                    sql += f" AND s.drugbank_id IN ({placeholders})"
                    params.extend(ids)

        if gene:
            sql += " AND LOWER(s.gene_symbol) = ?"
            params.append(gene.lower())

        if rs_id:
            sql += " AND s.rs_id = ?"
            params.append(rs_id)

        results = cursor.execute(sql, params).fetchall()

        snp_effects = [dict(row) for row in results]
        conn.close()

        logger.info(f"Found {len(snp_effects)} SNP effects for drug={drug}, gene={gene}, rs_id={rs_id}")
        return snp_effects

    def get_drugs_by_gene(self, gene_symbol: str) -> List[Dict[str, Any]]:
        """
        Get all drugs affected by a specific gene (pharmacogenomics).

        Args:
            gene_symbol: Gene symbol (e.g., CYP2C19)

        Returns:
            List of drugs with SNP effects for this gene
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        results = cursor.execute("""
            SELECT DISTINCT
                d.drugbank_id,
                d.name,
                d.indication,
                d.groups,
                COUNT(s.id) as snp_count
            FROM drugs d
            JOIN snp_effects s ON d.drugbank_id = s.drugbank_id
            WHERE LOWER(s.gene_symbol) = ?
            GROUP BY d.drugbank_id, d.name, d.indication, d.groups
            ORDER BY snp_count DESC, d.name
        """, (gene_symbol.lower(),)).fetchall()

        drugs = [dict(row) for row in results]
        conn.close()

        logger.info(f"Found {len(drugs)} drugs with SNP effects in gene {gene_symbol}")
        return drugs

    def _get_drug_synonyms(self, cursor, drugbank_id: str) -> List[str]:
        """Get drug synonyms."""
        results = cursor.execute(
            "SELECT synonym FROM drug_synonyms WHERE drugbank_id = ?",
            (drugbank_id,)
        ).fetchall()
        return [row["synonym"] for row in results]

    def _get_drug_dosages(self, cursor, drugbank_id: str) -> List[Dict[str, str]]:
        """Get drug dosages."""
        results = cursor.execute(
            "SELECT form, route, strength FROM drug_dosages WHERE drugbank_id = ?",
            (drugbank_id,)
        ).fetchall()
        return [dict(row) for row in results]

    def _get_drug_snp_effects(self, cursor, drugbank_id: str) -> List[Dict[str, Any]]:
        """Get SNP pharmacogenomic effects."""
        results = cursor.execute(
            """SELECT protein_name, gene_symbol, uniprot_id, rs_id, allele,
               defining_change, description, pubmed_id
               FROM snp_effects WHERE drugbank_id = ?""",
            (drugbank_id,)
        ).fetchall()
        return [dict(row) for row in results]

    def _get_drug_snp_adverse_reactions(self, cursor, drugbank_id: str) -> List[Dict[str, Any]]:
        """Get SNP adverse reactions."""
        results = cursor.execute(
            """SELECT protein_name, gene_symbol, uniprot_id, rs_id, allele,
               adverse_reaction, description, pubmed_id
               FROM snp_adverse_reactions WHERE drugbank_id = ?""",
            (drugbank_id,)
        ).fetchall()
        return [dict(row) for row in results]

    def _get_drug_targets(self, cursor, drugbank_id: str) -> List[Dict[str, str]]:
        """Get drug targets."""
        results = cursor.execute(
            """SELECT target_id, target_name, organism, actions, known_action,
               gene_name, uniprot_id FROM drug_targets WHERE drugbank_id = ?""",
            (drugbank_id,)
        ).fetchall()
        return [dict(row) for row in results]

    def _get_drug_enzymes(self, cursor, drugbank_id: str) -> List[Dict[str, str]]:
        """Get metabolizing enzymes."""
        results = cursor.execute(
            """SELECT enzyme_id, enzyme_name, organism, inhibition_strength,
               induction_strength, gene_name, uniprot_id
               FROM drug_enzymes WHERE drugbank_id = ?""",
            (drugbank_id,)
        ).fetchall()
        return [dict(row) for row in results]

    def _get_drug_interactions(self, cursor, drugbank_id: str) -> List[Dict[str, str]]:
        """Get drug-drug interactions."""
        results = cursor.execute(
            """SELECT interacting_drugbank_id, interacting_drug_name, description
               FROM drug_interactions WHERE drugbank_id = ?""",
            (drugbank_id,)
        ).fetchall()
        return [dict(row) for row in results]

    def _get_drug_categories(self, cursor, drugbank_id: str) -> List[Dict[str, str]]:
        """Get drug categories."""
        results = cursor.execute(
            "SELECT category, mesh_id FROM drug_categories WHERE drugbank_id = ?",
            (drugbank_id,)
        ).fetchall()
        return [dict(row) for row in results]

    def get_all_drug_names(self, approved_only: bool = True) -> List[Dict[str, str]]:
        """
        Get all drug names for autocomplete.

        Args:
            approved_only: Only return approved drugs

        Returns:
            List of {name, drugbank_id, type} dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        sql = "SELECT drugbank_id, name, groups FROM drugs"
        if approved_only:
            sql += " WHERE groups LIKE '%approved%'"
        sql += " ORDER BY name"

        drugs = []
        for row in cursor.execute(sql).fetchall():
            drugs.append({
                "name": row["name"],
                "drugbank_id": row["drugbank_id"],
                "type": "generic"
            })

            # Add synonyms for this drug
            synonyms = cursor.execute(
                "SELECT synonym FROM drug_synonyms WHERE drugbank_id = ? LIMIT 5",
                (row["drugbank_id"],)
            ).fetchall()

            for syn in synonyms:
                drugs.append({
                    "name": syn["synonym"],
                    "drugbank_id": row["drugbank_id"],
                    "type": "synonym"
                })

        conn.close()
        logger.info(f"Retrieved {len(drugs)} drug names for autocomplete")
        return drugs


# Singleton instance
_drugbank_service = None


def get_drugbank_service() -> DrugBankService:
    """Get singleton DrugBank service instance."""
    global _drugbank_service
    if _drugbank_service is None:
        _drugbank_service = DrugBankService()
    return _drugbank_service
