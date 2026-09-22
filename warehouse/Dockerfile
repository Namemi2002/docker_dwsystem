# Used mysql:8.0.46 as based image
FROM mysql:8.0.46

# Copy .sql files into docker-entrypoint-initdb.d/ directory, to make Docker initialize (if not exist available database) query in those files at the first time creating a container
# The database container will initialize data in alphabetical order of file name (note: digits < letters)
COPY init_create/01_mydudw.sql /docker-entrypoint-initdb.d/
COPY init_create/02_maybymay.sql /docker-entrypoint-initdb.d/
COPY init_insert/dwtable_updatetime_log.sql /docker-entrypoint-initdb.d/
COPY init_insert/customerbanks_202609190918.sql /docker-entrypoint-initdb.d/
COPY init_insert/delivery_reconciliation_202609190919.sql /docker-entrypoint-initdb.d/
COPY init_insert/deliveryorders_202609190921.sql /docker-entrypoint-initdb.d/
COPY init_insert/handle_deliveryorders_202609190921.sql /docker-entrypoint-initdb.d/
COPY init_insert/mbm_delivery_reconciliation_202609190948.sql /docker-entrypoint-initdb.d/
COPY init_insert/mbm_deliveryorders_202609190948.sql /docker-entrypoint-initdb.d/
COPY init_insert/mbm_metaads_202609190949.sql /docker-entrypoint-initdb.d/
COPY init_insert/mbm_pos_orderdetails_202609190949.sql /docker-entrypoint-initdb.d/
COPY init_insert/mbm_pos_orders_202609190950.sql /docker-entrypoint-initdb.d/
COPY init_insert/mbm_testorders_202609190950.sql /docker-entrypoint-initdb.d/
COPY init_insert/nhanhvnorderdetails_202609190922.sql /docker-entrypoint-initdb.d/
COPY init_insert/nhanhvnorders_202609190924.sql /docker-entrypoint-initdb.d/
COPY init_insert/returnedorders_scan_202609190925.sql /docker-entrypoint-initdb.d/
COPY init_insert/shopeeorderdetails_202609190925.sql /docker-entrypoint-initdb.d/
COPY init_insert/shopeeorders_202609190926.sql /docker-entrypoint-initdb.d/
COPY init_insert/tiktok_reconciliation_202609190926.sql /docker-entrypoint-initdb.d/
COPY init_insert/tiktokorderdetails_202609190927.sql /docker-entrypoint-initdb.d/
COPY init_insert/tiktokorders_202609190928.sql /docker-entrypoint-initdb.d/
COPY init_insert/zzzzz_initialization_complete.sql /docker-entrypoint-initdb.d/