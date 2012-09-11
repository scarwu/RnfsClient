CREATE TABLE cache (
	path TEXT NOT NULL,
	type TEXT NOT NULL,
	size INTEGER,
	hash TEXT,
	version INTEGER
);

CREATE TABLE local (
	path TEXT NOT NULL,
	type TEXT NOT NULL,
	size INTEGER,
	hash TEXT,
	version INTEGER
);

CREATE TABLE server (
	path TEXT NOT NULL,
	type TEXT NOT NULL,
	size INTEGER,
	hash TEXT,
	version INTEGER
);
