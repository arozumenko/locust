#  Copyright (c) 2014 Artem Rozumenko (artyom.rozumenko@gmail.com)
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from unittest import TestCase, TextTestRunner, TestLoader
import logging

from locustdriver import LocustDriver


class SimpleFailoverTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup class method in unittests."""
        cls.driver = LocustDriver()
        cls.driver.add_node(node_name='local_test',
                            node_ip='127.0.0.1:8080',
                            node_group='main',
                            key='test')
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)-10s : %(message)s',
                            datefmt='%y-%m-%d %H:%M:%S')

    def test_get_process(self):
        """Test for gracefull stop ngnix."""
        result = self.driver.get_process(nodes="local_test", names="nano")
        logging.debug(result)
        self.assertTrue('nano' in result['local_test']['list'][0]['name'])


if __name__ == '__main__':
    SUITE = TestLoader().loadTestsFromTestCase(SimpleFailoverTest)
    TextTestRunner(verbosity=2).run(SUITE)

