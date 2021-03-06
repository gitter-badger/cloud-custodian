# Copyright 2016 Capital One Services, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Provide basic caching services to avoid extraneous queries over
multiple policies on the same resource type.
"""

import cPickle

import os
import logging
import time

log = logging.getLogger('c7n.cache')


def factory(config):
    if not config:
        return NullCache(None)
    
    if not config.cache or not config.cache_period:
        log.info("Disabling cache")    
        return NullCache(config)
    
    return FileCacheManager(config)


class NullCache(object):

    def __init__(self, config):
        self.config = config

    def load(self):
        return False

    def get(self, key):
        pass
    
    def save(self, key, data):
        pass
    
    
class FileCacheManager(object):

    def __init__(self, config):
        self.config = config
        self.cache_period = config.cache_period
        self.cache_path = os.path.abspath(
            os.path.expanduser(
                os.path.expandvars(
                    config.cache)))
        self.data = {}

    def get(self, key):
        k = cPickle.dumps(key)
        return self.data.get(k)
        
    def load(self):
        if os.path.isfile(self.cache_path):
            if (time.time() - os.stat(self.cache_path).st_mtime >
                    self.config.cache_period * 60):
                return False
            with open(self.cache_path) as fh:
                self.data = cPickle.load(fh)
            log.info("Using cache file %s" % self.cache_path)
            return True
        
    def save(self, key, data):
        with open(self.cache_path, 'w') as fh:
            cPickle.dump({
                cPickle.dumps(key): data}, fh, protocol=2)
