import netmiko
from netmiko import ConnectHandler, SCPConn, file_transfer, progress_bar
from datetime import datetime
import os
import hashlib
import time
from easygui import passwordbox
import re




def check_ping(hostname):
    response = os.system("ping -n 1 " + hostname)
    if response == 0:
        print("")  # print blank lines
        ping_status = "Network Active"
    else:
        print("")  # print blank lines
        ping_status = "Network Error"

    return ping_status


def main_menu():
    print("")  # print blank lines
    print("")  # print blank lines
    print("1. Show VLAN list")
    print("2. Show interface status")
    print("3. Modify interface")
    print("4. Modify Interface Description")
    print("5. Bounce Selected Interface")
    print("6. Shut Interface")
    print("7. Backup Running Configuration")
    print("8. Reload Device Now")
    print("9. Planned Reload")
    print("10. Firmware Upgrade")
    print("11. Exit")


def backup_configuration():
    time.sleep(2)
    print(f'Backing up current running configuration')
    print("")  # print blank lines
    time.sleep(1)
    print(f'Creating backup file')
    # get hostname of device
    net_connect.enable()
    device_hostname = net_connect.send_command('show configuration | include hostname')
    device_hostname = device_hostname.split()
    device_hostname = device_hostname[1]
    # get current date and time
    dt = datetime.now()
    dt_string = dt.strftime("%Y%m%d_%H:%M")
    backup_file = f'{device_hostname}-{dt_string}.cfg'
    time.sleep(2)
    print(f'Backup file will be named {backup_file}')
    time.sleep(3)
    print(f'Copying configuration to backup file')

    try:
        backup = net_connect.send_command_timing(f'copy running-config flash:/{device_hostname}-{dt_string}.cfg')
        net_connect.send_command_timing('\n')
        print(f'SUCCESS: Configuration backed up')

    except Exception as e:
        print(f'ERROR: Configuration not backed up')


def bounce_interface():
    time.sleep(2)
    interface = input(f'Please input the interface you would like to bounce (e.g. Gi1/0/1): ')
    time.sleep(2)
    device_connected = net_connect.send_command(f'show mac address-table interface {interface}')
    #print(device_connected)

    while True:
        if interface in device_connected: # checks to see if there is a device connected to interface
            device_connected = device_connected.split()
            print(f'Device with mac address {device_connected[14]} will be disconnected during this process')
            print("")
            print("")
            confirm_change = input(f' Please enter YES to continue with bouncing the interface: ').upper()

            if confirm_change == 'YES' or confirm_change == 'Y':
                break
            else:
                return
        else:
            break

    print("")  # print blank lines
    print("")  # print blank lines
    time.sleep(2)
    print(f'Bouncing {interface}')
    time.sleep(3)
    config_commands = [
        'Interface ' + interface,
        'shut ',
        'no shut ',
    ]
    net_connect.send_config_set(config_commands)
    print("")  # print blank lines
    print("")  # print blank lines
    print(f'Interface {interface} has been bounced')

def shut_interface():
    time.sleep(2)
    interface = input(f'Please input the interface you would like to shut (e.g. Gi1/0/1): ')
    time.sleep(2)
    device_connected = net_connect.send_command(f'show mac address-table interface {interface}')
    print(device_connected)

    while True:
        if interface in device_connected: # checks to see if there is a device connected to interface
            device_connected = device_connected.split()
            print(f'Device with mac address {device_connected[14]} will be disconnected after this process')
            print("")
            print("")
            confirm_change = input(f' Please enter YES to continue with shutting the interface: ').upper()

            if confirm_change == 'YES' or confirm_change == 'Y':
                break
            else:
                return
        else:
            break

    print("")  # print blank lines
    print("")  # print blank lines
    time.sleep(2)
    print(f'Shutting {interface}')
    time.sleep(3)
    config_commands = [
        'Interface ' + interface,
        'shut ',
    ]
    net_connect.send_config_set(config_commands)
    print("")  # print blank lines
    print("")  # print blank lines
    print(f'Interface {interface} has been shut')


def firmware_upgrade():
    time.sleep(2)
    print(f'Upgrade Firmware')
    firmware_location = input(f'Please enter the location of the firmware file: ')
    firmware_image = input(f'Please enter the firmware image: ')

    # transfer file to device
    net_connect.config_mode()
    net_connect.send_command('ip scp server enable') #enable SCP on switch
    net_connect.exit_config_mode()
    source_file = firmware_location
    dest_file = firmware_image
    transfer_dict = file_transfer(net_connect, source_file=source_file, dest_file=dest_file, direction='put', overwrite_file=False, progress=progress_bar, socket_timeout=240,)

    #check file size is increasing
    time.sleep(10)
    filesize = net_connect.send_command(f'dir flash: | in {firmware_image}')
    print(filesize)


    if transfer_dict.get("file_exists") is True and transfer_dict.get("file_transferred") is False and transfer_dict.get("file_verified") is True:
        print(f'Firmware is already on the device, and has not been copied but has verified that the MD5 checksum are correct')
    else:
        print(f'Firmware has been copied to the device and MD5 checksum verified.')


    #install firmware version
    #net_connect.send_command(f'install add file flash:{firmware_image} activate commit prompt-level none')



def reload_now():
    time.sleep(2)
    confirm_reload = input(f'Are you sure you want to reload {hostname}: ')
    if confirm_reload == 'YES' or confirm_reload == 'Y':
        time.sleep(2)
        print(f'{hostname} is going to be reloaded, this will impact any downstream devices')
        net_connect.send_command('reload', expect_string='')
        net_connect.send_command('\n')
    else:
        time.sleep(3)
        print(f'{hostname} will not be reloaded at this stage')


def planned_reload():
    time.sleep(2)
    # confirm_reload = input(f'Are you sure you want to reload {hostname}')
    # if confirm_reload == 'YES' or confirm_reload == 'Y':
    #     time.sleep(2)
    #     print(f'{hostname} is going to be reloaded, this will impact any downstream devices')
    #     net_connect.send_command('reload', expect_string='')
    #     net_connect.send_command('\n')
    # else:
    #     print(f'{hostname} will not be reloaded at this stage')



def show_vlan():
    time.sleep(2)
    print(f'Collating all VLANs currently on device\n')
    time.sleep(4)
    show_vlan = net_connect.send_command('show vlan brief')
    regx = re.compile(r'(?m)^(\d+)|(Et\d+\/\d+)')
    for m in regx.finditer(show_vlan):
        print(f'VLAN {m.group(1)}')
    time.sleep(3)


def show_int_status():
    time.sleep(2)
    print(f'Collating current interface status\n')
    time.sleep(4)
    show_int_status = net_connect.send_command('show int status')
    print(show_int_status)
    time.sleep(3)


def modify_interface():
    time.sleep(2)
    print(f'Before modifying the interface, backing up the current configuration')
    backup_configuration()
    time.sleep(2)
    show_int_status = net_connect.send_command('show int status')
    interface = input(f'Please input the interface you would like to modify (e.g. Gi1/0/1): ')
    time.sleep(2)
    print(f'Showing current configuration for interface {interface}')
    current_configuration = net_connect.send_command(f'show running-config interface {interface}')
    if 'Incomplete command.' in current_configuration: # checks for port selection validation
        print(f' ERROR: Invalid port selection')
        return
    print(current_configuration)
    if 'Unrecognized command' in current_configuration: # checks for port selection validation
        print(f' ERROR: Invalid port selection')
        return
    if 'switchport mode trunk' in current_configuration: # trunk port check
        print(f' ERROR: The interface selected is a trunk port, and is restricted')
        return

    confirm_change = input(f' Please enter YES to continue with the VLAN change: ').upper()
    print("")
    print("")
    time.sleep(3)
    # VLAN configuration change

    if confirm_change == 'YES' or confirm_change == 'Y':
        vlan = input(f' Please enter new VLAN: ') #user enters new vlan number
        print("")
        print("")
        time.sleep(2)
        show_vlan = net_connect.send_command('show vlan brief') # stores current vlans on switch

        if vlan in show_vlan: # checks to confirm new VLAN is on device
            print(f'Assigning VLAN {vlan} to interface {interface}')
            time.sleep(3)
            config_commands = [
                'Interface ' + interface,
                'switchport access vlan ' + vlan,
            ]
            net_connect.send_config_set(config_commands)
            print(f'VLAN has been updated on interface {interface}\n')
            time.sleep(3)
            print(f'Showing updated configuration of interface {interface}\n')
            time.sleep(2)
            updated_configuration = net_connect.send_command(f'show running-config interface {interface}') # shows updated configuration
            print(updated_configuration)
            time.sleep(3)
            print(f'Writing configuration to device')
            time.sleep(2)
            net_connect.send_command_expect('write memory') # writes new configuration to device
        else:
            print(f'ERROR: The VLAN selected is not apart of the VLAN database')


def modify_interface_description():
    time.sleep(2)
    show_int_status = net_connect.send_command('show int status')
    interface = input(f'Please input the interface you would like to modify (e.g. Gi1/0/1): ')
    time.sleep(2)
    print(f'Showing current configuration for interface {interface}')
    current_configuration = net_connect.send_command(f'show running-config interface {interface}')
    if 'Incomplete command.' in current_configuration:  # checks for port selection validation
        print(f' ERROR: Invalid port selection')
        return
    print(current_configuration)
    if 'Unrecognized command' in current_configuration:  # checks for port selection validation
        print(f' ERROR: Invalid port selection')
        return
    if 'switchport mode trunk' in current_configuration:  # trunk port check
        print(f' ERROR: The interface selected is a trunk port, and is restricted')
        return

    confirm_change = input(f' Please enter YES to continue with the description change: ').upper()
    print("")
    print("")
    time.sleep(3)
    # interface description configuration change

    if confirm_change == 'YES' or confirm_change == 'Y':

        while True:
            try:
                description = input(f' Please enter new description: ')  # user enters new interface description
                description_length = len(description)
                if description_length <= 230:  # validates the description is less than or equal to 230 characters
                    break
                else:
                    continue
            except:
                print(f'ERROR: The description is too long, please ensure it is less than 230 characters')

        print("")  # print blank lines
        print("")  # print blank lines
        time.sleep(2)
        print(f'Updating description on interface {interface}')
        time.sleep(3)
        config_commands = [
            'Interface ' + interface,
            'description ' + description,
        ]
        net_connect.send_config_set(config_commands)
        print(f'Description has been updated on interface {interface}\n')
        time.sleep(3)
        print(f'Showing updated configuration of interface {interface}\n')
        time.sleep(2)
        updated_configuration = net_connect.send_command(f'show running-config interface {interface}')  # shows updated configuration
        print(updated_configuration)
        time.sleep(3)
        print(f'Writing configuration to device')
        time.sleep(2)
        net_connect.send_command_expect('write memory')  # writes new configuration to device


def exit_program():
    print(f'Exiting Program')
    print(f'Thank you for using this utility')
    loop = False # exiting the application
    net_connect.disconnect()

# ----- RUN COMMANDS ----- #

print(f'Welcome to the Network Automation Utility')
time.sleep(3)
# basic device check
while True:
    hostname = input(f'Please enter the host IP or DNS name (e.g. 192.168.0.10): ')
    # ping check
    ping_status = check_ping(hostname)
    if ping_status == "Network Active":
        print(f'{hostname} is active\n')
        break
    else:
        print(f'{hostname} is not active\n')

# connect to device
while True:
    try:
        username = input(f'Please enter the device username: ')
        device_type = 'cisco_ios'

        net_connect = ConnectHandler(host=hostname, device_type=device_type, username=username, password=passwordbox(msg="Please enter the device password: "))
        net_connect.enable()
        break
    except:
        print(f'Login failed, please try again.')
        continue

while True:
    main_menu() # displays main menu
    menu_selection = input(f'Please enter your selection [1-4]: ')
    print("")  # print blank lines
    # if to access menu selection
    if menu_selection == '1':
        show_vlan()
    elif menu_selection == '2':
        show_int_status()
    elif menu_selection == '3':
        modify_interface()
    elif menu_selection == '4':
        modify_interface_description()
    elif menu_selection == '5':
        bounce_interface()
    elif menu_selection == '6':
        shut_interface()
    elif menu_selection == '7':
        backup_configuration()
    elif menu_selection == '8':
        reload_now()
    elif menu_selection == '9':
        planned_reload()
    elif menu_selection == '10':
        firmware_upgrade()
    elif menu_selection == '11':
        exit_program()
        break
    else:
        print(f'The menus selection provided of {menu_selection} is invalid. Enter any key to try again.')







