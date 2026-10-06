


CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(150) UNIQUE,
    country VARCHAR(100),
    signup_date DATE NOT NULL
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(100),
    price NUMERIC(10,2) NOT NULL
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    order_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL,
    total_amount NUMERIC(10,2) NOT NULL
);

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10,2) NOT NULL
);


INSERT INTO customers
(first_name, last_name, email, country, signup_date)
VALUES
('Alice', 'Martin', 'alice@example.com', 'France', '2025-01-10'),
('Lucas', 'Bernard', 'lucas@example.com', 'France', '2025-02-12'),
('Emma', 'Schmidt', 'emma@example.com', 'Germany', '2025-03-05'),
('Noah', 'Wilson', 'noah@example.com', 'UK', '2025-04-20'),
('Sofia', 'Rossi', 'sofia@example.com', 'Italy', '2025-05-15');


INSERT INTO products
(name, category, price)
VALUES
('Laptop Pro', 'Electronics', 1499.00),
('Wireless Mouse', 'Electronics', 49.90),
('Office Chair', 'Furniture', 299.00),
('Standing Desk', 'Furniture', 599.00),
('Mechanical Keyboard', 'Electronics', 129.00);


INSERT INTO orders
(customer_id, order_date, status, total_amount)
VALUES
(1, '2026-01-05', 'completed', 1548.90),
(2, '2026-01-10', 'completed', 299.00),
(1, '2026-02-03', 'completed', 599.00),
(3, '2026-02-15', 'completed', 1628.00),
(4, '2026-03-01', 'cancelled', 49.90),
(5, '2026-03-12', 'completed', 728.00),
(2, '2026-04-08', 'completed', 1499.00);


INSERT INTO order_items
(order_id, product_id, quantity, unit_price)
VALUES
(1, 1, 1, 1499.00),
(1, 2, 1, 49.90),

(2, 3, 1, 299.00),

(3, 4, 1, 599.00),

(4, 1, 1, 1499.00),
(4, 5, 1, 129.00),

(5, 2, 1, 49.90),

(6, 4, 1, 599.00),
(6, 5, 1, 129.00),

(7, 1, 1, 1499.00);


CREATE USER text2sql_reader WITH PASSWORD 'reader_password';

GRANT CONNECT ON DATABASE analytics TO text2sql_reader;
GRANT USAGE ON SCHEMA public TO text2sql_reader;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO text2sql_reader;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT ON TABLES TO text2sql_reader;