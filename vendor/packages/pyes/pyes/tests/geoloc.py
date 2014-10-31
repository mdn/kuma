#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for pyes.  These require an es server with thrift plugin running on the default port (localhost:9500).
"""
import unittest
from pyes.tests import ESTestCase, get_conn
from pyes import GeoBoundingBoxFilter, GeoDistanceFilter, GeoPolygonFilter, FilteredQuery, MatchAllQuery

def setUp():
    conn = get_conn()
    mapping = {
        "pin" : {
            "properties" : {
                "location" : {
                    "type" : "geo_point"
                }
            }
        }
    }
    conn.delete_index_if_exists("test-mindex")
    conn.create_index("test-mindex")
    conn.put_mapping("test-type", {'properties':mapping}, ["test-mindex"])
    conn.index({
        "pin" : {
            "location" : {
                "lat" : 40.12,
                "lon" :-71.34
            }
        }
    }, "test-mindex", "test-type", 1)
    conn.index({
        "pin" : {
            "location" : {
                "lat" : 40.12,
                "lon" : 71.34
            }
        }
    }, "test-mindex", "test-type", 2)

    conn.refresh(["test-mindex"])

def tearDown():
    conn = get_conn()
    conn.delete_index_if_exists("test-mindex")

#--- Geo Queries Test case
class GeoQuerySearchTestCase(ESTestCase):

    def test_GeoDistanceFilter(self):
        gq = GeoDistanceFilter("pin.location", {"lat" : 40, "lon" :-70}, "200km")
        q = FilteredQuery(MatchAllQuery(), gq)
        result = self.conn.search(query=q, indexes=["test-mindex"])
        self.assertEquals(result['hits']['total'], 1)

        gq = GeoDistanceFilter("pin.location", [-70, 40], "200km")
        q = FilteredQuery(MatchAllQuery(), gq)
        result = self.conn.search(query=q, indexes=["test-mindex"])
        self.assertEquals(result['hits']['total'], 1)

    def test_GeoBoundingBoxFilter(self):
        gq = GeoBoundingBoxFilter("pin.location", location_tl={"lat" : 40.717, "lon" : 70.99}, location_br={"lat" : 40.03, "lon" : 72.0})
        q = FilteredQuery(MatchAllQuery(), gq)
        result = self.conn.search(query=q, indexes=["test-mindex"])
        self.assertEquals(result['hits']['total'], 1)

        gq = GeoBoundingBoxFilter("pin.location", [70.99, 40.717], [74.1, 40.03])
        q = FilteredQuery(MatchAllQuery(), gq)
        result2 = self.conn.search(query=q, indexes=["test-mindex"])
        self.assertEquals(result2['hits']['total'], 1)
        del result['took']
        del result2['took']
        self.assertEquals(result, result2)

    def test_GeoPolygonFilter(self):
        gq = GeoPolygonFilter("pin.location", [{"lat" : 50, "lon" :-30},
                                                {"lat" : 30, "lon" :-80},
                                                {"lat" : 80, "lon" :-90}]
                                                )
        q = FilteredQuery(MatchAllQuery(), gq)
        result = self.conn.search(query=q, indexes=["test-mindex"])
        self.assertEquals(result['hits']['total'], 1)

        gq = GeoPolygonFilter("pin.location", [[ -30, 50],
                                              [ -80, 30],
                                              [ -90, 80]]
                                                )
        q = FilteredQuery(MatchAllQuery(), gq)
        result = self.conn.search(query=q, indexes=["test-mindex"])
        self.assertEquals(result['hits']['total'], 1)

if __name__ == "__main__":
    unittest.main()
