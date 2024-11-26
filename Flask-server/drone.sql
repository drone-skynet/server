
USE drone;

CREATE TABLE `station` (
    `station_id` VARCHAR(50) NOT NULL,
    `station_name` VARCHAR(100) NOT NULL UNIQUE,
    `station_longitude` DECIMAL(9, 6) NOT NULL COMMENT 'XXX.XXXXXX°',
    `station_latitude` DECIMAL(9, 6) NOT NULL COMMENT 'XXX.XXXXXX°',
    `capacity` INT NOT NULL DEFAULT 5 COMMENT 'Station capacity',
    `grid_x` INT NULL COMMENT 'Grid X coordinate',
    `grid_y` INT NULL COMMENT 'Grid Y coordinate',
    PRIMARY KEY (`station_id`) 
);

CREATE TABLE `delivery` (
    `delivery_id` VARCHAR(50) NOT NULL,
    `origin_station_id` VARCHAR(50) NOT NULL,
    `destination_station_id` VARCHAR(50) NOT NULL,
    `delivery_status` VARCHAR(20) NOT NULL DEFAULT 'pending',
    `entire_arrival_time` TIMESTAMP NOT NULL,
    `arrival_time` TIMESTAMP NOT NULL,
    PRIMARY KEY (`delivery_id`),
    FOREIGN KEY (`origin_station_id`) REFERENCES `station`(`station_id`),
    FOREIGN KEY (`destination_station_id`) REFERENCES `station`(`station_id`)
);

CREATE TABLE `drone` (
    `drone_id` VARCHAR(50),
    `delivery_id` VARCHAR(50) NOT NULL,
    `drone_status` ENUM('available', 'in-flight', 'maintenance') NOT NULL DEFAULT 'available',
    `longitude` DECIMAL(9, 6) NOT NULL COMMENT 'XXX.XXXXXX°',
    `latitude` DECIMAL(9, 6) NOT NULL COMMENT 'XXX.XXXXXX°',
    `battery` INT NOT NULL DEFAULT 100 COMMENT '0% ~ 100%',
    `last_update_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`drone_id`),
    FOREIGN KEY (`delivery_id`) REFERENCES `delivery`(`delivery_id`)
);





CREATE TABLE `no_fly_zones` (
    `zone_id` VARCHAR(50) NOT NULL,
    `zone_name` VARCHAR(100) NOT NULL,
    `longitude` DECIMAL(9, 6) NOT NULL COMMENT 'XXX.XXXXXX°',
    `latitude` DECIMAL(9, 6) NOT NULL COMMENT 'XXX.XXXXXX°',
    `radius` INT NOT NULL COMMENT 'Radius in meters',
    PRIMARY KEY (`zone_id`)
);

CREATE TABLE `weather` (
    `weather_id` VARCHAR(50) NOT NULL,
    `wind_speed` FLOAT NULL DEFAULT 0,
    `rainfall` FLOAT NULL DEFAULT 0,
    `observation_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`weather_id`)
);

CREATE TABLE `edge` (
    `path_id` VARCHAR(50) NOT NULL,
    `origin_station_id` VARCHAR(50) NOT NULL,
    `destination_station_id` VARCHAR(50) NOT NULL,
    `distance` INT NOT NULL COMMENT 'Distance in meters',
    PRIMARY KEY (`path_id`),
    FOREIGN KEY (`origin_station_id`) REFERENCES `station`(`station_id`),
    FOREIGN KEY (`destination_station_id`) REFERENCES `station`(`station_id`)
);

CREATE TABLE `intersection` (
    `intersection_id` VARCHAR(50) NOT NULL,
    `longitude` DECIMAL(9, 6) NOT NULL COMMENT 'XXX.XXXXXX°',
    `latitude` DECIMAL(9, 6) NOT NULL COMMENT 'XXX.XXXXXX°',
    `path1_id` VARCHAR(50) NOT NULL,
    `path2_id` VARCHAR(50) NOT NULL,
    PRIMARY KEY (`intersection_id`),
    FOREIGN KEY (`path1_id`) REFERENCES `edge`(`path_id`),
    FOREIGN KEY (`path2_id`) REFERENCES `edge`(`path_id`)
);

CREATE TABLE `path` (
    `delivery_id` VARCHAR(50) NOT NULL,
    `path_id` VARCHAR(50) NOT NULL,
    PRIMARY KEY (`delivery_id`, `path_id`),
    FOREIGN KEY (`delivery_id`) REFERENCES `delivery`(`delivery_id`),
    FOREIGN KEY (`path_id`) REFERENCES `edge`(`path_id`)
);