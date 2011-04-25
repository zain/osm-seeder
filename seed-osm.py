import httplib2, ModestMaps, os, sys, time

API_URL = 'http://api.openstreetmap.org/api/0.6/map?bbox=%s'
DELAY_SECS = 300
MAX_TRIES = 3
ZOOM_LEVEL = 16
LOAD_COMMAND = 'osm2pgsql --append --database=gis --username=postgres -W %s'


class APIOfflineException(Exception):
    pass


class OSMSeeder:
    def __init__(self, min_lat, min_lon, max_lat, max_lon):
        self.mm = ModestMaps.OpenStreetMap.Provider()
        self.tiles = set()

        for lat, lon in [(lat, lon) for lat in [min_lat, max_lat] for lon in [min_lon, max_lon]]:
            loc = ModestMaps.Geo.Location(lat, lon)
            coord = self.mm.locationCoordinate(loc).zoomTo(ZOOM_LEVEL).container()
            self.tiles.add(coord)

        self.log("Found %s tiles at zoom level %s." % (len(self.tiles), ZOOM_LEVEL))

    def seed(self):
        start_time = time.time()
        first = True

        for tile in self.tiles:
            if not first:
                self.log("Waiting %s before fetching next tile." % DELAY_SECS)
                time.sleep(DELAY_SECS)
            else:
                first = False

            content = self.fetch(self.url_for(tile))

            filename = "%s-%s-%s.osm" % (tile.zoom, tile.column, tile.row)
            f = open(filename, 'w+')
            f.write(content)
            f.close()

            print "------------[Loading...]------------"
            os.system(LOAD_COMMAND % filename)
            print "-------------[Finished]-------------"

        self.log("Updated in %ss." % (time.time() - start_time))

    def url_for(self, coord):
        nw = self.mm.coordinateLocation(coord)
        se = self.mm.coordinateLocation(coord.right().down())
        max_lat = max(nw.lat, se.lat)
        min_lat = min(nw.lat, se.lat)
        max_lon = max(nw.lon, se.lon)
        min_lon = min(nw.lon, se.lon)
        bbox = "%s,%s,%s,%s" % (min_lon, min_lat, max_lon, max_lat)
        return API_URL % bbox

    def fetch(self, url):
        self.log("- Fetching: %s" % url)
        h = httplib2.Http()
        start_time = time.time()
        tries = 0

        while True:
            resp, content = h.request(url)

            if resp['status'] == '200':
                self.log("Success! %sb fetched in %ss." % (len(content), time.time() - start_time))
                return content

            self.log("HTTP Error %s. Trying again in %ss." % (resp['status'], DELAY_SECS))

            tries += 1
            if tries > MAX_TRIES:
                raise APIOfflineException("Giving up after %s tries on %s" % (MAX_TRIES, url))

            time.sleep(DELAY_SECS)

    def log(self, msg):
        sys.stdout.write("%s\n" % msg)
        sys.stdout.flush()


if __name__ == '__main__':
    seeder = OSMSeeder(*[float(arg) for arg in sys.argv[1:]])
    seeder.seed()
