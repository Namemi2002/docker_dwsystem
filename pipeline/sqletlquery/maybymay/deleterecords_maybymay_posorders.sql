delete from mbm_pos_orderdetails
where id in (
    select id from mbm_pos_orders
    where (orderstatus = 'new' or orderstatus = 'waiting for confirmation' or orderstatus = 'restocking' or orderstatus = 'wait for printing' or orderstatus = 'printed') and createdat >= '{startdate}' and createdat <= '{enddate}'
);
delete from mbm_pos_orders
where (orderstatus = 'new' or orderstatus = 'waiting for confirmation' or orderstatus = 'restocking' or orderstatus = 'wait for printing' or orderstatus = 'printed') and createdat >= '{startdate}' and createdat <= '{enddate}';