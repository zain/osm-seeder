import httplib2, sys, time

TRAPI_URL = 'http://api1.osm.absolight.net/api/0.6/map?tile=%s'
DELAY_SECS = 30
MAX_TRIES = 3


class TrapiOfflineException(Exception):
    pass


class OSMSeeder:
    def url_for(self, z, x, y):
        tile = "%s,%s,%s" % (z, x, y)
        return TRAPI_URL % tile

    def fetch(self, url):
        self.log("- Fetching: %s" % url)
        h = httplib2.Http()
        start_time = time.time()
        tries = 0

        while True:
            tries += 1
            if tries > MAX_TRIES:
                raise TrapiOfflineException("Giving up after %s tries on %s" % (MAX_TRIES, url))

            resp, content = h.request(url)

            if resp['status'] != 200:
                self.log("HTTP Error %s. Trying again in %ss." % (resp['status'], DELAY_SECS))
                time.sleep(DELAY_SECS)
            else:
                self.log("Success! %sb fetched in %ss." % (len(content), time.time() - start_time))
                return content

    def log(self, msg):
        sys.stdout.write("%s\n" % msg)
        sys.stdout.flush()


if __name__ == '__main__':
    h = httplib2.Http()

    status_code = 503
    while status_code != 200:
        resp, content = h.request('http://api1.osm.absolight.net/api/0.6/map?tile=14,2622,6336')
        status_code = resp['status']
        print ". ",
        sys.stdout.flush()
        time.sleep(30)

    print "\n"
    import ipdb; ipdb.set_trace()

