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

## HTML Templates

Ayase provides only a few HTML Templates as default, and they are not part of the standard: admins may feel free to use whichever HTML template suits their needs.

Our criteria for default HTML Templates is historical significance that match archived data with the period appropriate theming for the original boards they came from, and most of all an avoidance of anything but HTML5, basic CSS, and ECMAScript unless absolutely necessary.

Only the progrider template is currently built.

### Progrider Template

Based on https://github.com/bibanon/world4ch , this jinja2 template is based on clean source code from the progrider textboard when it was still around, which ultimately has its origins in 2ch-style textboard engines.

![Board Catalog](ayase-world4ch-catalog.png)

![Single Thread](ayase-world4ch-thread.png)

### Futaba & Burichan Template

A template recalling the colors of the Futaba/2chan imageboard, which 4chan was based on. 

We would probably use the [4archive](https://github.com/4archive/4archive) templates for this, a stunning laravel imageboard archive engine that was ultimately never put into use.

### Fuuka4plebs Template 

A template based on an previous attempted replacement of FoolFuuka by 4plebs.

### Infinity Template

A template based on 8chan OpenIB/infinity/vichan source code.

### Monaba Template

A template based on Monaba.

https://github.com/ahushh/Monaba
