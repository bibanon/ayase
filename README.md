> **Note:** Currently Ayase is only a proof of concept that essentially just proxies the 4chan API for API testing and HTML Templating. Future versions will set up a connection to the Asagi and Ayase Schemas.

**Ayase** is a 4chan Archiver API middleware and HTML frontend based on Python, Falcon, Hug, and Jinja2.

It was produced by the Bibliotheca Anonoma as a replacement for FoolFuuka, to be the API Middleware and HTML Templating Frontend to both Asagi and Ayase compatible scrapers, and the definition of the Ayase SQL Standard.

## Installation

Ensure that Python and Pip are installed. Python 2.7 or Python 3.3 and higher is recommended.

```
pip install -r requirements.txt
```

## Usage

The following command will run a server at <http://localhost:8000> . Check the automatically generated API documentation for HTML and REST API endpoint usage information.

```
cd ayase
hug -f fourchan.py
```
