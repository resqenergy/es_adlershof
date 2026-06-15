"""
This module prepares flat data from Technikkatalog to be used by oemof-pipe.

Steps:
1. Last sheet (flatdata_all) of Technikkatalog must be extracted and saved as CSV.
2. Adapt name (depending on ES component names and capacity dimensions) and parameters (depending on oemof.solph attributes) to your needs.
3. Run this script.
4. Use resulting CSV in oemof-pipe scenario
"""

from utils.technikkatalog import Technology, get_technology_data

from settings import DATASETS_DIR

FLATDATA_FILE_PREPROCESSED = DATASETS_DIR / "technology_cost" / "kww_technikkatalog.csv"
FLATDATA_FILE_PREPROCESSED.parent.mkdir(exist_ok=True)


TECHNOLOGY_MAPPING = {
    Technology("AbwaermeWP_zentral", 2): "heatpump_office",
    Technology("AbwaermeWP_zentral", 10): "heatpump_nt",
    Technology("AbwaermeWP_zentral", 20): "heatpump_mt",
    Technology("BHKW_zentral", 0.3): "bhkw",
    Technology("Tiefengeothermie_ab400_direkt_zentral", 10): "heatpump_geothermal",
    Technology("AbwasserWP_zentral", 10): "heatpump_wastewater",
    Technology("GewaesserWP_zentral", 10): "heatpump_canal",
    Technology("Solarthermie_flach_dezentral", 10): "heat_decentral-solarthermal",
}


if __name__ == "__main__":
    technology_df = get_technology_data(TECHNOLOGY_MAPPING)
    technology_df.to_csv(FLATDATA_FILE_PREPROCESSED, index=False, sep=";")
