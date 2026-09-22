-- IMPORTANT REMINDER: ALL QUERY IN THIS FILE MUST START WITH "--name: table_name"
--name: mbm_pos_orders
insert into mbm_pos_orders
values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
as new
on duplicate key update
    mbm_pos_orders.createdat = new.createdat,
    mbm_pos_orders.customername = new.customername,
    mbm_pos_orders.customerphonenumber = new.customerphonenumber,
    mbm_pos_orders.customer_countryaddress = new.customer_countryaddress,
    mbm_pos_orders.customer_cityaddress = new.customer_cityaddress,
    mbm_pos_orders.customer_districtaddress = new.customer_districtaddress,
    mbm_pos_orders.customer_communeaddress = new.customer_communeaddress,
    mbm_pos_orders.shippingfee_customerpaid = new.shippingfee_customerpaid,
    mbm_pos_orders.courier = new.courier,
    mbm_pos_orders.trackingnumber = new.trackingnumber,
    mbm_pos_orders.orderstatus = new.orderstatus,
    mbm_pos_orders.pickedupat = new.pickedupat,
    mbm_pos_orders.totaldiscount = new.totaldiscount,
    mbm_pos_orders.prepaid = new.prepaid,
    mbm_pos_orders.platform = new.platform,
    mbm_pos_orders.parentsource = new.parentsource,
    mbm_pos_orders.source = new.source,
    mbm_pos_orders.idfb_createdbyperson = new.idfb_createdbyperson,
    mbm_pos_orders.createdbyperson = new.createdbyperson,
    mbm_pos_orders.idfb_confirmedbyperson = new.idfb_confirmedbyperson,
    mbm_pos_orders.confirmedbyperson = new.confirmedbyperson,
    mbm_pos_orders.currency = new.currency,
    mbm_pos_orders.internal_note = new.internal_note,
    mbm_pos_orders.previous_ID = new.previous_ID,
    mbm_pos_orders.dw_updatedat = new.dw_updatedat;

--name: mbm_pos_orderdetails
insert into mbm_pos_orderdetails
values (%s,%s,%s,%s,%s,%s,%s)
as new
on duplicate key update
    mbm_pos_orderdetails.parentproductid = new.parentproductid,
    mbm_pos_orderdetails.price = new.price,
    mbm_pos_orderdetails.discount1product = new.discount1product,
    mbm_pos_orderdetails.quantity = new.quantity,
    mbm_pos_orderdetails.dw_updatedat = new.dw_updatedat;

--name: mbm_deliveryorders
insert into mbm_deliveryorders
values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
as new
on duplicate key update
    mbm_deliveryorders.shop_orderid = new.shop_orderid,
    mbm_deliveryorders.orderstatus = new.orderstatus,
    mbm_deliveryorders.cod_collected = new.cod_collected,
    mbm_deliveryorders.cod_declared = new.cod_declared,
    mbm_deliveryorders.shippingcost = new.shippingcost,
    mbm_deliveryorders.createdat = new.createdat,
    mbm_deliveryorders.pickupat = new.pickupat,
    mbm_deliveryorders.completedat = new.completedat,
    mbm_deliveryorders.courier = new.courier,
    mbm_deliveryorders.compensationvalue = new.compensationvalue,
    mbm_deliveryorders.courieraccount = new.courieraccount,
    mbm_deliveryorders.dw_updatedat = new.dw_updatedat;

--name: mbm_metaads
insert into mbm_metaads
values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
as new
on duplicate key update
    mbm_metaads.accountname = new.accountname,
    mbm_metaads.campainname = new.campainname,
    mbm_metaads.campain_distribution = new.campain_distribution,
    mbm_metaads.spending = new.spending,
    mbm_metaads.numbof_comment = new.numbof_comment,
    mbm_metaads.numbof_inbox = new.numbof_inbox,
    mbm_metaads.numbof_purchase = new.numbof_purchase,
    mbm_metaads.purchase_conversion_value = new.purchase_conversion_value,
    mbm_metaads.budget = new.budget,
    mbm_metaads.pagename = new.pagename,
    mbm_metaads.marketing_person = new.marketing_person,
    mbm_metaads.parentproductid = new.parentproductid,
    mbm_metaads.dw_updatedat = new.dw_updatedat;

--name: mbm_testorders
insert into mbm_testorders
values (%s,%s,%s,%s,%s,%s,%s,%s)
as new
on duplicate key update
    mbm_testorders.orderdate = new.orderdate,
    mbm_testorders.customer_fbname = new.customer_fbname,
    mbm_testorders.ordervalue = new.ordervalue,
    mbm_testorders.dw_updatedat = new.dw_updatedat;

--name: mbm_delivery_reconciliation
insert into mbm_delivery_reconciliation
values (%s,%s,%s,%s,%s,%s,%s)
as new
on duplicate key update
    mbm_delivery_reconciliation.reconciliation_value = new.reconciliation_value,
    mbm_delivery_reconciliation.reconciliation_at = new.reconciliation_at,
    mbm_delivery_reconciliation.courier = new.courier,
    mbm_delivery_reconciliation.reconciliation_content = new.reconciliation_content,
    mbm_delivery_reconciliation.dw_updatedat = new.dw_updatedat;