from src import orchestrator
from src import logger
import pymysql
import sys
import warnings
mysql_connection = pymysql.connect(
    host = orchestrator.db_host,
    user = orchestrator.db_user,
    password = orchestrator.db_password,
    database = orchestrator.db_databasename,
    port = orchestrator.db_port
)
warnings.formatwarning = logger.custom_formatwarning
sys.stdout = logger.LoggerStdout(mysql_connection, orchestrator.currenttime)
sys.stderr = logger.LoggerStderr(mysql_connection, orchestrator.currenttime)
orchestrator.run_ghtk_exceletl(mysql_connection)
orchestrator.run_ghn_exceletl(mysql_connection, orchestrator.configinfo['ghn']['excel']['path'], orchestrator.etltolake_query['deliveryorders'])
orchestrator.run_jte_exceletl(mysql_connection, orchestrator.configinfo['jte']['excel']['path'], orchestrator.etltolake_query['deliveryorders'])
orchestrator.run_spx_exceletl(mysql_connection)
orchestrator.run_codtvc_apietl(mysql_connection)
orchestrator.run_cusbank_apietl(mysql_connection)
orchestrator.run_internalprice_apietl(mysql_connection)
orchestrator.run_returnedorderscan_apietl(mysql_connection)
orchestrator.run_deliveryorderscan_apietl(mysql_connection)
orchestrator.run_deliveryordershandlingteam_apietl(mysql_connection)
orchestrator.run_jtetransactions_exceletl(mysql_connection, orchestrator.configinfo['transaction_jte']['excel'], orchestrator.etltolake_query['delivery_reconciliation'])
orchestrator.run_spxtransactions_exceletl(mysql_connection)
orchestrator.run_ghntransactions_exceletl(mysql_connection, orchestrator.configinfo['transaction_ghn']['excel'], orchestrator.etltolake_query['delivery_reconciliation'])
orchestrator.run_ghncointransactions_exceletl(mysql_connection, orchestrator.configinfo['cointransaction_ghn']['excel'], orchestrator.etltolake_query['delivery_reconciliation'])
orchestrator.run_tiktokincome_exceletl(mysql_connection)
orchestrator.run_nhanhvn_apietl(mysql_connection)
orchestrator.run_shopee_apietl(mysql_connection)
orchestrator.run_tiktok_apietl(mysql_connection)
orchestrator.run_laketowarehouse_etl(orchestrator.LAKETOWAREHOUSE_QUERYPATH, mysql_connection)
orchestrator.updatereport_googlesheet(mysql_connection, orchestrator.configinfo['updatereport_ggsheet'])
mysql_connection.close()