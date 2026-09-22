CREATE DATABASE mydudw;
USE mydudw;


-- DATALAKE TABLES:

create table nhanhvnorders (
	orderid varchar(40) not null primary key,
	created_at datetime,
	customername varchar(200),
	customerphonenumber varchar(40),
	customer_cityaddress varchar(60),
	customer_districtaddress varchar(60),
	deliverybrand varchar(40),
	trackingnumber varchar(40),
	orderstatus varchar(40),
	orderparentsource varchar(40),
	ordersource varchar(100),
	platform varchar(40),
	senddelivery_at datetime,
	cod_prepaid int,
	created_byperson varchar(60),
	internalnote varchar(255),
	customernote varchar(255),
	previousid_internalnote varchar(40),
	previousid_customernote varchar(40),
	is_wrongproduct boolean,
	dw_updatedat datetime not null
);

create table nhanhvnorderdetails (
	productid varchar(40) not null, -- for products haven't been created in the Product tab, they will show '' (empty string) value
	orderid varchar(40) not null,
	productbarcode varchar(40),
	parentproductid varchar(40),
	price int,
	discount_allproduct int,
	quantity int,
	dw_updatedat datetime not null,
	primary key (orderid, productid)
);

create table deliveryorders (
    delivery_orderid varchar(40) not null primary key,
    shop_orderid varchar(40),
    orderstatus varchar(40),
    cod_collected int,
    cod_declared int,
    shippingcost int,
    createdat datetime,
    pickupat datetime,
    completedat datetime,
    courier varchar(40),
    compensationvalue int,
    courieraccount varchar(40),
    dw_updatedat datetime not null
);

create table customerbanks (
    bank_surrogateid varchar(40) not null primary key,
    notedate date,
    orderid varchar(160),
    customerphonenumber varchar(40),
    bankvalue int,
    verifybyperson varchar(40),
    ftcode varchar(40),
    note varchar(255),
    dw_updatedat datetime not null,
    index idx_orderid (orderid)
);

create table returnedorders_scan (
    scan_surrogateid varchar(40) not null primary key,
    scanat date,
    delivery_orderid varchar(40),
    productid varchar(40),
    dw_updatedat datetime not null,
    index idx_delivery_orderid (delivery_orderid)
);

create table delivery_reconciliation (
    sessionid varchar(60) not null,
    delivery_orderid varchar(100) not null,
    reconciliation_value int,
    reconciliation_at datetime,
    courier varchar(40),
    reconciliation_content varchar(255),
    dw_updatedat datetime not null,
    primary key (delivery_orderid, sessionid)
);

create table handle_deliveryorders (
    delivery_orderid varchar(40) not null primary key,
    scan_deliveryorder_at date,
    handleteam_note1 varchar(255),
    handleteam_note2 varchar(255),
    handleteam_note3 varchar(255),
    dw_updatedat datetime not null
);

create table shopeeorders (
    orderid varchar(40) not null primary key,
    packageid varchar(40),
    courier varchar(40),
    createdat datetime,
    pickupat datetime,
    completedat datetime,
    orderstatus varchar(40),
    cancel_reason varchar(255),
    buyer_accountname varchar(255),
    returned_orderids varchar(255),
    buyer_paymentmethod varchar(100),
    collectedvalue_theory int,
    buyerpaidvalue int,
    shippingcost int,
    shippingcostdiscounted_byplatform int,
    shippingcostdiscounted_byseller int,
    delivery_orderid varchar(40),
    shopname varchar(160),
    dw_updatedat datetime not null
);

create table shopeeorderdetails (
    orderid varchar(40) not null,
    product_skuid varchar(40) not null,
    orderproduct_id varchar(100) not null,
    productid varchar(40),
    productname varchar(255),
    product_skuname varchar(255),
    quantity int,
    displayprice int,
    realprice int,
    shopdiscount_allquantities int,
    shopeediscount_allquantities int,
    return_quantity int,
    dw_updatedat datetime not null,
    primary key (orderid, product_skuid, orderproduct_id)
);

create table tiktokorders (
    orderid varchar(40) not null primary key,
    create_time datetime,
    collection_time datetime,
    delivery_time datetime,
    cancel_time datetime,
    status varchar(40),
    cancel_reason varchar(200),
    buyer_email varchar(160),
    payment_method_name varchar(100),
    original_shipping_fee int,
    actual_shipping_fee int,
    shipping_fee_platform_discount int,
    shipping_fee_seller_discount int,
    tracking_number varchar(40),
    shipping_provider varchar(60),
    buyeraddress_lv0 varchar(60),
    buyeraddress_lv1 varchar(60),
    buyeraddress_lv2 varchar(80),
    return_reason varchar(200),
    returned_trackingnumber varchar(50),
    returnstatus varchar(40),
    returnshippingfee_paidbybuyer int,
    returnshippingfee_paidbyplatform int,
    returnshippingfee_paidbyseller int,
    shopname varchar(160),
    dw_updatedat datetime not null
);

create table tiktokorderdetails (
    orderid varchar(40) not null,
    product_skuid varchar(40) not null,
    productid varchar(40),
    productname varchar(255),
    product_skuname varchar(255),
    displayprice int,
    quantity int,
    shopdiscount_allquantities int,
    tiktokdiscount_allquantities int,
    dw_updatedat datetime not null,
    primary key (orderid, product_skuid)
);

create table tiktok_reconciliation (
    order_or_statement_id varchar(40) not null,
    transactiontime date not null,
    transactiontype varchar(40),
    settlement_amount int,
    revenue int,
    subtotal_after_discount int,
    subtotal_before_discount int,
    seller_discount int,
    refund_subtotal_after_discount int,
    refund_subtotal_before_discount int,
    refundforseller_amount int,
    totalfee int,
    dw_updatedat datetime not null,
    primary key (order_or_statement_id, transactiontime)
);

create table dwtable_updatetime_log (
    dwtable_name varchar(160),
    updatetime datetime, -- updatetime show the last time the final record are inserted into the table
    primary key (dwtable_name, updatetime)
);

create table pipelines_runtime_log (
    logid int auto_increment primary key,
    runtime datetime,
    message varchar(2000),
    printtype varchar(60)
);


-- DATA WAREHOUSE TABLES:

create table dim_order (
    orderid varchar(40) not null primary key,
    createdat datetime,
    status varchar(60),
    parentsource varchar(40),
    source varchar(100),
    platform varchar(60),
    created_byperson varchar(60),
    cancel_reason varchar(255),
    returnid varchar(60),
    return_reason varchar(255),
    return_status varchar(255),
    is_wrongproduct boolean,
    lastupdateat datetime
);

create table dim_delivery (
    trackingnumber varchar(40) not null primary key,
    courier varchar(40),
    courieraccount varchar(40),
    delivery_status varchar(60),
    createdat datetime,
    pickupat datetime,
    deliveryat datetime,
    scan_deliveryorder_at date,
    handleteam_note1 varchar(255),
    handleteam_note2 varchar(255),
    handleteam_note3 varchar(255),
    lastupdateat datetime
);

create table dim_customer (
    customer_surrogateid varchar(160) not null primary key, -- created by concat phonenumber & ecommerce_name & city
    phonenumber varchar(40),
    name varchar(200),
    ecommerce_name varchar(60),
    country varchar(60),
    city varchar(60),
    district varchar(80)
);

create table dim_product (
    productid varchar(40) not null primary key,
    retailprice int,
    cate_purpose varchar(60),
    cate_color varchar(60),
    cate_fabric varchar(60),
    cate_collar varchar(60),
    cate_sleeve varchar(60),
    cate_sleevelong varchar(60),
    cate_dresstype varchar(60),
    cate_fabricpattern varchar(60)
);

create table dim_reconciliation (
    order_or_delivery_id varchar(160) not null primary key, -- grouped by delivery_orderid
    max_transactiontime datetime,
    min_transactiontime datetime,
    all_sessionid varchar(255),
    all_transactiontime varchar(255),
    allcontent varchar(255)
);

create table fact_orderdetails (
    orderid varchar(40) not null,
    productid varchar(40) not null,
    parentproductid varchar(40) not null,
    deliveryid varchar(40),
    customer_surrogateid varchar(160) not null,
    transaction_orderid varchar(40),
    baseorder_shippingfee int, -- this metrics is the grain for an order, need to calculate for the (order, product) grain later
    baseorder_cod_collected_allquantity int, -- this metrics is the grain for an order, need to calculate for the (order, product) grain later
    baseorder_codbank_collected_allquantity int, -- this metrics is the grain for an order, need to calculate for the (order, product) grain later
    baseorder_codprepaid_allquantity int, -- this metrics is the grain for an order, need to calculate for the (order, product) grain later
    baseorder_positive_reconciliation_allquantity int, -- this metrics is the grain for an order, need to calculate for the (order, product) grain later
    baseorder_negative_reconciliation_allquantity int, -- this metrics is the grain for an order, need to calculate for the (order, product) grain later
    shippingfee decimal(25,10),
    quantity int,
    originalprice int,
    discountamount_allquantity int,
    extradiscountamount_allquantity decimal(25,10),
    cod_collected_allquantity decimal(25,10), -- cod_collected is the amount that delivery has collected from customer (Nhanhvn orders) or the amount that showed in tiktok/shopeeorderdetails table (e-commerce orders)
    codbank_collected_allquantity decimal(25,10), -- codbank_collected only counts on Nhanhvn orders
    codprepaid_allquantity decimal(25,10), -- codprepaid only counts on Nhanhvn orders
    return_quantity int,
    positive_reconciliation_allquantity decimal(25,10),
    negative_reconciliation_allquantity decimal(25,10),
    finalstatus varchar(40),
    lastupdateat datetime,
    primary key (orderid, productid),
    constraint fk_order foreign key (orderid) references dim_order(orderid),
    constraint fk_delivery foreign key (deliveryid) references dim_delivery(trackingnumber),
    constraint fk_customer foreign key (customer_surrogateid) references dim_customer(customer_surrogateid),
    constraint fk_product foreign key (parentproductid) references dim_product(productid),
    constraint fk_reconciliation foreign key (transaction_orderid) references dim_reconciliation(order_or_delivery_id)
);