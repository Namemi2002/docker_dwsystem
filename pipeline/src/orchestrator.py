from .extractor import extractorclasses
from .cleaner import cleanerclasses
from .loader import loaderclasses
from datetime import datetime, timezone, timedelta
import yaml
from pathlib import Path
import pandas as pd
import time
import glob
import warnings
import os
from dotenv import load_dotenv
from typing import Literal


# Declare necessary variables
ROOTDIR = Path(__file__).resolve().parent.parent
CONFIGPATH = ROOTDIR / 'pipelineconfig.yaml'
GGSERVICEKEY = ROOTDIR / 'secretkey' / 'googlesheet_service_key.json'
ENVPATH = ROOTDIR / '.env'
ENVRUNCONFIGPATH = ROOTDIR / '.env.runconfig'
EXCELDATASOURCEPATH = ROOTDIR / 'excel_datasource'
ETLTOLAKE_QUERYPATH = ROOTDIR / 'sqletlquery' / 'mydu' / 'etltolake.sql'
MAYBYMAY_ETLTOLAKE_QUERYPATH = ROOTDIR / 'sqletlquery' / 'maybymay' / 'maybymay_etltolake.sql'
LAKETOWAREHOUSE_QUERYPATH = ROOTDIR / 'sqletlquery' / 'mydu' / 'laketowarehouse.sql'
DELETERECORDS_NHANHVN_QUERYPATH = ROOTDIR / 'sqletlquery' / 'mydu' / 'deleterecords_nhanhvnorders.sql'
DELETERECORDS_MAYBYMAY_POSORDERS_QUERYPATH = ROOTDIR / 'sqletlquery' / 'maybymay' / 'deleterecords_maybymay_posorders.sql'
DELETERECORDS_MAYBYMAY_METAADS_QUERYPATH = ROOTDIR / 'sqletlquery' / 'maybymay' / 'deleterecords_maybymay_metaads.sql'
currenttime = datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None)


# Declare variables that contain config and secret information
with open(CONFIGPATH, 'r', encoding='utf-8') as file:
    configinfo = yaml.safe_load(file) # configinfo is a dictionary
load_dotenv(ENVPATH)
load_dotenv(ENVRUNCONFIGPATH)


# Declare database connection variables:
db_host = os.getenv('DW_HOST_MYDU')
db_user = os.getenv('DW_USER_MYDU')
db_password = os.getenv('DW_PASSWORD_MYDU')
db_databasename = os.getenv('DW_DATABASENAME_MYDU')
db_port = int(os.getenv('DW_PORT_MYDU'))
db_maybymayhost = os.getenv('DW_HOST_MAYBYMAY')
db_maybymayuser = os.getenv('DW_USER_MAYBYMAY')
db_maybymaypassword = os.getenv('DW_PASSWORD_MAYBYMAY')
db_maybymaydatabasename = os.getenv('DW_DATABASENAME_MAYBYMAY')
db_maybymayport =  int(os.getenv('DW_PORT_MAYBYMAY'))


# Build functions to run ETL pipelines:
def is_run(isrun):
    if isrun != 'run':
        raise Exception('You configured to stop running this function')


def read_sqlquery(filepath, split_char: str, fileencoding='utf-8'):
    """
    :param filepath: the file contains queries that you want to convert to a key:value dictionary
    :param split_char: character to split queries
    :param fileencoding: 'utf-8' as default
    :return: return a key:value dictionary, key is the name of the mysql query, value is the query
    """
    with open(filepath, 'r', encoding=fileencoding) as file:
        content = file.read() # content is a string
    dict_query = {}
    content = content.split(split_char) # content now becomes a list of strings
    for text in content:
        if text.strip() == '':
            continue
        else:
            query = text.strip().split('\n') # query is a list of strings
            key = query[0].strip()
            value = ''
            for i in query[1:]:
                value = value + i.strip() + '\n'
            value = value.strip()
            dict_query[key] = value
    return dict_query
etltolake_query = read_sqlquery(ETLTOLAKE_QUERYPATH, '--name:')
maybymay_etltolake_query = read_sqlquery(MAYBYMAY_ETLTOLAKE_QUERYPATH, '--name:')


def return_message(pipelinename, state: Literal['success', 'neutral', 'failed'], message, *, errormessage=None):
    if state == 'failed':
        warnings.warn(f"{pipelinename} ({state}): {message}{'' if errormessage is None else f'\nError:\n{errormessage}'}")
    else:
        print(f"{pipelinename} ({state}): {message}")


def run_sqlscript(filepath, connection, *, params: dict[str,any] = None, fileencoding = 'utf-8'):
    """
    Purpose: execute all query in a .sql file
    :param filepath: the file contains queries you want to execute
    :param params: the .sql file may contain named placeholder (showed inside {}), use this parameter to fill those placeholders. params is a key:value dictionary, key is placeholder name, value is placeholder value
    :param connection: mysql.connector.connection.MySQLConnection object
    :param fileencoding: 'utf-8' as default
    :return: None.
    """
    with open(filepath, 'r', encoding=fileencoding) as file:
        content = file.read() # content is a string
    if params is not None:
        content = content.format(**params)
    content = content.split(';') # content now becomes a list of strings
    cursor = connection.cursor()
    try:
        for query in content:
            query = query.strip()
            if query == '':
                continue
            else:
                cursor.execute(query)
                return_message("run_sqlscript", "success", f"performed the query:\n{query}")
        connection.commit()
    except:
        connection.rollback()
        raise
    finally:
        cursor.close()


def run_laketowarehouse_etl(filepath, connection):
    try:
        is_run(os.getenv('RUN_LAKETOWAREHOUSE_ETL'))
        run_sqlscript(filepath, connection)
    except Exception as e:
        warnings.warn(f"orchestrator: run_laketowarehouse_etl: {e}")


def run_shopee_apietl(sqlconnection):
    shopeetoken = extractorclasses.GoogleSheetExtractor(GGSERVICEKEY)
    shopinfo = shopeetoken.extractlist(os.getenv('GGSHEET_SHOPEE_TOKEN_IDFILE'), int(os.getenv('GGSHEET_SHOPEE_TOKEN_IDSHEET')), 'A2:I')
    for shop in shopinfo:
        try:
            is_run(os.getenv('RUN_SHOPEE_APIETL'))
            # If the access_token is nearly or was expired, refresh the access_token and store new access_token and new refresh_token into the google sheet file:
            current = int(currenttime.timestamp())
            if int(shop[7]) + int(shop[8]) < current + configinfo['shopee']['token']['timerenew_beforeexpired']:
                return_message('run_shopee_apietl', 'neutral', f"refresh the access_token for shop {shop[1]}")
                # Refresh the access_token:
                refresh_shopee = extractorclasses.ShopeeAPIAuthentication(
                    '/api/v2/auth/access_token/get',
                    int(shop[3]),
                    shop[4],
                    int(shop[2]),
                    shop[6],
                    configinfo['shopee']['token']['header_gettoken_endpoint']
                )
                tokeninfo = refresh_shopee.extractdata() # tokeninfo is a dictionary: dict[str, str]
                shop[5] = tokeninfo['access_token']
                # Store new access_token and new refresh_token:
                sheetupdate = shopeetoken.extractsheet(os.getenv('GGSHEET_SHOPEE_TOKEN_IDFILE'), int(os.getenv('GGSHEET_SHOPEE_TOKEN_IDSHEET')))
                sheetupdate.update_acell('F' + str(int(shop[0])+1), tokeninfo['access_token'])
                sheetupdate.update_acell('G' + str(int(shop[0])+1), tokeninfo['refresh_token'])
                sheetupdate.update_acell('H' + str(int(shop[0])+1), current)
                sheetupdate.update_acell('I' + str(int(shop[0])+1), tokeninfo['expire_in'])
            # Extract: retrieve json data:
            return_message('run_shopee_apietl', 'neutral', f"retrieve orders data from API, shop {shop[1]}")
            dict_starttime_config = configinfo['shopee']['api']['orders']['starttime']
            dict_endtime_config = configinfo['shopee']['api']['orders']['endtime']
            orders = extractorclasses.ShopeeGetRecordsByTimeintervalAPIExtractor(
                '/api/v2/order/get_order_list',
                'GET',
                int(shop[3]),
                shop[4],
                int(shop[2]),
                shop[5],
                configinfo['shopee']['api']['header_other_endpoints'],
                {list(dict_starttime_config.keys())[0] : os.getenv(dict_starttime_config[list(dict_starttime_config.keys())[0]])},
                {list(dict_endtime_config.keys())[0] : os.getenv(dict_endtime_config[list(dict_endtime_config.keys())[0]])},
                'int',
                configinfo['shopee']['api']['orders']['chunk_date'],
                configinfo['shopee']['api']['orders']['page_size'],
                ['response', 'order_list'],
                ['response', 'next_cursor'],
                params_extension={'time_range_field': 'create_time'},
                append_returnlist_position=['order_sn']
            )
            orders_data = orders.extractdata() # orders_data is a list of string, each string is an order ID
            orderdetail = extractorclasses.ShopeeGetRecordsByListAPIExtractor(
                '/api/v2/order/get_order_detail',
                'GET',
                int(shop[3]),
                shop[4],
                int(shop[2]),
                shop[5],
                configinfo['shopee']['api']['header_other_endpoints'],
                orders_data,
                'str',
                'order_sn_list',
                configinfo['shopee']['api']['orderdetail']['chunk_record'],
                ['response', 'order_list'],
                params_extension={'response_optional_fields':'buyer_user_id,buyer_username,estimated_shipping_fee,recipient_address,actual_shipping_fee,note,note_update_time,item_list,pay_time,buyer_cancel_reason,cancel_by,cancel_reason,actual_shipping_fee_confirmed,fulfillment_flag,pickup_done_time,package_list,shipping_carrier,payment_method,total_amount,buyer_username,invoice_data,return_request_due_date,payment_info,model_discounted_price,model_original_price'}
            )
            orderdetail_data = orderdetail.extractdata() # orderdetail_data is a list of dictionaries, each dictionary is detail information of an order
            escrowdetail = extractorclasses.ShopeeGetRecordsByListAPIExtractor(
                '/api/v2/payment/get_escrow_detail_batch',
                'POST',
                int(shop[3]),
                shop[4],
                int(shop[2]),
                shop[5],
                configinfo['shopee']['api']['header_other_endpoints'],
                orders_data,
                'list[str]',
                'order_sn_list',
                configinfo['shopee']['api']['escrowdetail']['chunk_record'],
                ['response'],
                append_returnlist_position=['escrow_detail']
            )
            escrowdetail_data = escrowdetail.extractdata() # escrowdetail_data is list of dictionaries, each dictionary is escrow detail information of an order
            trackingnumber = extractorclasses.ShopeeGetRecordsByListAPIExtractor(
                '/api/v2/logistics/get_mass_tracking_number',
                'POST',
                int(shop[3]),
                shop[4],
                int(shop[2]),
                shop[5],
                configinfo['shopee']['api']['header_other_endpoints'],
                extractorclasses.getshopeepackagelist_fromorderdetaillist(orderdetail_data),
                'list[dict]',
                'package_list',
                configinfo['shopee']['api']['mass_tracking_number']['chunk_record'],
                ['response', 'success_list'],
                keyname_buildmethodlistofdict='package_number'
            )
            trackingnumber_data = trackingnumber.extractdata() # trackingnumber_data is a list of dictionaries, each dictionary contains information of package_number and tracking_number
            dict_starttime_income_config = configinfo['shopee']['api']['orderincome']['starttime']
            dict_endtime_income_config = configinfo['shopee']['api']['orderincome']['endtime']
            incomedetail = extractorclasses.ShopeeGetRecordsByTimeintervalAPIExtractor(
                '/api/v2/payment/get_income_detail',
                'GET',
                int(shop[3]),
                shop[4],
                int(shop[2]),
                shop[5],
                configinfo['shopee']['api']['header_other_endpoints'],
                {list(dict_starttime_income_config.keys())[0] : os.getenv(dict_starttime_income_config[list(dict_starttime_income_config.keys())[0]])},
                {list(dict_endtime_income_config.keys())[0] : os.getenv(dict_endtime_income_config[list(dict_endtime_income_config.keys())[0]])},
                'str',
                configinfo['shopee']['api']['orderincome']['chunk_date'],
                configinfo['shopee']['api']['orderincome']['page_size'],
                ['response', 'list'],
                ['response', 'next_page', 'cursor'],
                params_extension={'income_status': 1}
            )
            incomedetail_data = incomedetail.extractdata() # incomedetail_data is a list of dictionaries, each dictionary is income detail of an order
            # Clean: Convert json data to dataframe:
            return_message('run_shopee_apietl', 'neutral', f"clean orders data from API, shop {shop[1]}")
            cleanshopeeorder = cleanerclasses.OrdersShopeeAPICleaner(orderdetail_data, escrowdetail_data, trackingnumber_data, shop[1])
            shopeeorders_df = cleanshopeeorder.cleandata()
            shopeeorderdetails_df = cleanshopeeorder.cleandata_orderdetails()
            shopeeorders_df = cleanerclasses.cleandatetime_df(
                shopeeorders_df,
                {'Ngày đặt hàng':'s', 'Ngày lấy hàng':'s', 'Ngày hoàn thành':'s'},
                to_datetime_param = 'unit'
            )
            cleanincomedetail = cleanerclasses.IncomeShopeeAPICleaner(incomedetail_data)
            incomedetail_df = cleanincomedetail.cleandata()
            incomedetail_df = cleanerclasses.cleandatetime_df(
                incomedetail_df,
                {'Thời gian giao dịch': 's'},
                to_datetime_param='unit'
            )
            # Upload: Upload the dataframe to datalake:
            return_message('run_shopee_apietl', 'neutral', f"upload orders data from API to datalake, shop {shop[1]}")
            loadorders = loaderclasses.DataframeToDatabaseLoader(
                shopeeorders_df,
                sqlconnection,
                etltolake_query['shopeeorders'],
                currenttime
            )
            loadorderdetail = loaderclasses.DataframeToDatabaseLoader(
                shopeeorderdetails_df,
                sqlconnection,
                etltolake_query['shopeeorderdetails'],
                currenttime
            )
            loadincomedetail = loaderclasses.DataframeToDatabaseLoader(
                incomedetail_df,
                sqlconnection,
                etltolake_query['delivery_reconciliation'],
                currenttime
            )
            loadorders.loaddata()
            loadorderdetail.loaddata()
            loadincomedetail.loaddata()
            return_message('run_shopee_apietl', 'success', f"the whole ETL for shop {shop[1]} has run successfully!")
            time.sleep(5)
        except Exception as e:
            return_message('run_shopee_apietl', 'failed', f"the ETL pipeline for shop {shop[1]} has failed. Data have not been loaded to datalake", errormessage=e)


def run_tiktok_apietl(sqlconnection):
    tiktoktoken = extractorclasses.GoogleSheetExtractor(GGSERVICEKEY)
    shopinfo = tiktoktoken.extractlist(os.getenv('GGSHEET_TIKTOK_TOKEN_IDFILE'), int(os.getenv('GGSHEET_TIKTOK_TOKEN_IDSHEET')), 'A2:I')
    for shop in shopinfo:
        try:
            is_run(os.getenv('RUN_TIKTOK_APIETL'))
            # If the access_token is nearly or was expired, refresh the access_token and store new access_token and new refresh_token into the google sheet file:
            current = int(currenttime.timestamp())
            if int(shop[7]) < current + configinfo['tiktok']['token']['timerenew_beforeexpired']:
                return_message('run_tiktok_apietl', 'neutral', f"refresh the access_token for shop {shop[1]}")
                # Refresh the access_token:
                refresh_tiktok = extractorclasses.TiktokAPIAuthentication(
                    '/api/v2/token/refresh',
                    shop[3],
                    shop[4],
                    {'refresh_token': shop[6]},
                    'refresh_token'
                )
                tokeninfo = refresh_tiktok.extractdata()  # tokeninfo is a dictionary: dict[str, Any]
                shop[5] = tokeninfo['data']['access_token']
                # Store new access_token and new refresh_token:
                sheetupdate = tiktoktoken.extractsheet(os.getenv('GGSHEET_TIKTOK_TOKEN_IDFILE'), int(os.getenv('GGSHEET_TIKTOK_TOKEN_IDSHEET')))
                sheetupdate.update_acell('F' + str(int(shop[0]) + 1), tokeninfo['data']['access_token'])
                sheetupdate.update_acell('G' + str(int(shop[0]) + 1), tokeninfo['data']['refresh_token'])
                sheetupdate.update_acell('H' + str(int(shop[0]) + 1), tokeninfo['data']['access_token_expire_in'])
                sheetupdate.update_acell('I' + str(int(shop[0]) + 1), tokeninfo['data']['refresh_token_expire_in'])
            # Extract: retrieve json data:
            return_message('run_tiktok_apietl', 'neutral', f"retrieve orders data from API, shop {shop[1]}")
            dict_starttime_config = configinfo['tiktok']['api']['orders']['strattime']
            dict_endtime_config = configinfo['tiktok']['api']['orders']['endtime']
            orders = extractorclasses.TiktokGetRecordsByTimeintervalAPIExtractor(
                '/order/202309/orders/search',
                'POST',
                shop[3],
                shop[4],
                shop[5],
                shop[2],
                {list(dict_starttime_config.keys())[0] : os.getenv(dict_starttime_config[list(dict_starttime_config.keys())[0]])},
                {list(dict_endtime_config.keys())[0] : os.getenv(dict_endtime_config[list(dict_endtime_config.keys())[0]])},
                'int',
                configinfo['tiktok']['api']['orders']['page_size'],
                ['data', 'orders'],
                ['data', 'next_page_token']
            )
            orders_data = orders.extractdata() # orders_data is a list of dictionaries, each dictionary is information of an order
            returnorders = extractorclasses.TiktokGetRecordsByListAPIExtractor(
                '/return_refund/202602/returns/search',
                'POST',
                shop[3],
                shop[4],
                shop[5],
                shop[2],
                extractorclasses.gettiktokidlist_fromorderlist(orders_data),
                'list[str]',
                'order_ids',
                configinfo['tiktok']['api']['returnorders']['chunk_record'],
                ['data', 'return_orders']
            )
            returnorders_data = returnorders.extractdata() # returnorders_data is a list of dictionaries, each dictionary is information of a returned order
            # Clean: Convert json data to dataframe:
            return_message('run_tiktok_apietl', 'neutral', f"clean orders data from API, shop {shop[1]}")
            cleantiktokorder = cleanerclasses.OrdersTiktokAPICleaner(orders_data, returnorders_data, shop[1])
            tiktokorders_df = cleantiktokorder.cleandata()
            tiktokorderdetails_df = cleantiktokorder.cleandata_orderdetails()
            tiktokorders_df = cleanerclasses.cleandatetime_df(
                tiktokorders_df,
                {'create_time': 's', 'collection_time': 's', 'delivery_time': 's', 'cancel_time': 's'},
                to_datetime_param='unit'
            )
            # Upload: Upload the dataframe to datalake:
            return_message('run_tiktok_apietl', 'neutral', f"upload orders data from API to datalake, shop {shop[1]}")
            loadorders = loaderclasses.DataframeToDatabaseLoader(
                tiktokorders_df,
                sqlconnection,
                etltolake_query['tiktokorders'],
                currenttime
            )
            loadorderdetail = loaderclasses.DataframeToDatabaseLoader(
                tiktokorderdetails_df,
                sqlconnection,
                etltolake_query['tiktokorderdetails'],
                currenttime
            )
            loadorders.loaddata()
            loadorderdetail.loaddata()
            return_message('run_tiktok_apietl', 'success', f"the whole ETL for shop {shop[1]} has run successfully!")
        except Exception as e:
            return_message('run_tiktok_apietl', 'failed', f"the ETL pipeline for shop {shop[1]} has failed. Data have not been loaded to datalake", errormessage=e)


def run_ghtk_exceletl(sqlconnection):
    for deliacc in configinfo['ghtk']['excel']['path'].values(): # deliacc is a dictionary
        try:
            is_run(os.getenv('RUN_GHTK_EXCELETL'))
            name_deliveryorders = os.getenv(deliacc['deliveryorders'])
            name_paymentminutes = os.getenv(deliacc['paymentminutes'])
            if name_deliveryorders is None or name_deliveryorders == '' or name_paymentminutes is None or name_paymentminutes == '':
                return_message('run_ghtk_exceletl', 'failed', 'the file path is None. There is nothing to load to datalake')
            else:
                accountname = deliacc['name']
                name_canceledorders = os.getenv(deliacc['canceledorders'])
                name_compensations = os.getenv(deliacc['compensations'])
                path_deliveryorders = str(EXCELDATASOURCEPATH / name_deliveryorders)
                path_paymentminutes = str(EXCELDATASOURCEPATH / name_paymentminutes)
                path_canceledorders = str(EXCELDATASOURCEPATH / name_canceledorders)
                path_compensations = str(EXCELDATASOURCEPATH / name_compensations)
                checkpath_deliveryorders = deliacc['checkpath_deliveryorders']
                checkpath_paymentminutes = deliacc['checkpath_paymentminutes']
                checkpath_canceledorders = deliacc['checkpath_canceledorders']
                checkpath_compensations = deliacc['checkpath_compensations']
                # Extract: Extract data from excel files:
                ghtk_deliveryorders = extractorclasses.DeliveryOrdersExcelExtractor(
                    'Giao Hang Tiet Kiem',
                    path_deliveryorders,
                    configinfo['ghtk']['excel']['usecols']['deliveryorders'],
                    configinfo['ghtk']['excel']['usedtype']['deliveryorders'],
                    15,
                    accountname,
                    checkpath_deliveryorders
                )
                ghtk_paymentminutes = extractorclasses.ExcelExtractor(
                    'Giao Hang Tiet Kiem',
                    path_paymentminutes,
                    configinfo['ghtk']['excel']['usecols']['paymentminutes'],
                    configinfo['ghtk']['excel']['usedtype']['deliveryorders'],
                    10,
                    checkpath_paymentminutes
                )
                ghtk_canceledorders = extractorclasses.ExcelExtractor(
                    'Giao Hang Tiet Kiem',
                    path_canceledorders,
                    configinfo['ghtk']['excel']['usecols']['deliveryorders'],
                    configinfo['ghtk']['excel']['usedtype']['deliveryorders'],
                    15,
                    checkpath_canceledorders
                )
                ghtk_compensations = extractorclasses.ExcelExtractor(
                    'Giao Hang Tiet Kiem',
                    path_compensations,
                    configinfo['ghtk']['excel']['usecols']['compensations'],
                    configinfo['ghtk']['excel']['usedtype']['compensations'],
                    0,
                    checkpath_compensations
                )
                df_ghtk_deliveryorders = ghtk_deliveryorders.extractdata()
                df_ghtk_paymentminutes = ghtk_paymentminutes.extractdata()
                if path_canceledorders is None or path_canceledorders == '':
                    df_ghtk_canceledorders = None
                else:
                    df_ghtk_canceledorders = ghtk_canceledorders.extractdata()
                if path_compensations is None or path_compensations == '':
                    df_ghtk_compensations = None
                else:
                    df_ghtk_compensations = ghtk_compensations.extractdata()
                # Clean: Clean dataframes:
                cleanghtkorders = cleanerclasses.DeliveryOrdersGHTKExcelCleaner(
                    configinfo['ghtk']['excel']['clean']['finalcols'],
                    df_ghtk_deliveryorders,
                    df_ghtk_paymentminutes,
                    configinfo['ghtk']['excel']['clean']['listfee_paymentminutes'],
                    df_ghtk_canceledorders,
                    df_ghtk_compensations
                )
                ghtkorders_df = cleanghtkorders.cleandata()
                ghtkorders_df = cleanerclasses.cleandatetime_df(
                    ghtkorders_df,
                    {'Thời gian tạo đơn':'%Y-%m-%d %H:%M:%S', 'Thời gian lấy thành công':'%Y-%m-%d %H:%M:%S', 'Thời gian giao hàng thành công':'%Y-%m-%d %H:%M:%S'},
                    to_datetime_param='format'
                )
                # Upload: Upload the dataframe to datalake:
                loadghtkorders = loaderclasses.DataframeToDatabaseLoader(
                    ghtkorders_df,
                    sqlconnection,
                    etltolake_query['deliveryorders'],
                    currenttime
                )
                loadghtkorders.loaddata()
                return_message('run_ghtk_exceletl', 'success', f"the ETL pipeline for the {accountname} account has run successfully!")
        except Exception as e:
            return_message('run_ghtk_exceletl', 'failed', f"the ETL pipeline for the {deliacc.get('name', 'WRONG AT CONFIG')} account has failed. Data have not been loaded to datalake", errormessage=e)


def run_ghn_exceletl(sqlconnection, accounts: dict, uploadquery: str):
    """
    :param sqlconnection:
    :param accounts: a dictionary with keys are 'acc1', 'acc2',...
    :param uploadquery: the MySQL INSERT INTO query to execute.
    :return: None
    """
    for deliacc in accounts.values():
        try:
            is_run(os.getenv('RUN_GHN_EXCELETL'))
            name_deliveryorders = os.getenv(deliacc['deliveryorders'])
            name_cointransactions = os.getenv(deliacc['cointransactions'])
            if name_deliveryorders is None or name_deliveryorders == '' or name_cointransactions is None or name_cointransactions == '':
                return_message('run_ghn_exceletl', 'failed', 'the file path is None. There is nothing to load to datalake')
            else:
                accountname = deliacc['name']
                path_deliveryorders = str(EXCELDATASOURCEPATH / name_deliveryorders)
                path_cointransactions = str(EXCELDATASOURCEPATH / name_cointransactions)
                checkpath_deliveryorders = deliacc['checkpath_deliveryorders']
                checkpath_cointransactions = deliacc['checkpath_cointransactions']
                # Extract:
                ghn_deliveryorders = extractorclasses.DeliveryOrdersExcelExtractor(
                    'Giao Hang Nhanh',
                    path_deliveryorders,
                    configinfo['ghn']['excel']['usecols']['deliveryorders'],
                    configinfo['ghn']['excel']['usedtype']['deliveryorders'],
                    0,
                    accountname,
                    checkpath_deliveryorders
                )
                ghn_cointransactions = extractorclasses.ExcelExtractor(
                    'Giao Hang Nhanh',
                    path_cointransactions,
                    configinfo['ghn']['excel']['usecols']['cointransactions'],
                    configinfo['ghn']['excel']['usedtype']['cointransactions'],
                    2,
                    checkpath_cointransactions
                )
                df_ghn_deliveryorders = ghn_deliveryorders.extractdata()
                df_ghn_cointransactions = ghn_cointransactions.extractdata()
                # Clean:
                cleanghnorders = cleanerclasses.DeliveryOrdersGHNExcelCleaner(
                    configinfo['ghn']['excel']['clean']['finalcols'],
                    df_ghn_deliveryorders,
                    df_ghn_cointransactions
                )
                ghnorders_df = cleanghnorders.cleandata()
                ghnorders_df = cleanerclasses.cleandatetime_df(
                    ghnorders_df,
                    {'Ngày tạo đơn':'%d/%m/%Y', 'Ngày lấy hàng thành công':'%d/%m/%Y', 'Ngày giao hàng thành công':'%d/%m/%Y'},
                    to_datetime_param='format'
                )
                # Upload:
                loadghnorders = loaderclasses.DataframeToDatabaseLoader(
                    ghnorders_df,
                    sqlconnection,
                    uploadquery,
                    currenttime
                )
                loadghnorders.loaddata()
                return_message('run_ghn_exceletl', 'success', f"the ETL pipeline for the {accountname} account has run successfully!")
        except Exception as e:
            return_message('run_ghn_exceletl', 'failed', f"the ETL pipeline for the {deliacc.get('name', 'WRONG AT CONFIG')} account has failed. Data have not been loaded to datalake", errormessage=e)


def run_jte_exceletl(sqlconnection, accounts: dict, uploadquery: str):
    """
    :param sqlconnection:
    :param accounts: a dictionary with keys are 'acc1', 'acc2',...
    :param uploadquery: the MySQL INSERT INTO query to execute.
    :return: None
    """
    for deliacc in accounts.values():
        try:
            is_run(os.getenv('RUN_JTE_EXCELETL'))
            name_deliveryorders = os.getenv(deliacc['deliveryorders'])
            if name_deliveryorders is None or name_deliveryorders == '':
                return_message('run_jte_exceletl', 'failed', 'the file path is None. There is nothing to load to datalake')
            else:
                accountname = deliacc['name']
                path_deliveryorders = str(EXCELDATASOURCEPATH / name_deliveryorders)
                checkpath_deliveryorders = deliacc['checkpath_deliveryorders']
                # Extract:
                jte_deliveryorders = extractorclasses.DeliveryOrdersExcelExtractor(
                    'JT Express',
                    path_deliveryorders,
                    configinfo['jte']['excel']['usecols']['deliveryorders'],
                    configinfo['jte']['excel']['usedtype']['deliveryorders'],
                    0,
                    accountname,
                    checkpath_deliveryorders
                )
                df_jte_deliveryorders = jte_deliveryorders.extractdata()
                # Clean:
                cleanjteorders = cleanerclasses.DeliveryOrdersJTEExcelCleaner(
                    configinfo['jte']['excel']['clean']['finalcols'],
                    df_jte_deliveryorders
                )
                jteorders_df = cleanjteorders.cleandata()
                jteorders_df = cleanerclasses.cleandatetime_df(
                    jteorders_df,
                    {'Thời gian tạo đơn':'%Y-%m-%d %H:%M', 'Thời gian lấy hàng':'%Y-%m-%d %H:%M', 'Thời gian ký nhận':'%Y-%m-%d %H:%M'},
                    to_datetime_param='format'
                )
                # Upload:
                loadjteorders = loaderclasses.DataframeToDatabaseLoader(
                    jteorders_df,
                    sqlconnection,
                    uploadquery,
                    currenttime
                )
                loadjteorders.loaddata()
                return_message('run_jte_exceletl', 'success', f"the ETL pipeline for the {accountname} account has run successfully!")
        except Exception as e:
            return_message('run_jte_exceletl', 'failed', f"the ETL pipeline for the {deliacc.get('name', 'WRONG AT CONFIG')} account has failed. Data have not been loaded to datalake", errormessage=e)


def run_spx_exceletl(sqlconnection):
    for deliacc in configinfo['spx']['excel']['path'].values():
        try:
            is_run(os.getenv('RUN_SPX_EXCELETL'))
            name_deliveryorders = os.getenv(deliacc['deliveryorders'])
            if name_deliveryorders is None or name_deliveryorders == '':
                return_message('run_spx_exceletl', 'failed', 'the file path is None. There is nothing to load to datalake')
            else:
                accountname = deliacc['name']
                path_deliveryorders = str(EXCELDATASOURCEPATH / name_deliveryorders)
                checkpath_deliveryorders = deliacc['checkpath_deliveryorders']
                # Extract:
                spx_deliveryorders = extractorclasses.DeliveryOrdersExcelExtractor(
                    'Shopee Express',
                    path_deliveryorders,
                    configinfo['spx']['excel']['usecols']['deliveryorders'],
                    configinfo['spx']['excel']['usedtype']['deliveryorders'],
                    3,
                    accountname,
                    checkpath_deliveryorders
                )
                df_spx_deliveryorders = spx_deliveryorders.extractdata()
                # Clean:
                cleanspxorders = cleanerclasses.DeliveryOrdersSPXExcelCleaner(
                    configinfo['spx']['excel']['clean']['finalcols'],
                    df_spx_deliveryorders
                )
                spxorders_df = cleanspxorders.cleandata()
                spxorders_df = cleanerclasses.cleandatetime_df(
                    spxorders_df,
                    {'Thời gian tạo đơn':'%Y-%m-%d %H:%M', 'Thời gian lấy hàng/gửi hàng':'%Y-%m-%d %H:%M', 'Thời gian giao hàng':'%Y-%m-%d %H:%M'},
                    to_datetime_param='format'
                )
                # Upload:
                loadspxorders = loaderclasses.DataframeToDatabaseLoader(
                    spxorders_df,
                    sqlconnection,
                    etltolake_query['deliveryorders'],
                    currenttime
                )
                loadspxorders.loaddata()
                return_message('run_spx_exceletl', 'success', f"the ETL pipeline for the {accountname} account has run successfully!")
        except Exception as e:
            return_message('run_spx_exceletl', 'failed', f"the ETL pipeline for the {deliacc.get('name', 'WRONG AT CONFIG')} account has failed. Data have not been loaded to datalake", errormessage=e)


def run_cusbank_apietl(sqlconnection):
    try:
        is_run(os.getenv('RUN_CUSBANK_APIETL'))
        idfile = os.getenv(configinfo['cusbank']['idfile'])
        idsheet = int(os.getenv(configinfo['cusbank']['idsheet']))
        # Extract:
        return_message('run_cusbank_apietl', 'neutral', f"retrive customer banking data from google sheet API (idfile: {idfile}, idsheet: {idsheet})")
        opensheet = extractorclasses.GoogleSheetExtractor(GGSERVICEKEY)
        df_cusbank = opensheet.extractdataframe(
            idfile,
            idsheet,
            configinfo['cusbank']['datarange'],
            configinfo['cusbank']['usecols']
        )
        # Clean:
        return_message('run_cusbank_apietl', 'neutral', 'clean customer banking data from google sheet API')
        cleancusbank = cleanerclasses.CustomerBankingAPICleaner(
            configinfo['cusbank']['finalcols'],
            df_cusbank
        )
        df_cusbank = cleancusbank.cleandata()
        df_cusbank = cleanerclasses.cleandatetime_df(
            df_cusbank,
            {'Ngày':'%d/%m/%Y'},
            to_datetime_param='format'
        )
        # Upload:
        return_message('run_cusbank_apietl', 'neutral', 'upload customer banking data from google sheet API on datalake')
        loadcusbank = loaderclasses.DataframeToDatabaseLoader(
            df_cusbank,
            sqlconnection,
            etltolake_query['customerbanks'],
            currenttime
        )
        loadcusbank.loaddata()
        return_message('run_cusbank_apietl', 'success', 'the ETL pipeline has run successfully!')
    except Exception as e:
        return_message('run_cusbank_apietl', 'failed', 'the ETL pipeline has failed. Data have not been loaded to datalake', errormessage=e)


def run_codtvc_apietl(sqlconnection):
    for source in configinfo['codtvc']['datasource'].values(): # source is a dictionary
        try:
            is_run(os.getenv('RUN_CODTVC_APIETL'))
            file = os.getenv(source['idfile'])
            sheet = int(os.getenv(source['idsheet']))
            # Extract:
            return_message('run_codtvc_apietl', 'neutral', f"retrieve codtvc data from google sheet API (idfile: {file}, idsheet: {sheet})")
            opensheet = extractorclasses.GoogleSheetExtractor(GGSERVICEKEY)
            df_codtvc = opensheet.extractdataframe(
                file,
                sheet,
                configinfo['codtvc']['datarange'],
                configinfo['codtvc']['usecols']
            )
            # Clean:
            return_message('run_codtvc_apietl', 'neutral', f"clean codtvc data from google sheet API (idfile: {file}, idsheet: {sheet})")
            cleancodtvc = cleanerclasses.CodTvcAPICleaner(
                configinfo['codtvc']['finalcols'],
                df_codtvc
            )
            df_codtvc = cleancodtvc.cleandata()
            df_codtvc = cleanerclasses.cleandatetime_df(
                df_codtvc,
                {'Ngày lên':'%d/%m/%Y', 'Ngày đi':'%d/%m/%Y'},
                to_datetime_param='format'
            )
            # Upload:
            return_message('run_codtvc_apietl', 'neutral', f"upload codtvc data from google sheet API (idfile: {file}, idsheet: {sheet}) on datalake")
            loadcodtvc = loaderclasses.DataframeToDatabaseLoader(
                df_codtvc,
                sqlconnection,
                etltolake_query['deliveryorders'],
                currenttime
            )
            loadcodtvc.loaddata()
            return_message('run_codtvc_apietl', 'success', f"the ETL pipeline (file {file}, sheet: {sheet}) has run successfully!")
        except Exception as e:
            return_message('run_codtvc_apietl', 'failed', f"the ETL pipeline for codtvc data in {source} has failed. Data have not been loaded to datalake. Note that some 'Tu Van Chuyen' orders may don't have their tracking number in the fact_orderdetails table", errormessage=e)


def run_internalprice_apietl(sqlconnection):
    try:
        is_run(os.getenv('RUN_INTERNALPRICE_APIETL'))
        idfile = os.getenv(configinfo['internalprice']['idfile'])
        idsheet = int(os.getenv(configinfo['internalprice']['idsheet']))
        # Extract:
        return_message('run_internalprice_apietl', 'neutral', f"retrieve internal price information of products using google sheet API (idfile: {idfile}, idsheet: {idsheet})")
        opensheet = extractorclasses.GoogleSheetExtractor(GGSERVICEKEY)
        df_internalprice = opensheet.extractdataframe(
            idfile,
            idsheet,
            configinfo['internalprice']['datarange'],
            configinfo['internalprice']['usecols']
        )
        # Clean:
        return_message('run_internalprice_apietl', 'neutral', 'clean internal price information of products using google sheet API')
        cleaninternalprice = cleanerclasses.InternalPriceAPICleaner(
            configinfo['internalprice']['finalcols'],
            df_internalprice
        )
        df_internalprice = cleaninternalprice.cleandata()
        # Upload:
        return_message('run_internalprice_apietl', 'neutral', 'upload internal price information of products using google sheet API on data warehouse')
        loadinterprice = loaderclasses.DataframeToDatabaseLoader(
            df_internalprice,
            sqlconnection,
            etltolake_query['dim_product'],
            currenttime,
            enable_updatetime='No'
        )
        loadinterprice.loaddata()
        return_message('run_internalprice_apietl', 'success', 'the ETL pipeline has run successfully!')
    except Exception as e:
        return_message('run_internalprice_apietl', 'failed', 'the ETL pipeline has failed. Data have not been loaded to datalake')


def run_returnedorderscan_apietl(sqlconnection):
    for source in configinfo['returnedorderscan']['datasource'].values(): # source is a dictionary
        try:
            is_run(os.getenv('RUN_RETURNEDORDERSCAN_APIETL'))
            idfile = os.getenv(source['idfile'])
            idsheet = int(os.getenv(source['idsheet']))
            # Extract:
            return_message('run_returnedorderscan_apietl', 'neutral', f"retrieve returned orders scanning data from google sheet API (idfile: {idfile}, idsheet: {idsheet})")
            opensheet = extractorclasses.GoogleSheetExtractor(GGSERVICEKEY)
            df_scanreturnedorder = opensheet.extractdataframe(
                idfile,
                idsheet,
                source['datarange'],
                source['usecols']
            )
            time.sleep(5)
            # Clean:
            return_message('run_returnedorderscan_apietl', 'neutral', 'clean returned orders scanning data from google sheet API')
            cleanscanreturnedorder = cleanerclasses.ReturnedOrdersScanTrackingNumberAPICleaner(
                configinfo['returnedorderscan']['finalcols'],
                df_scanreturnedorder,
                2026
            )
            df_scanreturnedorder = cleanscanreturnedorder.cleandata()
            df_scanreturnedorder = cleanerclasses.cleandatetime_df(
                df_scanreturnedorder,
                {'Ngày bắn':'%Y-%m-%d'},
                to_datetime_param='format'
            )
            # Upload:
            return_message('run_returnedorderscan_apietl', 'neutral', 'upload returned orders scanning data from google sheet API to datalake')
            loadreturnedorder = loaderclasses.DataframeToDatabaseLoader(
                df_scanreturnedorder,
                sqlconnection,
                etltolake_query['returnedorders_scan'],
                currenttime
            )
            loadreturnedorder.loaddata()
            return_message('run_returnedorderscan_apietl', 'success', f"the ETL pipeline for {idsheet} sheet has run successfully!")
        except Exception as e:
            return_message('run_returnedorderscan_apietl', 'failed', f"the ETL pipeline for (file: {source.get('idfile', 'WRONG AT CONFIG')}, sheet: {source.get('idsheet', 'WRONG AT CONFIG')}) has failed. Data have not been loaded to datalake", errormessage=e)


def run_deliveryorderscan_apietl(sqlconnection):
    try:
        is_run(os.getenv('RUN_DELIVERYORDERSCAN_APIETL'))
        idfile = os.getenv(configinfo['deliveryorderscan']['idfile'])
        idsheet = int(os.getenv(configinfo['deliveryorderscan']['idsheet']))
        # Extract:
        opensheet = extractorclasses.GoogleSheetExtractor(GGSERVICEKEY)
        df_scandeliveryorder = opensheet.extractdataframe(
            idfile,
            idsheet,
            configinfo['deliveryorderscan']['datarange'],
            configinfo['deliveryorderscan']['usecols']
        )
        # Clean:
        cleanscandeliveryorder = cleanerclasses.DeliveryOrdersScanTrackingNumberAPICleaner(
            configinfo['deliveryorderscan']['finalcols'],
            df_scandeliveryorder
        )
        df_scandeliveryorder = cleanscandeliveryorder.cleandata()
        df_scandeliveryorder = cleanerclasses.cleandatetime_df(
            df_scandeliveryorder,
            {'Ngày bắn đơn':'%Y-%m-%d'},
            to_datetime_param='format'
        )
        # Upload:
        loaddeliveryorder = loaderclasses.DataframeToDatabaseLoader(
            df_scandeliveryorder,
            sqlconnection,
            etltolake_query['handle_deliveryorders'],
            currenttime
        )
        loaddeliveryorder.loaddata()
        return_message('run_deliveryorderscan_apietl', 'success', 'the ETL pipeline has run successfully!')
    except Exception as e:
        return_message('run_deliveryorderscan_apietl', 'failed', 'the ETL pipeline has failed. Data have not been loaded to datalake', errormessage=e)


def run_deliveryordershandlingteam_apietl(sqlconnection):
    for source in configinfo['deliveryordershandlingteam']['datasource'].values(): # source is a dictionary
        try:
            is_run(os.getenv('RUN_DELIVERYORDERSHANDLINGTEAM_APIETL'))
            idfile = os.getenv(source['idfile'])
            idsheet = int(os.getenv(source['idsheet']))
            # Extract:
            return_message('run_deliveryordershandlingteam_apietl', 'neutral', f"retrieve note data of handling team using google sheet API (file: {idfile}, sheet: {idsheet})")
            opensheet = extractorclasses.GoogleSheetExtractor(GGSERVICEKEY)
            df_handleteam = opensheet.extractdataframe(
                idfile,
                idsheet,
                configinfo['deliveryordershandlingteam']['datarange'],
                configinfo['deliveryordershandlingteam']['usecols']
            )
            # Clean:
            return_message('run_deliveryordershandlingteam_apietl', 'neutral', f"clean note data of handling team using google sheet API (file: {idfile}, sheet: {idsheet})")
            cleanhandleteam = cleanerclasses.DeliveryOrdersHandlingTeamAPICleaner(
                configinfo['deliveryordershandlingteam']['finalcols'],
                df_handleteam
            )
            df_handleteam = cleanhandleteam.cleandata()
            # Upload
            return_message('run_deliveryordershandlingteam_apietl', 'neutral', f"upload note data of handling team using google sheet API on datalake (file: {idfile}, sheet: {idsheet})")
            loadhandleteam = loaderclasses.DataframeToDatabaseLoader(
                df_handleteam,
                sqlconnection,
                etltolake_query['handle_deliveryorders'],
                currenttime
            )
            loadhandleteam.loaddata()
            return_message('run_deliveryordershandlingteam_apietl', 'success', 'the ETL pipeline has run successfully!')
            time.sleep(5)
        except Exception as e:
            return_message('run_deliveryordershandlingteam_apietl', 'failed', f"the ETL pipeline for (file: {source.get('idfile', 'WRONG AT CONFIG')}, sheet: {source.get('idsheet', 'WRONG AT CONFIG')}) has failed. Data have not been loaded to datalake", errormessage=e)


def run_jtetransactions_exceletl(sqlconnection, information: dict, uploadquery: str, *, sessionid_outoftable = 'No'):
    """
    :param sqlconnection:
    :param information: a dictionary with keys are 'folderpath', 'check_filepath', 'usecols', 'usedtype'.
    :param uploadquery: the MySQL INSERT INTO query to execute.
    :param sessionid_outoftable: whether the session ID in the excel file is out of the table. Default as 'No', using 'Yes' if handling Mây By Mây JTE's transaction.
    :return: None
    """
    folder_name = os.getenv(information['folderpath'])
    if folder_name is None or folder_name == '':
        return_message('run_jtetransactions_exceletl', 'failed', 'the file path is None. There is nothing to load to datalake')
    else:
        listpath = glob.glob(str(EXCELDATASOURCEPATH / folder_name / '*')) # listpath is a list of strings, each string is a path of an excel file
        for path in listpath:
            try:
                is_run(os.getenv('RUN_JTETRANSACTIONS_EXCELETL'))
                if path.casefold().find('(') == -1:
                    # Extract:
                    jtetransac = extractorclasses.ExcelExtractor(
                        'JT Express',
                        path,
                        information['usecols'],
                        information['usedtype'],
                        information['skiprows'],
                        information['check_filepath']
                    )
                    df_jtetransac = jtetransac.extractdata()
                    if sessionid_outoftable != 'No':
                        infodf = pd.read_excel(path, header=None, usecols='B', skiprows=1, nrows=1)
                        sessionid = infodf.loc[0, 1]
                        df_jtetransac['Kỳ thanh toán'] = sessionid
                        df_jtetransac.rename(columns={'Số tiền phải trả sau cấn trừ':'Tiền thực nhận'}, inplace=True)
                    # Clean:
                    cleanjtetransac = cleanerclasses.TransactionsJTEExcelCleaner(
                        configinfo['transaction_jte']['excel']['finalcols'],
                        df_jtetransac
                    )
                    df_jtetransac = cleanjtetransac.cleandata()
                    # Upload:
                    loadjtetransac = loaderclasses.DataframeToDatabaseLoader(
                        df_jtetransac,
                        sqlconnection,
                        uploadquery,
                        currenttime
                    )
                    loadjtetransac.loaddata()
                    return_message('run_jtetransactions_exceletl', 'success', f"the ETL pipeline for the {path} filepath has run successfully!")
                else:
                    return_message('run_jtetransactions_exceletl', 'failed', f"The file path {path} contains '(' characters, data in this file won't be upload on database!")
            except Exception as e:
                return_message('run_jtetransactions_exceletl', 'failed', f"the ETL pipeline for the {path} filepath has failed. Data have not been loaded to datalake", errormessage=e)


def run_spxtransactions_exceletl(sqlconnection):
    folder_name = os.getenv(configinfo['transaction_spx']['excel']['folderpath'])
    if folder_name is None or folder_name == '':
        return_message('run_spxtransactions_exceletl', 'failed', 'the file path is None. There is nothing to load to datalake')
    else:
        listpath = glob.glob(str(EXCELDATASOURCEPATH / folder_name / '*')) # listpath is a list of strings, each string is a path of an excel file
        for path in listpath:
            try:
                is_run(os.getenv('RUN_SPXTRANSACTIONS_EXCELETL'))
                if path.casefold().find('(') == -1:
                    # Extract:
                    spxtransac = extractorclasses.ExcelExtractor(
                        'SPX Express',
                        path,
                        configinfo['transaction_spx']['excel']['usecols'],
                        configinfo['transaction_spx']['excel']['usedtype'],
                        0,
                        configinfo['transaction_spx']['excel']['check_filepath']
                    )
                    df_spxtransac = spxtransac.extractdata()
                    # Clean:
                    cleanspxtransac = cleanerclasses.TransactionsSPXExcelCleaner(
                        configinfo['transaction_spx']['excel']['finalcols'],
                        df_spxtransac
                    )
                    df_spxtransac = cleanspxtransac.cleandata()
                    df_spxtransac = cleanerclasses.cleandatetime_df(
                        df_spxtransac,
                        {'Thời gian giao dịch':'%Y/%m/%d %H:%M:%S'},
                        to_datetime_param='format'
                    )
                    # Upload:
                    loadspxtransac = loaderclasses.DataframeToDatabaseLoader(
                        df_spxtransac,
                        sqlconnection,
                        etltolake_query['delivery_reconciliation'],
                        currenttime
                    )
                    loadspxtransac.loaddata()
                    return_message('run_spxtransactions_exceletl', 'success', f"the ETL pipeline for the {path} filepath has run successfully!")
                else:
                    return_message('run_spxtransactions_exceletl', 'failed', f"The file path {path} contains '(' characters, data in this file won't be upload on database!")
            except Exception as e:
                return_message('run_spxtransactions_exceletl', 'failed', f"the ETL pipeline for the {path} filepath has failed. Data have not been loaded to datalake", errormessage=e)


def run_ghntransactions_exceletl(sqlconnection, information: dict, uploadquery: str):
    """
    :param sqlconnection:
    :param information: a dictionary with keys are 'folderpath', 'check_filepath', 'usecols', 'usedtype'.
    :param uploadquery: the MySQL INSERT INTO query to execute.
    :return: None
    """
    folder_name = os.getenv(information['folderpath'])
    if folder_name is None or folder_name == '':
        return_message('run_ghntransactions_exceletl', 'failed', 'the file path is None. There is nothing to load to datalake')
    else:
        listpath = glob.glob(str(EXCELDATASOURCEPATH / folder_name / '*'))  # listpath is a list of strings, each string is a path of an excel file
        for path in listpath:
            try:
                is_run(os.getenv('RUN_GHNTRANSACTIONS_EXCELETL'))
                if path.casefold().find('(') == -1:
                    # Extract:
                    infodf = pd.read_excel(path, header=None, usecols='A:B', skiprows=7, nrows=2)
                    ma_gd = infodf.loc[0,1]
                    ngay_gd = infodf.loc[1,1]
                    ghntransac = extractorclasses.ExcelExtractor(
                        'Giao Hang Nhanh',
                        path,
                        configinfo['transaction_ghn']['excel']['usecols'],
                        configinfo['transaction_ghn']['excel']['usedtype'],
                        20,
                        information['check_filepath']
                    )
                    df_ghntransac = ghntransac.extractdata()
                    # Clean:
                    cleanghntransac = cleanerclasses.TransactionsGHNExcelCleaner(
                        configinfo['transaction_ghn']['excel']['finalcols'],
                        df_ghntransac,
                        ma_gd,
                        ngay_gd
                    )
                    df_ghntransac = cleanghntransac.cleandata()
                    # Upload:
                    loadghntransac = loaderclasses.DataframeToDatabaseLoader(
                        df_ghntransac,
                        sqlconnection,
                        uploadquery,
                        currenttime
                    )
                    loadghntransac.loaddata()
                    return_message('run_ghntransactions_exceletl', 'success', f"the ETL pipeline for the {path} filepath has run successfully!")
                else:
                    return_message('run_ghntransactions_exceletl', 'failed', f"The file path {path} contains '(' characters, data in this file won't be upload on database!")
            except Exception as e:
                return_message('run_ghntransactions_exceletl', 'failed', f"the ETL pipeline for the {path} filepath has failed. Data have not been loaded to datalake", errormessage=e)


def run_ghncointransactions_exceletl(sqlconnection, information: dict, uploadquery: str):
    """
    :param sqlconnection:
    :param information: a dictionary with keys are 'folderpath', 'check_filepath', 'usecols', 'usedtype'.
    :param uploadquery: the MySQL INSERT INTO query to execute.
    :return: None
    """
    folder_name = os.getenv(information['folderpath'])
    if folder_name is None or folder_name == '':
        return_message('run_ghncointransactions_exceletl', 'failed', 'the file path is None. There is nothing to load to datalake')
    else:
        listpath = glob.glob(str(EXCELDATASOURCEPATH / folder_name / '*'))  # listpath is a list of strings, each string is a path of an excel file
        for path in listpath:
            try:
                is_run(os.getenv('RUN_GHNCOINTRANSACTIONS_EXCELETL'))
                if path.casefold().find('(') == -1:
                    # Extract:
                    ghncointransac = extractorclasses.ExcelExtractor(
                        'Giao Hang Nhanh',
                        path,
                        configinfo['cointransaction_ghn']['excel']['usecols'],
                        configinfo['cointransaction_ghn']['excel']['usedtype'],
                        2,
                        information['check_filepath']
                    )
                    df_ghncointransac = ghncointransac.extractdata()
                    # Clean:
                    cleanghncointransac = cleanerclasses.CoinTransactionsGHNExcelCleaner(
                        configinfo['cointransaction_ghn']['excel']['finalcols'],
                        df_ghncointransac
                    )
                    df_ghncointransac = cleanghncointransac.cleandata()
                    # Upload:
                    loadghncointrans = loaderclasses.DataframeToDatabaseLoader(
                        df_ghncointransac,
                        sqlconnection,
                        uploadquery,
                        currenttime
                    )
                    loadghncointrans.loaddata()
                    return_message('run_ghncointransactions_exceletl', 'success', f"the ETL pipeline for the {path} filepath has run successfully!")
                else:
                    return_message('run_ghncointransactions_exceletl', 'failed', f"The file path {path} contains '(' characters, data in this file won't be upload on database!")
            except Exception as e:
                return_message('run_ghncointransactions_exceletl', 'failed', f"the ETL pipeline for the {path} filepath has failed. Data have not been loaded to datalake", errormessage=e)


def run_nhanhvn_apietl(sqlconnection):
    try:
        is_run(os.getenv('RUN_NHANHVN_APIETL'))
        run_sqlscript(
            DELETERECORDS_NHANHVN_QUERYPATH,
            sqlconnection,
            params={'startdate': os.getenv(configinfo['nhanhvn']['api']['orders']['startdate']), 'enddate': os.getenv(configinfo['nhanhvn']['api']['orders']['enddate'])}
        )
    except Exception as e:
        return_message('run_nhanhvn_apietl', 'failed', 'the queries to delete records have failed! Stop this pipeline', errormessage=e)
    else:
        for nhanhvnacc in configinfo['nhanhvn']['account'].values():
            try:
                appid = os.getenv(nhanhvnacc['appid'])
                businessid = os.getenv(nhanhvnacc['businessid'])
                accesstoken = os.getenv(nhanhvnacc['accesstoken'])
                # Extract:
                return_message('run_nhanhvn_apietl', 'neutral', 'retrieve orders and orderdetails data from Nhanhvn Open API')
                nhanh = extractorclasses.NhanhvnOrdersAPIExtractor(
                    'https://pos.open.nhanh.vn/v3.0/order/list',
                    {'appId': appid, 'businessId': businessid},
                    {'Authorization': accesstoken, 'Content-Type': 'application/json'},
                    os.getenv(configinfo['nhanhvn']['api']['orders']['startdate']),
                    os.getenv(configinfo['nhanhvn']['api']['orders']['enddate']),
                    salechannel=[1, 10]
                )
                json_nhanh = nhanh.extractdata()
                # Clean:
                return_message('run_nhanhvn_apietl', 'neutral', 'clean orders and orderdetails data from Nhanhvn Open API')
                cleannhanh = cleanerclasses.OrdersNhanhvnAPICleaner(
                    configinfo['nhanhvn']['api']['orders']['orderfinalcols'],
                    configinfo['nhanhvn']['api']['orders']['orderdetailfinalcols'],
                    json_nhanh
                )
                df_orders = cleannhanh.cleandata()
                df_orderdetails = cleannhanh.cleandata_orderdetails()
                df_orders = cleanerclasses.cleandatetime_df(
                    df_orders,
                    {'Thoi gian':'s', 'Ngay gui HVC':'s'},
                    to_datetime_param='unit'
                )
                opensheet = extractorclasses.GoogleSheetExtractor(GGSERVICEKEY)
                idfile = os.getenv(configinfo['nhanhvn']['api']['orders']['codeexplain']['idfile'])
                idsheet = int(os.getenv(configinfo['nhanhvn']['api']['orders']['codeexplain']['idsheet']))
                orderstatus_des = opensheet.extractlist(
                    idfile,
                    idsheet,
                    configinfo['nhanhvn']['api']['orders']['codeexplain']['orderstatus']['datarange']
                )
                cleanerclasses.map_valuedf(df_orders, 'Trang thai', orderstatus_des)
                salechannel_des = opensheet.extractlist(
                    idfile,
                    idsheet,
                    configinfo['nhanhvn']['api']['orders']['codeexplain']['salechannel']['datarange']
                )
                cleanerclasses.map_valuedf(df_orders, 'Nen tang', salechannel_des)
                cityaddress_des = opensheet.extractlist(
                    idfile,
                    idsheet,
                    configinfo['nhanhvn']['api']['orders']['codeexplain']['cityaddress']['datarange']
                )
                cleanerclasses.map_valuedf(df_orders, 'Thanh pho', cityaddress_des)
                districtaddress_des = opensheet.extractlist(
                    idfile,
                    idsheet,
                    configinfo['nhanhvn']['api']['orders']['codeexplain']['districtaddress']['datarange']
                )
                cleanerclasses.map_valuedf(df_orders, 'Quan huyen', districtaddress_des)
                # Upload:
                return_message('run_nhanhvn_apietl', 'neutral', 'upload orders and orderdetails data from Nhanhvn Open API to datalake')
                loadorders = loaderclasses.DataframeToDatabaseLoader(
                    df_orders,
                    sqlconnection,
                    etltolake_query['nhanhvnorders'],
                    currenttime
                )
                loadorders.loaddata()
                loadorderdetails = loaderclasses.DataframeToDatabaseLoader(
                    df_orderdetails,
                    sqlconnection,
                    etltolake_query['nhanhvnorderdetails'],
                    currenttime
                )
                loadorderdetails.loaddata()
                return_message('run_nhanhvn_apietl', 'success', 'the whole ETL has run successfully!')
            except Exception as e:
                return_message('run_nhanhvn_apietl', 'failed', f"the ETL pipeline for {nhanhvnacc.get('appid', 'WRONG AT CONFIG')} appid has failed. Data have not been loaded to datalake", errormessage=e)


def run_tiktokincome_exceletl(sqlconnection):
    folder_name = os.getenv(configinfo['tiktok']['excel']['income']['folderpath'])
    if folder_name is None or folder_name == '':
        return_message('run_tiktokincome_exceletl', 'failed', 'the file path is None. There is nothing to load to datalake')
    else:
        listpath = glob.glob(str(EXCELDATASOURCEPATH / folder_name / '*'))  # listpath is a list of strings, each string is a path of an excel file
        for path in listpath:
            try:
                is_run(os.getenv('RUN_TIKTOKINCOME_EXCELETL'))
                # Extract:
                tiktokincome = extractorclasses.ExcelExtractor(
                    'Tiktok shops',
                    path,
                    configinfo['tiktok']['excel']['income']['finalcols'],
                    configinfo['tiktok']['excel']['income']['usedtype'],
                    0,
                    ['']
                )
                df_tiktokincome = tiktokincome.extractdata()
                # Clean:
                cleantiktokincome = cleanerclasses.IncomeTiktokExcelCleaner(
                    configinfo['tiktok']['excel']['income']['finalcols'],
                    df_tiktokincome
                )
                df_tiktokincome = cleantiktokincome.cleandata()
                df_tiktokincome = cleanerclasses.cleandatetime_df(
                    df_tiktokincome,
                    {'Thời gian quyết toán đơn hàng': '%Y/%m/%d'},
                    to_datetime_param='format'
                )
                # Upload:
                loadtiktokincome = loaderclasses.DataframeToDatabaseLoader(
                    df_tiktokincome,
                    sqlconnection,
                    etltolake_query['tiktok_reconciliation'],
                    currenttime
                )
                loadtiktokincome.loaddata()
                return_message('run_tiktokincome_exceletl', 'success', f"the whole ETL for the {path} filepath has run successfully!")
            except Exception as e:
                return_message('run_tiktokincome_exceletl', 'failed', f"the ETL pipeline for the {path} filepath has failed. Data have not been loaded to datalake", errormessage=e)


def run_pos_apietl(sqlconnection, config: dict, key: dict):
    """
    :param sqlconnection: the object that was born from the pymysql.connect() method
    :param config: a dictionary with keys are 'startdate', 'enddate', 'orderfinalcols', 'orderdetailfinalcols',... from pipelineconfig.yaml file
    :param key: a dictionary with keys are 'acc1', 'acc2',... from key.yaml file
    :return: None
    """
    try:
        is_run(os.getenv('RUN_POS_APIETL'))
        run_sqlscript(
            DELETERECORDS_MAYBYMAY_POSORDERS_QUERYPATH,
            sqlconnection,
            params={'startdate': os.getenv(config['startdate']), 'enddate': os.getenv(config['enddate'])}
        )
    except Exception as e:
        return_message('run_pos_apietl', 'failed', 'the queries to delete reocrds have failed! Stop this pipeline', errormessage=e)
    else:
        for posacc in key.values():
            try:
                shopid = os.getenv(posacc['shopid'])
                apikey = os.getenv(posacc['apikey'])
                # Extract:
                return_message('run_pos_apietl', 'neutral', 'retrieve orders and orderdetails data from POS API')
                pos = extractorclasses.PosOrdersAPIExtractor(
                    'https://pos.pages.fm/api/v1/shops/real_shop_id/orders',
                    'GET',
                    apikey,
                    shopid,
                    {'fields[]': ['id', 'status_history', 'shipping_address', 'items', 'shipping_fee', 'partner', 'status', 'prepaid', 'note', 'order_sources_name', 'page', 'account_name', 'creator', 'status_history', 'order_currency', 'total_discount'], 'page_size':60},
                    ['data'],
                    ['page_number'],
                    ['total_pages'],
                    os.getenv(config['startdate']),
                    os.getenv(config['enddate'])
                )
                json_pos = pos.extractdata() # json_pos is a list of dictionaries, each dictionary contains information of an order
                # Clean:
                return_message('run_pos_apietl', 'neutral', 'clean data from POS API')
                cleanpos = cleanerclasses.PosOrdersAPICleaner(
                    config['orderfinalcols'],
                    config['orderdetailfinalcols'],
                    json_pos
                )
                df_pos_orders = cleanpos.cleandata()
                df_pos_orderdetails = cleanpos.cleandata_orderdetails()
                df_pos_orders = cleanerclasses.cleandatetime_df(
                    df_pos_orders,
                    {'Thoi gian tao don':'%Y-%m-%dT%H:%M:%S', 'Thoi diem DVVC lay hang':'%Y-%m-%dT%H:%M:%S'},
                    to_datetime_param = 'formatGMT+0'
                )
                indexsheet = extractorclasses.GoogleSheetExtractor(GGSERVICEKEY)
                orderstatus_des = indexsheet.extractlist(
                    os.getenv(config['codeexplain']['idfile']),
                    int(os.getenv(config['codeexplain']['idsheet'])),
                    config['codeexplain']['orderstatus']['datarange']
                )
                cleanerclasses.map_valuedf(df_pos_orders, 'Trang thai', orderstatus_des)
                # Upload:
                return_message('run_pos_apietl', 'neutral', 'upload orders and orderdetails data from POS API to datalake')
                loadorders = loaderclasses.DataframeToDatabaseLoader(
                    df_pos_orders,
                    sqlconnection,
                    maybymay_etltolake_query['mbm_pos_orders'],
                    currenttime
                )
                loadorders.loaddata()
                loadorderdetails = loaderclasses.DataframeToDatabaseLoader(
                    df_pos_orderdetails,
                    sqlconnection,
                    maybymay_etltolake_query['mbm_pos_orderdetails'],
                    currenttime
                )
                loadorderdetails.loaddata()
                return_message('run_pos_apietl', 'success', 'the whole ETL has run successfully!')
            except Exception as e:
                return_message('run_pos_apietl', 'failed', f"the ETL pipeline for {posacc.get('shopid', 'WRONG AT CONFIG')} shopid has failed. Data have not been loaded to datalake", errormessage=e)


def run_mbmmetaads_apietl(sqlconnection):
    try:
        is_run(os.getenv('RUN_MBMMETAADS_APIETL'))
        run_sqlscript(DELETERECORDS_MAYBYMAY_METAADS_QUERYPATH, sqlconnection)
    except Exception as e:
        return_message('run_mbmmetaads_apietl', 'failed', 'the queries to delete reocrds have failed! Stop this pipeline', errormessage=e)
    else:
        try:
            idfile = os.getenv(configinfo['maybymay_metaads']['idfile'])
            idsheet = int(os.getenv(configinfo['maybymay_metaads']['idsheet']))
            # Extract:
            return_message('run_mbmmetaads_apietl', 'neutral', f"retrieve Meta ads information using google sheet API (idfile: {idfile}, idsheet: {idsheet})")
            opensheet = extractorclasses.GoogleSheetExtractor(GGSERVICEKEY)
            df_mbmmetaads = opensheet.extractdataframe(
                idfile,
                idsheet,
                configinfo['maybymay_metaads']['datarange'],
                configinfo['maybymay_metaads']['usecols']
            )
            # Clean:
            return_message('run_mbmmetaads_apietl', 'neutral', f"clean Meta ads data from google sheet API (idfile: {idfile}, idsheet: {idsheet})")
            cleansheet = cleanerclasses.MaybymayMetaadsAPICleaner(
                configinfo['maybymay_metaads']['finalcols'],
                df_mbmmetaads
            )
            df_mbmmetaads = cleansheet.cleandata()
            df_mbmmetaads = cleanerclasses.cleandatetime_df(
                df_mbmmetaads,
                {'Ngày':'%Y-%m-%d'}
            )
            # Upload:
            return_message('run_mbmmetaads_apietl', 'neutral', f"upload Meta ads data from google sheet API (idfile: {idfile}, idsheet: {idsheet}) onto data lake")
            loadmetaads = loaderclasses.DataframeToDatabaseLoader(
                df_mbmmetaads,
                sqlconnection,
                maybymay_etltolake_query['mbm_metaads'],
                currenttime
            )
            loadmetaads.loaddata()
            return_message('run_mbmmetaads_apietl', 'success', 'the ETL pipeline has run successfully!')
        except Exception as e:
            return_message('run_mbmmetaads_apietl', 'failed', 'the ETL pipeline has failed. Data have not been loaded to datalake', errormessage=e)


def run_mbmordertest_apietl(sqlconnection):
    try:
        is_run(os.getenv('RUN_MBMORDERTEST_APIETL'))
        idfile = os.getenv(configinfo['maybymay_testorders']['idfile'])
        idsheet = int(os.getenv(configinfo['maybymay_testorders']['idsheet']))
        # Extract:
        return_message('run_mbmordertest_apietl', 'neutral', f"retrieve test orders information using google sheet API (idfile: {idfile}, idsheet: {idsheet})")
        opensheet = extractorclasses.GoogleSheetExtractor(GGSERVICEKEY)
        df_mbmordertest = opensheet.extractdataframe(
            idfile,
            idsheet,
            configinfo['maybymay_testorders']['datarange'],
            configinfo['maybymay_testorders']['usecols']
        )
        # Clean:
        return_message('run_mbmordertest_apietl', 'neutral', f"clean test orders data from google sheet API (idfile: {idfile}, idsheet: {idsheet})")
        cleansheet = cleanerclasses.MaybymayOrdertestVer2APICleaner(
            configinfo['maybymay_testorders']['finalcols'],
            df_mbmordertest
        )
        df_mbmordertest = cleansheet.cleandata()
        df_mbmordertest = cleanerclasses.cleandatetime_df(
            df_mbmordertest,
            {'Ngày đặt hàng':'%d/%m/%Y %H:%M:%S'}
        )
        # Upload:
        return_message('run_mbmordertest_apietl', 'neutral', f"upload test orders data from google sheet API (idfile: {idfile}, idsheet: {idsheet}) onto data lake")
        loadtestorders = loaderclasses.DataframeToDatabaseLoader(
            df_mbmordertest,
            sqlconnection,
            maybymay_etltolake_query['mbm_testorders'],
            currenttime
        )
        loadtestorders.loaddata()
        return_message('run_mbmordertest_apietl', 'success', 'the whole ETL has run successfully!')
    except Exception as e:
        return_message('run_mbmordertest_apietl', 'failed', f"the ETL pipeline has failed. Data have not been loaded to datalake", errormessage=e)


def updatereport_googlesheet(sqlconnection, information):
    """
    :param sqlconnection:
    :param information: a dictionary with keys are 'googlesheet', 'params'
    :return: None
    """
    try:
        is_run(os.getenv('UPDATEREPORT_GOOGLESHEET'))
    except Exception as e:
        return_message('updatereport_googlesheet', 'failed', '', errormessage=e)
    else:
        updateinfo_object = extractorclasses.GoogleSheetExtractor(GGSERVICEKEY)
        updateinfo = updateinfo_object.extractlist(os.getenv(information['googlesheet']['idfile']), int(os.getenv(information['googlesheet']['idsheet'])), information['googlesheet']['datarange'])
        for report in updateinfo:
            try:
                if report[4] == 'YES':
                    dict_params = {}
                    for x,y in information['params'].items():
                        try:
                            y_new = int(os.getenv(y))
                        except:
                            y_new = os.getenv(y)
                        z = {x:y_new}
                        dict_params.update(z)
                    worksheet_report = updateinfo_object.extractsheet(report[1], report[2])
                    sheetloader = loaderclasses.DatabaseToSheetLoader(
                        sqlconnection,
                        report[5].format(**dict_params),
                        worksheet_report,
                        report[3]
                    )
                    sheetloader.loaddata()
                    return_message('updatereport_googlesheet', 'success', f"successfully updated the report: {report[0]}")
                    time.sleep(5)
                else:
                    continue
            except Exception as e:
                return_message('updatereport_googlesheet', 'failed', f"failed updated the report: {report[0]}", errormessage=e)