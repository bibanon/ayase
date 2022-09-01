"""Load configuration from config.toml."""
import toml

default_config = toml.load('src/core/defaults.toml')
user_config = toml.load('config.toml')

# Ensure default config lists are empty
default_config["archives"] = None
default_config["boards"] = None
default_config["skins"] = None

default_config.update(user_config)
config = default_config

# SHA256 options
sha256_dirs = False
if "hash_format" in config and config["hash_format"] == "sha256":
    sha256_dirs = True

# Define board list
board_list = []
for board in (config["board"] if "board" in config else []):
    board_list.append(board["shortname"])

# Define archive list
archive_list = []
for archive in (config["archives"] if "archives" in config else []):
    archive_list.append(archive["shortname"])

render_constants = dict(
    asagi=True,
    sha256_dirs=sha256_dirs,
    archives=config["archives"],
    boards=config["boards"],
    skins=config["skins"],
    options=config["options"],
    scraper=config["scraper"],
    site_name=config["site_name"]
)
