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

LOG = logging.getLogger("sts.entities.teston_entities")

from sts.entities.base import BiDirectionalLinkAbstractClass
from sts.entities.hosts import HostAbstractClass
from sts.entities.hosts import HostInterface

from sts.entities.controllers import ControllerAbstractClass
from sts.entities.controllers import ControllerState


class TestONNetworkLink(BiDirectionalLinkAbstractClass):
  def __init__(self, node1, port1, node2, port2):
    super(TestONNetworkLink, self).__init__(node1, port1, node2, port2)


class TestONAccessLink(BiDirectionalLinkAbstractClass):
  def __init__(self, host, interface, switch, switch_port):
    super(TestONAccessLink, self).__init__(host, interface, switch, switch_port)

  @property
  def host(self):
    return self.node1

  @property
  def interface(self):
    return self.port1

  @property
  def switch(self):
    return self.node2

  @property
  def switch_port(self):
    return self.port2


class TestONHostInterface(HostInterface):
  def __init__(self, hw_addr, ips, name):
    super(TestONHostInterface, self).__init__(hw_addr, ips, name)

  def __repr__(self):
    return "%s:%s" % (self.name, ",".join([ip.toStr() for ip in self.ips]))


class TestONHost(HostAbstractClass):
  def __init__(self, interfaces, name="", hid=None):
    super(TestONHost, self).__init__(interfaces, name, hid)

  def send(self, interface, packet):
    # Mininet doesn't really deal with multiple interfaces
    pass

  def receive(self, interface, packet):
    pass

  def __repr__(self):
    return "<Host %s: %s>" % (self.name,
                              ",".join([repr(i) for i in self.interfaces]))


class TestONOVSSwitch(object):
  def __init__(self, dpid, name, ports):
    self.ports = {}
    self.name = name
    self.dpid = dpid
    for port in ports:
      self.ports[port.name] = port

  def __str__(self):
    return self.name

  def __repr__(self):
    return "<OVSSwitch %s: %s>" % (self.name,
                                   ",".join([repr(p) for p in self.ports]))


class TestONPort(object):
  def __init__(self, hw_addr, name, ips=None):
    self.hw_addr = hw_addr
    self.name = name
    self.ips = ips

  def __str__(self):
    return self.name

  def __repr__(self):
    return "%s:%s" % (self.name, self.ips)


class TestONONOSConfig(object):
  """
  TestON ONOS specific configurations
  """
  def __init__(self, label, address, port):
    self.label = label
    self.address = address
    self.port = port
    self.cid = self.label


class TestONONOSController(ControllerAbstractClass):
  """
  ONOS Controller using TestON Driver for ONOS.
  """
  def __init__(self, config, teston_onos, sync_connection_manager=None,
               snapshot_service=None, log=None):
    super(TestONONOSController, self).__init__(config,
                                               sync_connection_manager,
                                               snapshot_service)
    self.teston_onos = teston_onos
    self.log = log or LOG
    self.state = self.check_status(None)
    self._blocked_peers = set()

  @property
  def config(self):
    """Controller specific configuration object"""
    return self._config

  @property
  def label(self):
    """Human readable label for the controller"""
    return self.config.label

  @property
  def cid(self):
    """Controller unique ID"""
    return self.config.label

  @property
  def state(self):
    """
    The current controller state.

    See: ControllerState
    """
    return self._state

  @state.setter
  def state(self, value):
    self._state = value

  @property
  def snapshot_service(self):
    return self._snapshot_service

  @property
  def sync_connection_manager(self):
    return self._sync_connection_manager

  def is_remote(self):
    """
    Returns True if the controller is running on a different host that sts
    """
    return True

  def start(self, multiplex_sockets=False):
    """Starts the controller"""
    if self.state != ControllerState.DEAD:
      self.log.warn("Controller is already started!" % self.label)
      return
    self.log.info("Launching controller: %s" % self.label)
    self.teston_onos.start_all()
    self.state = ControllerState.ALIVE

  def kill(self):
    self.log.info("Killing controller: %s" % self.label)
    if self.state != ControllerState.ALIVE:
      self.log.warn("Controller already killed: %s" % self.label)
      return
    self.teston_onos.stop_all()
    self.state = ControllerState.DEAD

  def restart(self):
    """
    Restart the controller
    """
    self.log.info("Restarting controller: %s" % self.label)
    if self.state != ControllerState.DEAD:
      self.log.warn(
        "Restarting controller %s when it is not dead!" % self.label)
      return
    self.start()

  def check_status(self, simulation):
    if self.teston_onos.status() == 1:
      return ControllerState.ALIVE
    else:
      return ControllerState.DEAD

  @property
  def blocked_peers(self):
    """Return a list of blocked peer controllers (if any)"""
    return self._blocked_peers

  def block_peer(self, peer_controller):
    """Ignore traffic to/from the given peer controller
    """
    self.teston_onos.block_peer(peer_controller.config.address)
    self.blocked_peers.add(peer_controller)

  def unblock_peer(self, peer_controller):
    """Stop ignoring traffic to/from the given peer controller"""
    self.teston_onos.unblock_peer(peer_controller.config.address)
    self.blocked_peers.remove(peer_controller)
