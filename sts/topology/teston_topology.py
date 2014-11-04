# Copyright 2014      Ahmed El-Hassany
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import logging

from sts.entities.teston_entities import TestONHost
from sts.entities.teston_entities import TestONHostInterface
from sts.entities.teston_entities import TestONAccessLink
from sts.entities.teston_entities import TestONNetworkLink
from sts.entities.teston_entities import TestONPort
from sts.entities.teston_entities import TestONOVSSwitch
from sts.entities.teston_entities import TestONONOSConfig
from sts.entities.teston_entities import TestONONOSController

from sts.topology.base import Topology
from sts.topology.base import TopologyCapabilities
from sts.topology.controllers_manager import ControllersManager
from sts.topology.connectivity_tracker import ConnectivityTracker
from sts.topology.dp_buffer import DataPathBuffer

from sts.topology.teston_switches_manager import TestONSwitchesManager
from sts.topology.teston_hosts_manager import TestONHostsManager
from sts.topology.teston_patch_panel import TestONPatchPanel


class TestONTopology(Topology):
  """
  A Topology abstraction for TestON Infrastructure.

  Example use:
  topo = TestONTopology(main.Mininet1, onos_controllers=
  [(main.ONOS1, 'ONOS1', main.params['CTRL']['ip1'], main.params['CTRL']['port1']),
  (main.ONOS2, 'ONOS2', main.params['CTRL']['ip2'], main.params['CTRL']['port2'])])
  """
  def __init__(self, teston_mn, onos_controllers, reactive_controllers=False):
    assert onos_controllers is None or isinstance(onos_controllers, list)
    self.log = logging.getLogger(__name__ + '.TestONTopology')
    teston_mn.update()
    switches_manager = TestONSwitchesManager(teston_mn)
    hosts_manager = TestONHostsManager(teston_mn)
    patch_panel = TestONPatchPanel(teston_mn, hosts_manager, switches_manager)
    controller_manager = ControllersManager()
    if onos_controllers is None:
      onos_controllers = []
    for info in onos_controllers:
      config = TestONONOSConfig(label=info[1], address=info[2], port=info[3])
      if len(info) > 4:
        config.intent_ip = info[4]
        config.intent_port = info[5]
        config.intent_url = info[6]

      controller = TestONONOSController(config, info[0])
      if len(info) > 4:
        controller_manager.capabilities._can_add_intent = True
        controller_manager.capabilities._can_remove_intent = True
      controller_manager.add_controller(controller)
    capabilities = TopologyCapabilities()

    is_host = lambda x: isinstance(x, TestONHost)
    is_switch = lambda x: isinstance(x, TestONOVSSwitch)
    is_network_link = lambda x: isinstance(x, TestONNetworkLink)
    is_access_link = lambda x: isinstance(x, TestONAccessLink)
    is_host_interface = lambda x: isinstance(x, TestONHostInterface)
    is_port = lambda x: isinstance(x, TestONPort)


    super(TestONTopology, self).__init__(
      capabilities=capabilities, patch_panel=patch_panel,
      switches_manager=switches_manager, hosts_manager=hosts_manager,
      controllers_manager=controller_manager, dp_buffer=DataPathBuffer(),
      is_host=is_host, is_switch=is_switch, is_network_link=is_network_link,
      is_access_link=is_access_link, is_host_interface=is_host_interface,
      is_port=is_port,
      connectivity_tracker=ConnectivityTracker(reactive_controllers))
