from src import orchestrator
from src import logger
import pymysql
import sys
import warnings


mysql_connection = pymysql.connect(
    host=orchestrator.db_maybymayhost,
    user=orchestrator.db_maybymayuser,
    password=orchestrator.db_maybymaypassword,
    database=orchestrator.db_maybymaydatabasename,
    port=orchestrator.db_maybymayport,
)

warnings.formatwarning = logger.custom_formatwarning
sys.stdout = logger.LoggerStdout(mysql_connection, orchestrator.currenttime)
sys.stderr = logger.LoggerStderr(mysql_connection, orchestrator.currenttime)

orchestrator.run_ghn_exceletl(
    mysql_connection,
    orchestrator.configinfo['maybymay_ghn']['excel']['path'],
    orchestrator.maybymay_etltolake_query['mbm_deliveryorders'],
)
orchestrator.run_jte_exceletl(
    mysql_connection,
    orchestrator.configinfo['maybymay_jte']['excel']['path'],
    orchestrator.maybymay_etltolake_query['mbm_deliveryorders'],
)
orchestrator.run_jtetransactions_exceletl(
    mysql_connection,
    orchestrator.configinfo['maybymay_transaction_jte']['excel'],
    orchestrator.maybymay_etltolake_query['mbm_delivery_reconciliation'],
    sessionid_outoftable='Yes',
)
orchestrator.run_ghntransactions_exceletl(
    mysql_connection,
    orchestrator.configinfo['maybymay_transaction_ghn']['excel'],
    orchestrator.maybymay_etltolake_query['mbm_delivery_reconciliation'],
)
orchestrator.run_ghncointransactions_exceletl(
    mysql_connection,
    orchestrator.configinfo['maybymay_cointransaction_ghn']['excel'],
    orchestrator.maybymay_etltolake_query['mbm_delivery_reconciliation'],
)
orchestrator.run_pos_apietl(
    mysql_connection,
    orchestrator.configinfo['maybymay_pos']['api']['orders'],
    orchestrator.configinfo['maybymay_pos']['account'],
)
orchestrator.run_mbmmetaads_apietl(mysql_connection)
orchestrator.run_mbmordertest_apietl(mysql_connection)
orchestrator.updatereport_googlesheet(
    mysql_connection,
    orchestrator.configinfo['maybymay_updatereport_ggsheet'],
)
mysql_connection.close()
