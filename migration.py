from DB import DB

DB.query("""create table if not exists admins(
         id       int(255)     not null primary key,
         is_admin tinyint(3)   not null,
         alias    varchar(255) not null)"""
         )
if len(DB.query("""SELECT * FROM admins WHERE id = %s""", (413081486,))) == 0:
    DB.query("""INSERT INTO admins (id, is_admin, alias) VALUES (%s, %s, %s)""", (413081486, 1, 'Алексей Голованов'))

DB.query("""create table if not exists  categories(
         id   int(255) auto_increment primary key,
         name varchar(32) null)"""
         )

DB.query("""create table if not exists subcategories(
         id            int(255) auto_increment primary key,
         name          varchar(255)            not null,
         parent_cat_id int(255)                not null,
         charge_type   int(255)     default 0  not null,
         charge        varchar(255) default '' not null)"""
         )

DB.query("""CREATE TABLE if not exists currency(
        id int(255) auto_increment primary key,
        name varchar(255) not null,
        value varchar(255) not null
)""")

if len(DB.query("""SELECT * FROM currency WHERE name = %s""", ('CNY',))) == 0:
    DB.query("""INSERT INTO currency (id, name, value) VALUES (%s, %s, %s)""", (None, 'CNY', '11.3'))
