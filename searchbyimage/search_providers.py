# TODO: logging
import os
from io import BytesIO
from urllib.parse import urljoin

import pycurl


class SearchProvider:

    def search(self, filename):
        pass


class SearchProviderCurl(SearchProvider):

    def __init__(self, upload_progress=None):
        '''
        :param upload_progress: request uploading progress callback,
                                will be called with a fraction value 0-1
                                (might slightly overshoot)
        '''
        self.upload_progress = upload_progress

    def _make_curl(self):
        c = pycurl.Curl()
        c.headers = {}
        c.buffer = BytesIO()
        c.setopt(c.NOPROGRESS, 0)
        c.setopt(c.PROGRESSFUNCTION, self._loading)
        # c.setopt(c.WRITEFUNCTION, lambda _: None)
        c.setopt(c.WRITEDATA, c.buffer)
        c.setopt(c.HEADERFUNCTION, lambda l: self._header_function(l, c))
        return c

    @staticmethod
    def _header_function(header_line, c):
        header_line = header_line.decode('iso-8859-1')
        if ':' not in header_line:
            return
        name, value = header_line.split(':', 1)
        name = name.strip()
        value = value.strip()
        name = name.lower()
        c.headers[name] = value

    def _loading(self, download_t, download_d, upload_t, upload_d):
        self.upload_progress(upload_d/upload_t if upload_t else 0)

    def _upload_done(self):
        self.upload_progress(1)


class ImgOps(SearchProviderCurl):

    def search(self, filename):
        size = os.path.getsize(filename)/1024/1024
        if size > 5:
            # TODO: downscale till within limit?
            raise Exception(f'file "{filename} ({size:.02f}MiB)" exceeds ImgOps 5MiB limit.')

        c = self._make_curl()
        data = [
            ('photo', (pycurl.FORM_FILE, filename.encode('utf-8')))
        ]
        c.setopt(c.URL, 'http://imgops.com/upload/uploadPhoto-action.asp')
        c.setopt(c.POST, True)
        c.setopt(c.HTTPPOST, data)
        c.setopt(c.USERAGENT, "Mozilla/5.0 (compatible; pycurl)")
        c.perform()
        c.close()
        self._upload_done()
        redirect = urljoin('https://imgops.com', c.headers['location'])
        return redirect


class Google(SearchProviderCurl):

    def search(self, filename):
        c = self._make_curl()
        data = [
            ('encoded_image', (pycurl.FORM_FILE, filename.encode('utf-8')))
        ]
        c.setopt(c.URL, 'https://www.google.com/searchbyimage/upload')
        c.setopt(c.POST, True)
        c.setopt(c.HTTPPOST, data)
        c.setopt(c.USERAGENT, "Mozilla/5.0 (compatible; pycurl)")
        c.perform()
        c.close()
        self._upload_done()
        return c.headers['location']
