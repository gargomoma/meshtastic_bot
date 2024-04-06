import meshtastic
import meshtastic.serial_interface, meshtastic.tcp_interface
from pubsub import pub
import time
import traceback
import os

meshtastic_addr = os.environ.get('MESHTASTIC_ADDR', '/dev/ttyUSB0')
conn_type       = os.environ.get('CONN_TYPE'      , 'serial')
no_limit_users  = os.environ.get('NO_LIMIT_USERS' , '').split(',')
print("---------------STARTING---------------")
print(f"No limit users: {no_limit_users}")


reply_message_ping = "🏓Pong!🏓"

users = {}
meshtastic_interface = None

def ts_toStr(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

def connectNode(meshtastic_addr,conn_type='serial'):
    global meshtastic_interface
    #https://github.com/geoffwhittington/meshtastic-matrix-relay/blob/main/meshtastic_utils.py#L20
    retry_limit = 10
    attempts = 1
    successful = False
    while not successful and attempts <= retry_limit:
        try:
            if conn_type == 'wifi':
                meshtastic_interface = meshtastic.tcp_interface.TCPInterface(hostname=meshtastic_addr)
            else:
                meshtastic_interface = meshtastic.serial_interface.SerialInterface(meshtastic_addr)
            successful = True
        except Exception as e:
            attempts += 1
            if attempts <= retry_limit:
                print(
                    f"Attempt #{attempts-1} failed. Retrying in {10*attempts} secs {e}"
                )
                time.sleep(10*attempts)
            else:
                print(f"Could not connect: {e}")
                return None
    return meshtastic_interface
    
######### Messages #########
def get_can_reply(fromId,packet):
    global users,no_limit_users 
    if fromId in no_limit_users:
        can_reply = True    
    elif fromId in users and 'lastTS' in users[fromId].keys():
        can_reply = packet['rxTime'] - users[fromId]['lastTS'] >= 60*15 #minutes
    else:
        can_reply = True
    ####################################################
    if not can_reply:
        print(f"Ignoring user: [{fromId}] {users[packet['fromId']]['longName']} ({users[packet['fromId']]['shortName']}) wait { int(15-((time.time() - users[fromId]['lastTS'])/60)) }")
    return can_reply

def get_channel(packet):
    return 0 if 'channel' not in packet else packet['channel']
    
def is_mqtt(packet,node_info={}):
    print(f"is_mqtt=={'viaMqtt' in node_info} or {('rxRssi' not in packet or 'rxSnr' not in packet)}")
    return 'viaMqtt' in node_info or ('rxRssi' not in packet or 'rxSnr' not in packet)

def sendText(interface,packet,text):
    global users
    print(f"-#--#- Sending message to [{packet['fromId']}] {users[packet['fromId']]['longName']}")      
    if packet['toId']=='^all':
        #Gets channel, or deduces it's 0
        interface.sendText(text, channelIndex= get_channel(packet) )
    else:
        interface.sendText(text, destinationId= packet['fromId'] )
    
######### PubSub #########
def onReceive(packet, interface):
    global users
    try:
        if 'decoded' in packet and packet['decoded']['portnum'] == 'TEXT_MESSAGE_APP':
            message_bytes = packet['decoded']['payload']
            message_string = message_bytes.decode('utf-8')
            fromId = packet['fromId']
            toId = packet['toId']
            
            ###Gets node info##
            node_info = interface.nodes.get(fromId, {})
            if fromId not in users.keys():
                users[fromId] = {}   
            users[fromId]['longName']  = node_info['user']['longName']
            users[fromId]['shortName'] = node_info['user']['shortName']            
            fromMqtt = is_mqtt(packet,node_info)
            users[fromId]['viaMqtt'] = fromMqtt
            time.sleep(1)
            
            if 'rxTime' not in packet:
                print("***Following packet has rxTime missing, adding local time***")
                packet['rxTime'] = time.time()
            
            signal_info = "" if fromMqtt else f" [ RSSI:{packet['rxRssi']} SNR:{packet['rxSnr']} ]"            
            print(f"-#- {ts_toStr(packet['rxTime'])}|UTC From Ch[{get_channel(packet)}] MQTT[{fromMqtt}] -- User: [{fromId}] {users[packet['fromId']]['longName']} ({users[packet['fromId']]['shortName']}){signal_info}")
            print(f"-#--#- Received: '{message_string}'")
            print("#####PACKET#####")
            print(packet)
            print("------NODE------")
            print(node_info)
            print("################")
            can_reply = get_can_reply(fromId,packet)
            if can_reply:              
                if message_string == "/ping":
                    sendText(interface,packet,f"{reply_message_ping}\n{ts_toStr(packet['rxTime'])}|UTC MQTT[{fromMqtt}]")
                    users[fromId]['lastTS'] = packet['rxTime']
                if message_string == "/rt" and not fromMqtt:
                    sendText(interface,packet,f"{ts_toStr(packet['rxTime'])}|UTC\n[ RSSI:{packet['rxRssi']} SNR:{packet['rxSnr']} ]")
                    users[fromId]['lastTS'] = packet['rxTime']                    

    except KeyError as e:
        print(f"Error processing packet: {e}")
        print(traceback.format_exc())

def onConnLost(interface):
    print("---------------Trying to connect---------------")
    time.sleep(10) #seconds
    #meshtastic_interface.connect()
    connectNode(meshtastic_addr,conn_type)

def onConnEst(interface):
    ##time.sleep(30) #seconds
    node_info = interface.getMyNodeInfo()
    print(f"---------------Connected to: {node_info['user']['longName']}---------------")
    
pub.subscribe(onReceive, 'meshtastic.receive')
pub.subscribe(onConnLost,'meshtastic.connection.lost')
pub.subscribe(onConnEst, 'meshtastic.connection.established')

connectNode(meshtastic_addr,conn_type)

while True:
    pass

#meshtastic_interface.close()