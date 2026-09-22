CREATE DATABASE maybymaydw;
USE maybymaydw;


create table mbm_pos_orders (
    id varchar(40) not null primary key,
    createdat datetime,
	customername varchar(200),
	customerphonenumber varchar(40),
	customer_countryaddress varchar(60),
	customer_cityaddress varchar(60),
	customer_districtaddress varchar(60),
	customer_communeaddress varchar(60),
	shippingfee_customerpaid int,
	courier varchar(40),
	trackingnumber varchar(40),
	orderstatus varchar(40),
	pickedupat datetime,
	totaldiscount int,
	prepaid int,
	platform varchar(40),
	parentsource varchar(40),
	source varchar(100),
	idfb_createdbyperson varchar(60),
	createdbyperson varchar(60),
	idfb_confirmedbyperson varchar(60),
	confirmedbyperson varchar(60),
	currency varchar(40),
	internal_note varchar(255),
	previous_ID varchar(40),
	dw_updatedat datetime not null
);

create table mbm_pos_orderdetails (
    id varchar(40) not null,
    parentproductid varchar(40),
    productid varchar(40) not null,
    price int,
    discount1product int,
    quantity int,
    dw_updatedat datetime not null,
    primary key (id, productid)
);

create table mbm_deliveryorders (
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

create table mbm_metaads (
    days date not null,
    campaignid varchar(40) not null,
    accountid varchar(40) not null,
    accountname varchar(160),
    campainname varchar(160),
    campain_distribution varchar(40),
    spending int,
    numbof_comment int,
    numbof_inbox int,
    numbof_purchase int,
    purchase_conversion_value int,
    budget int,
    pagename varchar(100),
    marketing_person varchar(60),
    parentproductid varchar(40),
    dw_updatedat datetime not null,
    primary key (days, accountid, campaignid)
);

create table mbm_testorders (
    customer_phonenumber varchar(100) not null,
    testproductid varchar(40) not null,
    productsize varchar(20) not null,
    pagename varchar(100) not null,
    orderdate datetime,
    customer_fbname varchar(60),
    ordervalue int,
    dw_updatedat datetime not null,
    primary key (customer_phonenumber, testproductid, productsize, pagename)
);

create table mbm_delivery_reconciliation (
    sessionid varchar(60) not null,
    delivery_orderid varchar(100) not null,
    reconciliation_value int,
    reconciliation_at datetime,
    courier varchar(40),
    reconciliation_content varchar(255),
    dw_updatedat datetime not null,
    primary key (delivery_orderid, sessionid)
);

create table pipelines_runtime_log (
    logid int auto_increment primary key,
    runtime datetime,
    message varchar(2000),
    printtype varchar(60)
);