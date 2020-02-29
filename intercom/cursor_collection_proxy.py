# -*- coding: utf-8 -*-

import six
from intercom import HttpError
from intercom import utils
from intercom.collection_proxy import CollectionProxy

class CursorCollectionProxy(CollectionProxy):
    def __init__(self, client, collection_cls, collection, finder_url, finder_params={}):
        super(CursorCollectionProxy, self).__init__(client, collection_cls, collection,finder_url, finder_params=finder_params)
        self.paging_info = None

    def get_page(self, url, params={}):
        # get a page of results
        # from intercom import Intercom

        # if there is no url stop iterating
        if url is None:
            raise StopIteration

        if "sort" in params or "query" in params:
            url = f"{url}/search"
            if self.paging_info and "next" in self.paging_info:
                params["pagination"] = {
                    "per_page": self.paging_info["per_page"],
                    "starting_after": self.paging_info["next"]["starting_after"]
                }
            response = self.client.post(url, params)
        else:
            response = self.client.get(url, params)

        if response is None:
            raise HttpError('Http Error - No response entity returned')

        # HACK: dealing with the fact that in unstable /tags is returning
        # {'type': 'list', 'data': []} instead of
        # {'type': 'tags.list', 'tags': []}
        if response['type'] == 'list':
            collection = response['data']
        else:
            collection = response[self.collection]
        # if there are no resources in the response stop iterating
        if collection is None:
            raise StopIteration

        # create the resource iterator
        self.resources = iter(collection)
        # grab the next page URL if one exists
        self.next_page = self.extract_next_link(response)

    def get_next_page(self):
        # get the next page of results
        return self.get_page(self.next_page, self.finder_params)

    def extract_next_link(self, response):
        if self.paging_info_present(response):
            self.paging_info = response["pages"]
            print(self.paging_info)
            if "next" in self.paging_info:
                # '/users?per_page=50&page=2'
                # {'page': 2, 'starting_after': 'WzE1NzkxODQzNDEwMDAsIjVlMTZmOTg3MWEzNmFiMTFjMDY2YmMzZSIsMl0='}
                if self.finder_params:
                    return '/{}'.format(self.collection)
                else:
                    return '/{}?page={}&starting_after={}'.format(
                        self.collection,
                        self.paging_info["next"]["page"],
                        self.paging_info["next"]["starting_after"])
