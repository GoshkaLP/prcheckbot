CREATE TABLE Logs (
    id SERIAL,
    user_id VARCHAR(255),
    username VARCHAR(255),
    search_string VARCHAR(255),
    after_date VARCHAR(255),
    before_date VARCHAR(255),
    PRIMARY KEY (id)
);

CREATE TABLE Users (
    id SERIAL,
    user_id VARCHAR(255),
    token VARCHAR(255),
    allow BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (id)
)
CREATE TABLE Proxy (
    id SERIAL,
    proxy_url VARCHAR(255),
    PRIMARY KEY (id)
);