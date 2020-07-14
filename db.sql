CREATE TABLE Users (
    id SERIAL,
    user_id VARCHAR(255),
    search_string VARCHAR(255),
    after_date VARCHAR(255),
    before_date VARCHAR(255),
    country VARCHAR(255),
    language VARCHAR(255),
    PRIMARY KEY (id)
);

CREATE TABLE Proxy (
    id SERIAL,
    proxy_url VARCHAR(255),
    PRIMARY KEY (id)
);

CREATE TABLE Countries (
    id SERIAL,
    country VARCHAR(255),
    country_code VARCHAR(255),
    PRIMARY KEY (id)
);

CREATE TABLE Languages (
    id SERIAL,
    language VARCHAR(255),
    language_code VARCHAR(255),
    PRIMARY KEY (id)
);
