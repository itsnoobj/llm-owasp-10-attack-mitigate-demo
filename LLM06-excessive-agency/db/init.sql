-- Init script: creates two users with different permissions
-- admin_agent: full access (SELECT, INSERT, UPDATE, DELETE, DROP)
-- readonly_agent: SELECT only

CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT, email TEXT, role TEXT);
INSERT INTO users VALUES (1,'Alice Chen','alice@acme.com','admin'),
  (2,'Bob Smith','bob@acme.com','user'),
  (3,'Carol Davis','carol@acme.com','user'),
  (4,'Dave Wilson','dave@acme.com','manager');

CREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INTEGER, product TEXT, amount REAL);
INSERT INTO orders VALUES (1,1,'Enterprise License',49999.99),(2,2,'Pro Plan',299.00),(3,3,'Starter Plan',49.00);

CREATE TABLE payments (id SERIAL PRIMARY KEY, order_id INTEGER, status TEXT, card_last4 TEXT);
INSERT INTO payments VALUES (1,1,'completed','4242'),(2,2,'completed','1234'),(3,3,'pending','5678');

CREATE TABLE audit_log (id SERIAL PRIMARY KEY, action TEXT, ts TEXT);
INSERT INTO audit_log VALUES (1,'user_login: alice','2025-04-15 09:00'),(2,'order_created: #1','2025-04-15 09:15');

-- Admin agent: full power
CREATE USER admin_agent WITH PASSWORD 'admin123';
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin_agent;
GRANT ALL PRIVILEGES ON SCHEMA public TO admin_agent;
ALTER USER admin_agent CREATEDB;

-- Readonly agent: SELECT only
CREATE USER readonly_agent WITH PASSWORD 'readonly123';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_agent;
