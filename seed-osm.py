import httplib2, ModestMaps, os, sys, time

TRAPI_URL = 'http://api1.osm.absolight.net/api/0.6/map?tile=%s'
DELAY_SECS = 300
MAX_TRIES = 3
ZOOM_LEVEL = 14
LOAD_COMMAND = 'osm2pgsql %s'


class TrapiOfflineException(Exception):
    pass


class OSMSeeder:
    def __init__(self, min_lat, min_lon, max_lat, max_lon):
        mm = ModestMaps.OpenStreetMap.Provider()
        self.tiles = set()

        for lat, lon in [(lat, lon) for lat in [min_lat, max_lat] for lon in [min_lon, max_lon]]:
            coord = mm.locationCoordinate(ModestMaps.Geo.Location(lat, lon)).zoomTo(ZOOM_LEVEL)
            self.tiles.add((ZOOM_LEVEL, int(coord.column), int(coord.row)))

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

            content = self.fetch(self.url_for(*tile))

            filename = "%s-%s-%s.osm" % tile
            f = open(filename, 'w+')
            f.write(content)
            f.close()

            os.system(LOAD_COMMAND % filename)

        self.log("Updated %s tiles in %ss." % (time.time() - start_time))

    def url_for(self, z, x, y):
        tile = "%s,%s,%s" % (z, x, y)
        return TRAPI_URL % tile

    def fetch(self, url):
        self.log("- Fetching: %s" % url)
        h = httplib2.Http()
        start_time = time.time()
        tries = 0

        while True:
            resp, content = h.request(url)

            if resp['status'] == 200:
                self.log("Success! %sb fetched in %ss." % (len(content), time.time() - start_time))
                return content

            self.log("HTTP Error %s. Trying again in %ss." % (resp['status'], DELAY_SECS))

            tries += 1
            if tries > MAX_TRIES:
                raise TrapiOfflineException("Giving up after %s tries on %s" % (MAX_TRIES, url))

            time.sleep(DELAY_SECS)

    def log(self, msg):
        sys.stdout.write("%s\n" % msg)
        sys.stdout.flush()


if __name__ == '__main__':
    seeder = OSMSeeder(*[float(arg) for arg in sys.argv[1:]])
    seeder.seed()
