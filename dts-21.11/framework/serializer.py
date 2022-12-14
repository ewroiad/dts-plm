# BSD LICENSE
#
# Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of Intel Corporation nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Wrapper class for serializer module
"""
import os
import pickle


class Singleton(type):
    _instances = {}

    def __call__(self, *args, **kwargs):
        if self not in self._instances:
            self._instances[self] = \
                super(Singleton, self).__call__(*args, **kwargs)
        return self._instances[self]


class Serializer(object):

    """
    Two-levels cache implementation for storing/retrieving any kind of object
    using using a key-value model. It uses the pickle module to store objects
    into a file.
    This class implements the Singleton pattern. Everytime its constructor
    is called it will return a reference to the same instance.
    """

    def __init__(self):
        self.volatile_cache = {}
        self.filename = 'serializer.cache'

    def save(self, object_name, object_to_save):
        """
        Saves an object into the volatile dictionary cache - which
        resides in memory.
        """
        self.volatile_cache[object_name] = object_to_save

    def load(self, object_name):
        """
        Loads and returns an object from the volatile cache.
        """
        return self.volatile_cache.get(object_name, None)

    def set_serialized_filename(self, filename):
        """
        Sets the name of the non-volatile cache file to be used in the future
        """
        self.filename = filename

    def save_to_file(self):
        """
        Saves the volatile cache to a file (non-volatile) using the pickle
        module. Returns True in case everything went OK, False otherwise.
        """
        try:
            serialized_file = open(self.filename, 'w')
            pickle.dump(self.volatile_cache, serialized_file)
            serialized_file.close()
            return True
        except:
            return False

    def load_from_file(self):
        """
        Reads from a pickle-like file using pickle module and populates the
        volatile cache. Returns True in case everything went OK, False
        otherwise.
        """
        try:
            serialized_file = open(self.filename, 'r')
            self.volatile_cache = pickle.load(serialized_file)
            serialized_file.close()
            return True
        except:
            self.volatile_cache.clear()
            return False

    def discard_cache(self):
        """
        Discards both volatile and non-volatile cache.
        """
        self.volatile_cache.clear()
        if os.path.exists(self.filename):
            os.remove(self.filename)
