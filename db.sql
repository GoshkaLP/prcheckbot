DROP TABLE Users;
CREATE TABLE Users (
    id SERIAL,
    user_id VARCHAR(255),
    mes_status INT,
    search_string VARCHAR(255),
    after_date VARCHAR(255),
    before_date VARCHAR(255),
    PRIMARY KEY (id)
);