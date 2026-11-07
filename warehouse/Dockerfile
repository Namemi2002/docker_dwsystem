# Used mysql:8.0.46 as based image
FROM mysql:8.0.46

# Copy .sql files into docker-entrypoint-initdb.d/ directory, to make Docker initialize (if not exist available database) query in those files at the first time creating a container
# The database container will initialize data in alphabetical order of file name (note: digits < letters)
COPY init_create/01_mydudw.sql /docker-entrypoint-initdb.d/
COPY init_create/02_maybymay.sql /docker-entrypoint-initdb.d/
COPY init_insert/dwtable_updatetime_log.sql /docker-entrypoint-initdb.d/
COPY init_insert/customerbanks.sql /docker-entrypoint-initdb.d/
COPY init_insert/delivery_reconciliation.sql /docker-entrypoint-initdb.d/
COPY init_insert/deliveryorders.sql /docker-entrypoint-initdb.d/
COPY init_insert/handle_deliveryorders.sql /docker-entrypoint-initdb.d/
COPY init_insert/mbm_delivery_reconciliation.sql /docker-entrypoint-initdb.d/
COPY init_insert/mbm_deliveryorders.sql /docker-entrypoint-initdb.d/
COPY init_insert/mbm_metaads.sql /docker-entrypoint-initdb.d/
COPY init_insert/mbm_pos_orderdetails.sql /docker-entrypoint-initdb.d/
COPY init_insert/mbm_pos_orders.sql /docker-entrypoint-initdb.d/
COPY init_insert/mbm_testorders0.sql /docker-entrypoint-initdb.d/
COPY init_insert/nhanhvnorderdetails.sql /docker-entrypoint-initdb.d/
COPY init_insert/nhanhvnorders.sql /docker-entrypoint-initdb.d/
COPY init_insert/returnedorders_scan.sql /docker-entrypoint-initdb.d/
COPY init_insert/shopeeorderdetails.sql /docker-entrypoint-initdb.d/
COPY init_insert/shopeeorders.sql /docker-entrypoint-initdb.d/
COPY init_insert/tiktok_reconciliation.sql /docker-entrypoint-initdb.d/
COPY init_insert/tiktokorderdetails.sql /docker-entrypoint-initdb.d/
COPY init_insert/tiktokorders.sql /docker-entrypoint-initdb.d/
COPY init_insert/zzzzz_initialization_complete.sql /docker-entrypoint-initdb.d/