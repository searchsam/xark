CREATE TABLE xark_status(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	create_at INTEGER,
	sync_status BOOLEAN,
	collect_status BOOLEAN,
	sync_date DATETIME,
	collect_date DATETIME
);

CREATE TABLE data_xo(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	serial_num VARCHAR,
	uuid VARCHAR,
	create_at DATETIME,
	update_at DATETIME
);
