#! /usr/bin/python

import sys
import os
import re
import prlsdkapi

host_ip = "127.0.0.1"
host_user = "user"
host_passwd = "password"
vm_name = "vm"
guest_user = "vm_user"
guest_passwd = "vm_password"

consts = prlsdkapi.prlsdk.consts
# ----------------------------------------------------------------------------


def get_vm(server, vm_name):
    result = server.get_vm_list().wait()
    # Iterate through all VMs until we find the one we're looking for
    for i in range(result.get_params_count()):
        vm = result.get_param_by_index(i)
        name = vm.get_name()
        if name.startswith(vm_name):
            return vm
    print "VM", vm_name, "not found on Virtualisation Host",\
          server.get_server_info().get_host_name()
# ----------------------------------------------------------------------------


def get_vm_info(HOST, USER, PASSW, VM):
    prlsdkapi.init_server_sdk()
    server = prlsdkapi.Server()
    server.login(HOST, USER, PASSW, '', 0, 0,
                 consts.PSL_NORMAL_SECURITY).wait()

    vm = get_vm(server, VM)
    vm_config = vm.get_config()

    print "----------------------------------------------------------------"
    print "Virtualisation host:", server.get_server_info().get_host_name()
    print "----------------------------------------------------------------"
    print "VM name:", vm_config.get_name()

    count = vm_config.get_net_adapters_count()
    for i in range(count):
        net_adapter = vm.get_net_adapter(i)
        print "VM MAC:", str(net_adapter.get_mac_address())
        print "VM VLAN:", str(net_adapter.get_virtual_network_id())
        print "Virtualisation Host interface name:",\
              str(net_adapter.get_host_interface_name())

    print "----------------------------------------------------------------"
    print "VM ip-address:",\
          get_guest_ip(get_guest(vm, guest_user, guest_passwd))
    print "----------------------------------------------------------------"

    server.logoff()
    prlsdkapi.deinit_sdk()
# ----------------------------------------------------------------------------


def get_guest(vm, g_login, g_password):
    guest = vm.login_in_guest(g_login, g_password).wait().get_param()
    return guest
# ----------------------------------------------------------------------------


def get_guest_ip(guest):
    network_info = get_guest_netinfo(guest)

    m = re.search('^([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})',
                  network_info[0]["ip"])
    ip = m.group(0)

    return ip
# ----------------------------------------------------------------------------


def get_guest_netinfo(guest):
    server_config = guest.get_network_settings().wait().get_param()
    count = server_config.get_net_adapters_count()
    vm_net_adapters = {}

    # For every adapter, parse out it's network info
    for n in range(count):
        vm_net_adapters[n] = {}
        host_net = server_config.get_net_adapter(n)
        emulated_type = host_net.get_net_adapter_type()
        type = ""

        # Determine what type of adapter this is
        if emulated_type == prlsdkapi.prlsdk.consts.PNA_HOST_ONLY:
            type = "host-only"
        elif emulated_type == prlsdkapi.prlsdk.consts.PNA_SHARED:
            type = "shared"
        elif emulated_type == prlsdkapi.prlsdk.consts.PNA_BRIDGED_ETHERNET:
            type = "bridged"

        # Adapter type
        vm_net_adapters[n]["type"] = type
        # The IPv4 address associated with this adapter
        vm_net_adapters[n]["ip"] = host_net.get_net_addresses().get_item(0)
        # The hardware address for this adapter
        vm_net_adapters[n]["mac"] = host_net.get_mac_address()
        # Parse the DNS servers used by this adapter
        dns_str_list = host_net.get_dns_servers()
        vm_net_adapters[n]["dns"] = [dns_str_list.get_item(m)
                                     for m in
                                     range(dns_str_list.get_items_count())]
        # The gateway address for this adapter
        vm_net_adapters[n]["gateway"] = host_net.get_default_gateway()

    return vm_net_adapters
# ----------------------------------------------------------------------------


def main():
    get_vm_info(host_ip, host_user, host_passwd, vm_name)
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
