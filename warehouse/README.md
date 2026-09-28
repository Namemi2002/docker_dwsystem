# Warehouse Service

## 1. Role

The **Warehouse Service** provides centralized and persistent storage for data collected and processed by the Pipeline Service. The architecture is designed to support both historical data preservation and business reporting, while keeping source-level data available for debugging and further analysis.

---

## 2. Architecture

The Warehouse Service currently contains two separate databases, with each database corresponding to one company:

### Mydu — database name: `mydudw`

The Mydu database uses a **two-layer architecture**:

- **Data Lake:** Stores data close to its source representation. It serves as a backup for the Data Warehouse, supports debugging, and provides additional data for advanced analysis when the required data is not available in the Data Warehouse. Data Lake tables may or may not have primary keys and do not use foreign keys.

- **Data Warehouse:** Serves as the **single source of truth** for dashboards and basic analysis. It contains highly cleaned and standardized data and uses a **Star Schema** with **1 fact table and 5 dimension tables**.

Visit `/warehouse/init_create/01_mydudw.sql` for detailed information about table schema and relationships of this database.

For reference, this architecture can be compared to the Medallion Architecture, where the Data Lake plays a role similar to the **Silver layer** and the Data Warehouse plays a role similar to the **Gold layer**.

### Mây By Mây — database name: `maybymaydw`

The Mây By Mây database only contains a **Data Lake** because its current reporting requirements are relatively simple.

Its Data Lake serves the same purposes as the Mydu Data Lake: preserving source-level data, providing a backup, supporting debugging, and providing additional data for analysis when required.

A separate Data Warehouse layer for this business is not implemented because it is not currently necessary for that company's reporting requirements.

Visit `/warehouse/init_create/02_maybymay.sql` for detailed information about table schema of this database.