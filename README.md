
# EasyMap_Shim

EasyMap_Shim is a Python-based service that generates species distribution maps based on NBN Atlas data. I guess it was named thus as it serves as a simplified interface for accessing and visualizing species distribution data without directly interacting with the more complex underlying WMS services.


# Architecture Diagram

```
                       +----------------+
                       |                |
                       |  Web Browser/  |
                       |    Client      |
                       |                |
                       +--------+-------+
                                |
                                | HTTP Request/Response
                                | (PNG Image)
                                v
+------------------------------------------------------------------+
|                                                                  |
|                        EasyMap_Shim Server                       |
|                                                                  |
|  +---------------+    +----------------+    +----------------+   |
|  |               |    |                |    |                |   |
|  | Tornado Web   |    | Request        |    | Cache System   |   |
|  | Server        +--->+ Handler        |<-->| (PNG files)    |   |
|  | (server.py)   |    | (server.py)    |    |                |   |
|  |               |    |                |    |                |   |
|  +---------------+    +--------+-------+    +----------------+   |
|                                |                                 |
|                                | If not cached                   |
|                                v                                 |
|  +---------------+    +----------------+    +----------------+   |
|  |               |    |                |    |                |   |
|  | Bounding Box  |<-->| Image          |<-->| Data Source    |   |
|  | Handler       |    | Generator      |    | Manager        |   |
|  | (loadbboxes.py)|   | (loadimage.py)  |    |(loaddatasources.py)|
|  |               |    |                |    |                |   |
|  +---------------+    +----------------+    +----------------+   |
|                                |                                 |
|  +---------------+             |             +----------------+  |
|  |               |             |             |                |  |
|  | Coordinate    |<------------+------------>| Cache          |  |
|  | Transformer   |                           | Management     |  |
|  |(coordtransform.py)                        | (updatecaches.py) |
|  |               |                           |                |  |
|  +---------------+                           +----------------+  |
|                                                                  |
+------------------+----------------+---------------+--------------+
                   |                |               |
                   | HTTP Requests  | HTTP Requests | HTTP Requests
                   v                v               v
+----------------+ +----------------+ +-------------+ +----------------+
|                | |                | |             | |                |
| Records WS     | | Species WS     | | Layers      | | Registry       |
| Service        | | Service        | | Service     | | Service        |
|                | |                | | (GeoServer) | |                |
|(records-ws.    | |(species-ws.    | |(layers.     | |(registry.      |
| nbnatlas.org)  | | nbnatlas.org)  | | nbnatlas.org)| | nbnatlas.org)  |
|                | |                | |             | |                |
+----------------+ +----------------+ +-------------+ +----------------+

   Data Flow:
   ---------
   1. Client requests image with TVK and parameters
   2. Server checks cache for existing image
   3. If not cached or expired, server processes:
      a. Looks up species info via Species WS
      b. Gets distribution data from Records WS
      c. Gets base maps from Layers Service
      d. Generates composite image using Image Generator
      e. Caches the result
   4. Returns image to client
```

## Component Descriptions:

1. **Tornado Web Server**: Handles HTTP requests and routes to appropriate handlers
2. **Request Handler**: Processes parameters and orchestrates the image generation
3. **Cache System**: Stores generated images to improve performance
4. **Image Generator**: Creates composite maps from tiles or WMS requests
5. **Data Source Manager**: Interacts with NBN services to retrieve species data
6. **Bounding Box Handler**: Manages geographic areas and coordinates
7. **Coordinate Transformer**: Converts between coordinate systems
8. **External Services**: NBN Atlas services providing species data and maps

## Overview

This service provides an API endpoint for generating species distribution maps as PNG images with customizable parameters such as:
- Taxon Version Keys (TVKs)
- Geographic areas (e.g. vice-counties or custom bounding boxes)
- Time periods
- Custom colors
- Resolution options
- Multiple data layers

The application uses a caching mechanism to improve performance and reduce load on underlying services.

## Dependencies

### External Services
EasyMap_Shim depends on the following NBN Atlas services:

1. **Records Web Service** (https://records-ws.nbnatlas.org)
   - Used for querying occurrence records
   - Provides the actual species distribution data

2. **Species Web Service** (https://species-ws.nbnatlas.org)
   - Used for species information lookup
   - Resolves TVKs to scientific names and common names
   - Maps synonyms to accepted taxonomic concepts

3. **Layers Service** (https://layers.nbnatlas.org)
   - Provides base maps and administrative boundaries
   - Serves GeoServer WMS layers

4. **Registry** (https://registry.nbnatlas.org)
   - Maps between dataset GUIDs and UIDs

### Python Dependencies
- Tornado (web server)
- PIL/Pillow (image processing)
- pyproj (coordinate transformations)
- Standard libraries: urllib, json, hashlib, concurrent.futures, etc.

## Installation

```bash
# Update system and install dependencies
sudo apt-get -y update
sudo apt-get -y install python-virtualenv build-essential python3-dev zlib1g-dev libjpeg-dev git fail2ban

# Clone the repository
git clone https://github.com/nbnuk/EasyMap_Shim.git
cd EasyMap_Shim

# Set up virtual environment
virtualenv ENV -p python3 --system-site-packages
source ENV/bin/activate
pip install tornado
pip install pyproj
pip install pillow

# Create cache directory
mkdir cache

# Set up port forwarding (optional)
sudo iptables -A INPUT -i eth0 -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -i eth0 -p tcp --dport 8080 -j ACCEPT
sudo iptables -A PREROUTING -t nat -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 8080
sudo iptables -A INPUT -i eth0 -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -i eth0 -p tcp --dport 8443 -j ACCEPT
sudo iptables -A PREROUTING -t nat -i eth0 -p tcp --dport 443 -j REDIRECT --to-port 8443
sudo iptables-save > iptables.conf

# Set up scheduled tasks
crontab cron.tab

# Initialize cache
python updatecaches.py

# Start service
./startup.sh
```

## API Documentation

### Main Endpoint: `/Image`

Generates a map image for a specified species.

#### Required Parameters:

- `tvk` - Taxon Version Key for the species

#### Optional Parameters:

- **Map Area**
  - `vc` - Vice county ID
  - `zoom` - Predefined zoom area (e.g. "UK")
  - `bl` & `tr` - Bottom-left and top-right OS grid references
  - `blCoord` & `trCoord` - Bottom-left and top-right coordinates in EPSG:27700

- **Appearance**
  - `w` - Width in pixels (80-800, default: 350)
  - `h` - Height in pixels (80-800, default: 350)
  - `retina` - Resolution multiplier (1 or 2)
  - `bg` - Background type ("vc" for vice-county background)
  - `res` - Grid resolution ("50km", "10km", "2km", "1km", "100m")

- **Data Selection**
  - `ds` - Data source IDs (comma-separated)

- **Color and Date Bands**
  - `b0fill` - Color for main layer (hex without #, default: FFFF00)
  - `b0from` & `b0to` - Year range for main layer (e.g. "1990", "2020")

  - `b1fill` - Color for second layer (optional)
  - `b1from` & `b1to` - Year range for second layer

  - `b2fill` - Color for third layer (optional) 
  - `b2from` & `b2to` - Year range for third layer

- **Cache Control**
  - `cachedays` - Number of days to keep cached images (0-31, default: 31)

### Legacy Endpoint: `/singlespecies/{tvk}`

Compatible with legacy NBN Gateway singlespecies URL format.

## Examples

### Basic Usage

Generate a simple species distribution map:
```
https://easymap.nbnatlas.org/Image?tvk=NBNSYS0000002740
```

### Custom Width and Color

Generate a red map of specific width:
```
https://easymap.nbnatlas.org/Image?tvk=NBNSYS0000002740&w=332&b0fill=ff0000
```

### Multiple Date Bands

Generate a map showing distribution across three time periods with different colors:
```
https://easymap.nbnatlas.org/Image?tvk=NBNSYS0000002740&b0from=1600&b0to=1987&b0fill=ffffff&b1from=1988&b1to=1997&b1fill=0095ff&b2from=1998&b2to=2025&b2fill=0000ff
```

### Regional Map with Custom Resolution

Generate a map for a specific vice county with 2km resolution:
```
https://easymap.nbnatlas.org/Image?tvk=NBNSYS0000002740&vc=23&res=2km
```

### Custom Dataset Selection

Generate a map using specific data sources:
```
https://easymap.nbnatlas.org/Image?tvk=NBNSYS0000002740&ds=GA000157,GA001180
```

## Technical Notes

- Images are cached based on request parameters
- The service first checks if an accepted taxonomic concept exists for the provided TVK
- For large areas or high resolutions, the service automatically switches between tiled requests and direct WMS requests
- Multiple worker threads are used to fetch map tiles in parallel
- The cache can be purged or refreshed using the updatecaches.py and cleancache.py scripts
