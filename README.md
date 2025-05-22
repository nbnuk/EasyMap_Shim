# EasyMap Shim

This project is a shim for the NBN Atlas, designed to provide backward compatibility for the older NBN EasyMap service and some functionalities of the SingleSpecies map service. Its primary purpose is to offer developers a transitional period to adapt their applications and websites to the new NBN Atlas APIs.

## Key Features

*   **Species Distribution Map Generation:** Creates map images visualizing species distribution based on data from the NBN Atlas.
*   **Flexible Parameterization:** Supports a wide range of parameters for map customization, including:
    *   Taxon Version Key (TVK) for species identification.
    *   Vice County (VC), zoom levels, and custom bounding boxes (via OS Grid References or Northing/Easting coordinates).
    *   Multiple date bands for displaying occurrences across different time periods.
    *   Adjustable image dimensions (width, height) and resolution (including retina @2x support).
*   **Performance Caching:** Implements caching for generated map images and HTML pages to ensure fast response times and reduce load on backend services.
*   **`/EasyMap` Endpoint:** Provides an HTML page that embeds the generated map. This page can be customized with titles, terms and conditions, links to NBN Atlas, data source references, and the NBN logo.
*   **`/Image` Endpoint:** Offers direct access to the generated map images, suitable for embedding in various applications.
*   **`/SingleSpecies` Compatibility:** Includes a `/SingleSpecies/{tvk}/map` endpoint that translates parameters from some older NBN SingleSpecies map URLs to the `/Image` format, aiding in a smoother transition.
*   **Coordinate Transformation:** Built-in capability to convert OS Grid References to WGS84 geographic coordinates.

## Endpoints and Parameters

The service provides the following main endpoints:

### 1. `/Image`

This endpoint directly returns a PNG map image based on the provided parameters.

**Common Parameters:**

*   `tvk` (required): The Taxon Version Key for the species (e.g., `NHMSYS0000344177`).
*   `vc`: Vice County name or code (e.g., `CAMALL`, `VC113`). Overrides `zoom` if `zoom` is also UK-based.
*   `zoom`: Predefined zoom area (e.g., `UK`, `England`, `Scotland`, `Wales`, `Ireland`, `channelislands`, or specific VC codes like `VC113`). Also accepts custom bounding box names defined in `server.py` like `highland`.
*   `bl`, `tr`: Bottom-left and top-right OS Grid References to define a custom bounding box (e.g., `bl=TG50`, `tr=TG51`).
*   `blCoord`, `trCoord`: Bottom-left and top-right Northing/Easting coordinates (EPSG:27700) as comma-separated values (e.g., `blCoord=600000,300000`, `trCoord=610000,310000`).
*   `ds`: Comma-separated list of data source UIDs or GUIDs (e.g., `GA000012,GA000157`).
*   `w`, `h`: Width and height of the image in pixels (e.g., `w=400`, `h=300`). Defaults to 350x350 if not specified. Clamped between 80 and 800 pixels.
*   `retina`: Set to `2` for a double resolution (retina) image (e.g., `retina=2`).
*   `b0from`, `b0to`: Start and end year for the primary date band (e.g., `b0from=1990`, `b0to=1999`).
*   `b0fill`: Hex color code for the primary date band fill (e.g., `b0fill=FFFF00`).
*   `b1from`, `b1to`, `b1fill`: Parameters for an optional second date band.
*   `b2from`, `b2to`, `b2fill`: Parameters for an optional third date band.
*   `bg`: Background map type. `vc` for a Vice County boundary map, otherwise defaults to a world map.
*   `res`: Resolution of the map grid. Accepted values: `50km`, `10km`, `2km`, `1km`, `100m`. Defaults to `10km`.
*   `cachedays`: Number of days to cache the image (0-31). `0` forces regeneration. Defaults to 31.

**Example:**

```
https://<your-server-address>/Image?tvk=NHMSYS0000344177&w=400&ds=GA000012&b0fill=ff0000&res=2km
```

*(This will generate a 400px wide map for the specified TVK, filtering by dataset GA000012, with occurrences colored red, at a 2km resolution.)*

### 2. `/EasyMap`

This endpoint returns an HTML page that embeds the map image and can include additional information like titles, links, and data source references. It accepts most of the same parameters as the `/Image` endpoint to control the map generation.

**Additional Parameters for `/EasyMap`:**

*   `title`: Type of title to display.
    *   `sci` (default): Scientific name.
    *   `com`: Common name.
    *   Any other string: Custom title.
    *   Set to `0` or an empty string for no title.
*   `terms`: Set to `1` (default) to display terms and conditions. `0` to hide.
*   `link`: Set to `1` (default) to display a link to the NBN Atlas interactive map for the species. `0` to hide.
*   `ref`: Set to `1` (default) to display a list of data sources. `0` to hide.
*   `logo`: Set to `1` (default) to display the NBN logo. `0` to hide.
*   `css`: URL to a custom CSS file for styling the EasyMap page.
*   `maponly`: Set to `1` to display only the map image without any surrounding HTML content (title, terms, etc.). `0` (default).

**Example:**

```
https://<your-server-address>/EasyMap?tvk=NHMSYS0000344177&w=500&h=400&title=com&res=10km&b0from=2000&b0to=2010&b0fill=00FF00
```

*(This will generate an HTML page with a 500x400 map, showing the common name as the title, for occurrences between 2000-2010 colored green, at 10km resolution.)*

### 3. `/SingleSpecies/{tvk}/map`

This endpoint provides compatibility for some older NBN SingleSpecies map URLs. It translates the parameters and redirects to the `/Image` endpoint.

**Supported Parameters (translated to `/Image` parameters):**

*   `datasets`: Maps to `ds`.
*   `resolution`: Maps to `res`.
*   `imagesize`: Multiplied by 100 to map to `w`. (Aspect ratio is maintained based on default map proportions).
*   `band`: Up to three `band` parameters can be supplied, mapping to `b0from,b0to,b0fill`, `b1from,b1to,b1fill`, etc. Format: `YYYY-YYYY,hexcolor`.

**Example:**

```
https://<your-server-address>/SingleSpecies/NHMSYS0001387317/map?datasets=GA000157,GA001180&resolution=10km&imagesize=8&band=1600-1987,ffffff&band=1988-1997,0095ff&band=1998-2025,0000ff
```

*(This URL will be translated and redirected to an equivalent `/Image` URL.)*

## Setup and Installation

These instructions are based on the `notes.txt` file and assume a Linux (Ubuntu-like) environment.

**1. Prerequisites:**

*   Python 3 and `virtualenv`
*   `git`
*   Build essentials (often `build-essential` package)
*   Development files for zlib and libjpeg (e.g., `zlib1g-dev`, `libjpeg-dev`)

You can typically install these using your system's package manager:
```bash
sudo apt-get update
sudo apt-get install -y python3-virtualenv build-essential python3-dev zlib1g-dev libjpeg-dev git
```

**2. Clone Repository:**

```bash
git clone https://github.com/nbnuk/EasyMap_Shim.git
cd EasyMap_Shim
```

**3. Create Virtual Environment:**

It's recommended to use a virtual environment:
```bash
virtualenv ENV -p python3 --system-site-packages
source ENV/bin/activate
```

**4. Install Python Dependencies:**

Install the required Python packages using pip:
```bash
pip install tornado pyproj pillow
```

**5. Create Cache Directory:**

The application needs a directory to store cached images and HTML:
```bash
mkdir cache
```

**6. Running the Server:**

*   **Development:** You can run the server directly for testing:
    ```bash
    python server.py
    ```
    By default, it might try to run HTTPS on port 8443 and expects SSL certificates (`.cert`, `.key`, `.intr`) in `/home/ubuntu/.keys/`. You might need to adjust the `server.py` script (e.g., comment out SSL options or change paths) for a simpler HTTP setup for local development if certificates are not available. The original `notes.txt` also implies an HTTP server was tested on port 8888.

*   **Production:**
    *   The `startup.sh` script is intended to run the server (likely via a process manager like `systemd` or in `rc.local` as mentioned in `notes.txt`).
    *   `iptables` rules (as detailed in `notes.txt`) are suggested to redirect standard HTTP/HTTPS ports (80/443) to the application's ports (e.g., 8080/8443). A more robust approach in modern systems might involve using a reverse proxy like Nginx or Apache.
    *   SSL certificates need to be correctly configured as per the paths in `server.py` or adapted for your reverse proxy.

**7. Cache Management:**

*   A cron job is intended to run `cleancache.py` periodically to remove stale cache files (older than 31 days). Refer to `cron.tab` for the suggested cron job definition.
    ```
    # Example from cron.tab (runs daily at 3:05 AM)
    # 5 3 * * * /usr/bin/python3 /home/ubuntu/EasyMap_Shim/cleancache.py
    ```
*   The `updatecaches.py` script (mentioned in `notes.txt`) is likely used for initial population of caches, such as the `guid-to-uid.json` file. This might need to be run once during setup:
    ```bash
    python updatecaches.py
    ```

**Note:** The original `notes.txt` contains specific paths (e.g., `/home/ubuntu/`) and configurations. You will need to adapt these to your specific server environment and user.

## Directory Structure

A brief overview of important files and directories within the project:

```
.
├── cache/                # Directory for storing cached images and HTML files
├── static/               # Static assets served directly
│   ├── index.html        # Informational page about the EasyMap Shim
│   ├── easymap.html      # Basic HTML structure for map embedding (likely a fallback)
│   ├── documentation.css # CSS for static pages
│   └── ...               # Other static files (images, icons)
├── templates/            # HTML templates used by the /EasyMap endpoint
│   ├── retina.html       # Template for retina display maps
│   └── standard.html     # Standard template for maps
├── .gitignore            # Specifies intentionally untracked files that Git should ignore
├── cleancache.py         # Script to remove old files from the cache (run by cron)
├── cleancache-size.py    # Script to remove small (likely erroneous) files from the cache
├── coordtransform.py     # Handles coordinate system transformations
├── cron.tab              # Example cron job definitions for cache cleaning
├── httpredirectserver.py # (Purpose not fully clear from content, may be for HTTP to HTTPS redirection or other utility)
├── loadbboxes.py         # Loads bounding box definitions
├── loaddatasources.py    # Utilities for fetching data from NBN Atlas (species names, data source UIDs)
├── loadimage.py          # Core logic for fetching map tiles and composing images
├── notes.txt             # Original developer setup notes and instructions
├── server.py             # Main Tornado web server application, request handlers, and core logic
├── simpleflock.py        # File locking utility (used by loaddatasources.py)
├── startup.sh            # Shell script for starting the application server
└── updatecaches.py       # Script to update/populate certain cache files (e.g., GUID to UID mapping)
```

## Caveats

This shim aims to provide continuity but has some limitations compared to the original NBN EasyMap service:

*   **Background Maps:** Ordnance Survey maps are not available as backgrounds. Grid overlays are also not supported.
*   **Service Degradation:** At certain resolutions, the map generation might switch from tiled images to point markers. When this occurs:
    *   Filter parameters (like date ranges and dataset filters) may be ignored.
    *   Only the primary data layer might be displayed.
    *   The map background may turn grey to indicate this simplified rendering.
*   **WMS Functionality:** This shim does not implement Web Map Service (WMS) functions. For WMS alternatives, please consult the official NBN Atlas API documentation.

## Recommendations

While this EasyMap Shim provides a temporary solution, developers are strongly encouraged to migrate their applications to utilize the modern NBN Atlas APIs. The new APIs offer more robust and flexible ways to integrate NBN data, including:

*   **Interactive Maps:** Transitioning to interactive maps (e.g., using Leaflet.js, OpenLayers) can significantly enhance user experience. The NBN Atlas API fully supports tile-based and vector-based interactive maps.
*   **Comprehensive API:** Explore the full capabilities of the [NBN Atlas API](https://api.nbnatlas.org) for richer data integration beyond static map images.

## How it Works (High-Level Overview)

1.  **HTTP Request:** A user or client sends an HTTP request to one of the defined endpoints (e.g., `/Image` or `/EasyMap`) with various URL parameters.
2.  **Parameter Parsing:** The `server.py` (Tornado request handler) parses these parameters, sanitizes inputs, and determines the map specifications (species, area, date ranges, colors, dimensions, etc.).
3.  **Cache Check:** The system generates a unique hash based on the request parameters that affect the visual output. It checks if a cached version of the image (or HTML page for `/EasyMap`) exists for this hash and if it's still valid (within `cachedays`).
    *   If a valid cached version exists, it's served directly.
4.  **Data Fetching (if not cached or stale):**
    *   `loaddatasources.py` might be used to resolve TVKs to scientific/common names or DRUIDs for data sources via NBN Atlas web services.
    *   `loadimage.py` constructs URLs to fetch map data/tiles from NBN Atlas services (geoserver for basemaps, biocache for occurrence data).
    *   Coordinate transformations (e.g., OS Grid to EPSG:27700, then to EPSG:4326 for some API calls) are handled by `coordtransform.py` as needed.
5.  **Image Composition (if not cached or stale):**
    *   `loadimage.py` fetches the necessary map tiles or data.
    *   Using the Pillow (PIL) library, it composites these layers:
        *   A base map layer.
        *   One or more species occurrence layers, colored and filtered according to date bands and other parameters.
6.  **Caching:** The newly generated image (or HTML page) is saved to the `cache/` directory with a filename derived from the parameter hash.
7.  **HTTP Response:** The generated (or cached) image/HTML is sent back to the client.
8.  **Error Handling:** If issues occur (e.g., NBN Atlas services are down, no records found for a query), the system might return a default or empty map. The `cleancache-size.py` script helps remove very small (potentially empty/error) cached files.
