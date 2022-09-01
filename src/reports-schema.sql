CREATE TABLE `rules` (                                                                                                                                                                                       
  `rule_id` int(11) NOT NULL AUTO_INCREMENT,                                                                                                                                                                 
  `rule_name` varchar(30) NOT NULL,                                                                                                                                                                          
  `rule_desc` text,                                                                                                                                                                                          
  PRIMARY KEY (`rule_id`)                                                                                                                                                                                    
)

CREATE TABLE `reports` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `board` varchar(10) NOT NULL,
  `no` int(10) unsigned NOT NULL,
  `rule_id` int(11) NOT NULL,
  `reason` text,
  `ip_reporter` int(4) unsigned NOT NULL,
  `created` datetime NOT NULL,
  `reviewed` boolean NOT NULL,
  `reviewer` text,
  PRIMARY KEY (`id`),
  KEY `FK_rule_id` (`rule_id`),
  CONSTRAINT `FK_rule_id` FOREIGN KEY (`rule_id`) REFERENCES `rules` (`rule_id`)
)

