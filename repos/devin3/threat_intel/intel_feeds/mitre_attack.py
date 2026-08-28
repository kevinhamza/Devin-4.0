# Devin/threat_intel/intel_feeds/mitre_attack.py
# Purpose: A client to download, cache, and query the MITRE ATT&CK
#          Enterprise framework, providing a local TTP database.

import logging
import requests
import json
from pathlib import Path
import time
from typing import Dict, Any, Optional, List

# Configure basic logging
logger = logging.getLogger("MitreAttackDB")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)


class MitreAttackDB:
    """
    Manages a local, queryable database of the MITRE ATT&CK Enterprise framework.
    """
    ENTERPRISE_ATTACK_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"

    def __init__(self, cache_dir: str = "intel_cache", cache_duration_days: int = 7):
        self.cache_path = Path(cache_dir) / "enterprise-attack.json"
        self.cache_duration_sec = cache_duration_days * 86400
        self.cache_path.parent.mkdir(exist_ok=True)
        
        # In-memory indexed data
        self.techniques: Dict[str, Dict] = {}
        self.tactics: Dict[str, Dict] = {}
        self.mitigations: Dict[str, Dict] = {}
        self.relationships: List[Dict] = []

        self._load_data()

    def _fetch_from_mitre(self) -> Optional[Dict]:
        """Downloads the latest STIX data from MITRE's CTI repository."""
        logger.info(f"Downloading latest MITRE ATT&CK data from {self.ENTERPRISE_ATTACK_URL}...")
        try:
            response = requests.get(self.ENTERPRISE_ATTACK_URL, timeout=60)
            response.raise_for_status()
            data = response.json()
            with open(self.cache_path, 'w') as f:
                json.dump(data, f)
            logger.info(f"Successfully downloaded and cached data to '{self.cache_path}'.")
            return data
        except requests.RequestException as e:
            logger.error(f"Failed to download ATT&CK data: {e}")
            return None

    def _load_data(self):
        """Loads data from the cache if it's recent, otherwise fetches it."""
        data = None
        if self.cache_path.exists():
            file_age = time.time() - self.cache_path.stat().st_mtime
            if file_age < self.cache_duration_sec:
                logger.info(f"Loading ATT&CK data from recent cache file (age: {file_age/3600:.1f} hours).")
                with open(self.cache_path, 'r') as f:
                    data = json.load(f)
            else:
                logger.warning("Cache file is outdated. Fetching fresh data.")
                data = self._fetch_from_mitre()
        else:
            data = self._fetch_from_mitre()

        if data:
            self._parse_and_index(data)

    def _parse_and_index(self, stix_data: Dict):
        """Parses the raw STIX bundle and indexes the objects for fast querying."""
        logger.info("Parsing and indexing STIX data...")
        
        # Pass 1: Index all objects by their STIX ID
        stix_objects_by_id = {obj['id']: obj for obj in stix_data.get('objects', [])}

        # Pass 2: Process and store objects in a more useful format
        for obj_id, obj in stix_objects_by_id.items():
            obj_type = obj.get('type')
            
            if obj_type == 'attack-pattern': # Technique
                ext_refs = obj.get('external_references', [{}])
                technique_id = ext_refs[0].get('external_id', '')
                self.techniques[technique_id] = {
                    "id": technique_id, "stix_id": obj_id, "name": obj.get('name'),
                    "description": obj.get('description'), "tactics": [kc['phase_name'] for kc in obj.get('kill_chain_phases', [])]
                }
            elif obj_type == 'x-mitre-tactic':
                ext_refs = obj.get('external_references', [{}])
                tactic_id = ext_refs[0].get('external_id', '')
                shortname = obj.get('x_mitre_shortname', '')
                self.tactics[shortname] = {
                    "id": tactic_id, "stix_id": obj_id, "name": obj.get('name'), "shortname": shortname
                }
            elif obj_type == 'course-of-action': # Mitigation
                ext_refs = obj.get('external_references', [{}])
                mitigation_id = ext_refs[0].get('external_id', '')
                self.mitigations[mitigation_id] = {
                    "id": mitigation_id, "stix_id": obj_id, "name": obj.get('name'), "description": obj.get('description')
                }
            elif obj_type == 'relationship':
                self.relationships.append(obj)
        
        # Pass 3: Link objects using relationships
        for rel in self.relationships:
            if rel.get('relationship_type') == 'mitigates' and rel.get('source_ref') in stix_objects_by_id and rel.get('target_ref') in stix_objects_by_id:
                mitigation_stix_id = rel['source_ref']
                technique_stix_id = rel['target_ref']
                
                # Find the technique and mitigation by their STIX IDs and add the link
                for tech in self.techniques.values():
                    if tech['stix_id'] == technique_stix_id:
                        for mit in self.mitigations.values():
                            if mit['stix_id'] == mitigation_stix_id:
                                tech.setdefault('mitigations', []).append(mit['id'])
                                break
                        break

        logger.info(f"Indexing complete. Found {len(self.tactics)} tactics and {len(self.techniques)} techniques.")

    def get_technique_by_id(self, technique_id: str) -> Optional[Dict]:
        """Retrieves a technique by its external ID (e.g., 'T1548')."""
        return self.techniques.get(technique_id.upper())

    def find_techniques_for_tactic(self, tactic_shortname: str) -> List[Dict]:
        """Finds all techniques associated with a given tactic shortname (e.g., 'persistence')."""
        return [tech for tech in self.techniques.values() if tactic_shortname in tech.get('tactics', [])]

    def get_mitigations_for_technique(self, technique_id: str) -> List[Dict]:
        """Retrieves all mitigation strategies for a given technique ID."""
        technique = self.get_technique_by_id(technique_id)
        if not technique or 'mitigations' not in technique:
            return []
        return [self.mitigations[mit_id] for mit_id in technique['mitigations'] if mit_id in self.mitigations]

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== MITRE ATT&CK Threat Intelligence DB Demo ⚔️ ===")
    print("=========================================================")
    
    try:
        # This will automatically download/update the database on first run
        db = MitreAttackDB()
        
        if not db.techniques:
            print("\nCould not load MITRE ATT&CK database. Please check your internet connection.")
        else:
            # --- 1. Look up a specific Technique ---
            print("\n--- 1. Looking up Technique T1059.001 (PowerShell) ---")
            technique = db.get_technique_by_id("T1059.001")
            if technique:
                print(f"  Name: {technique['name']}")
                print(f"  Description: {technique['description'][:150]}...")
            else:
                print("  Technique not found.")
                
            # --- 2. Find all techniques for a Tactic ---
            print("\n\n--- 2. Finding all techniques for the 'Defense Evasion' Tactic ---")
            tactic_shortname = "defense-evasion"
            techniques_in_tactic = db.find_techniques_for_tactic(tactic_shortname)
            print(f"  Found {len(techniques_in_tactic)} techniques for '{tactic_shortname}'.")
            print("  Examples:")
            for tech in techniques_in_tactic[:3]:
                print(f"    - {tech['id']}: {tech['name']}")
                
            # --- 3. Find all mitigations for a Technique ---
            print("\n\n--- 3. Finding mitigations for T1059.001 (PowerShell) ---")
            mitigations = db.get_mitigations_for_technique("T1059.001")
            if mitigations:
                print(f"  Found {len(mitigations)} mitigation strategies:")
                for mit in mitigations:
                    print(f"    - {mit['id']}: {mit['name']}")
            else:
                print("  No mitigations found for this technique.")

    except Exception as e:
        logger.error(f"Demo failed to run: {e}", exc_info=True)

    print("\n=========================================================")
    print("=== Threat Intelligence DB Demo Complete ===")
    print("=========================================================")
