"""Load configuration from config.toml."""
import toml
import os

print(os.getcwd())
default_config = toml.load('src/core/defaults.toml')
user_config = toml.load('src/config.toml')

# Ensure default config lists are empty
default_config["archives"] = None
default_config["boards"] = None
default_config["skins"] = None

default_config.update(user_config)
config = default_config
print(config)
# SHA256 options
sha256_dirs = False
if "hash_format" in config and config["hash_format"] == "sha256":
    sha256_dirs = True

# Define board list
board_list = []
for board in config["board"]:
    board_list.append(board["shortname"])

# Define archive list
archive_list = []
for archive in config["archives"]:
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
