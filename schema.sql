DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS cuts;
DROP TABLE IF EXISTS saved_plans;

CREATE TABLE suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE species (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE qualities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    species_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    length INTEGER NOT NULL,
    height INTEGER NOT NULL,
    width INTEGER NOT NULL,
    price REAL NOT NULL,
    link TEXT,
    quality_id INTEGER,
    FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
    FOREIGN KEY (species_id) REFERENCES species (id),
    FOREIGN KEY (quality_id) REFERENCES qualities (id)
);

CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cuts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    species_id INTEGER,
    label TEXT NOT NULL,
    length INTEGER NOT NULL,
    width INTEGER NOT NULL,
    depth INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    quality_id INTEGER,
    FOREIGN KEY (project_id) REFERENCES projects (id),
    FOREIGN KEY (species_id) REFERENCES species (id),
    FOREIGN KEY (quality_id) REFERENCES qualities (id)
);

CREATE TABLE saved_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    plan_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id)
);