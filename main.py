#!/usr/bin/env python3
import json
import mimerender
import settings
from bottle import route, redirect, request, run
from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, base_dc_reader
from oaipmh.error import NoRecordsMatchError

# Add text/bibliography MIME-TYPE
mimerender._MIME_TYPES['bibtex'] = ('text/bibliography',)
mimerender = mimerender.BottleMimeRender()


def render_html(url):
    redirect(url)


def render_bibtex(**args):
    # TODO
    return json.dumps(args,
                      sort_keys=True,
                      indent=4,
                      separators=(',', ': '))


def render_json(**args):
    return json.dumps(args,
                      sort_keys=True,
                      indent=4,
                      separators=(',', ': '))


@route("/<doi:path>")
@mimerender(
    default='html',
    html=render_html,
    bibtex=render_bibtex,
    json=render_json
)
def doi(doi):
    # Try to fetch it from the registry
    registry = MetadataRegistry()
    registry.registerReader('base_dc', base_dc_reader)
    client = Client(settings.oaipmh_url, registry)
    try:
        for record in client.listRecords(metadataPrefix="base_dc",
                                         set=("proaixy:doi:%s" % (doi,))):
            try:
                # If openaccess version available, redirect the user to it
                has_oa = True in [i == "1" for i in record[1].getField("oa")]
                if has_oa:
                    return {"url": record[1].getField("link")[0]}
            except KeyError:
                pass
    except NoRecordsMatchError:
        pass
    # If not found, pass it to upstream doi handler
    doi_upstream_url = "https://dx.doi.org/%s?" % (doi,)
    for k, v in request.query.decode().items():
        doi_upstream_url += "%s=%s&" % (k, v)
    return {"url": doi_upstream_url}


if __name__ == "__main__":
    # Run the app
    run(host=settings.host,
        port=settings.port,
        debug=settings.debug)
