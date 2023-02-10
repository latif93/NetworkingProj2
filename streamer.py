# do not import anything else from loss_socket besides LossyUDP
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY
from struct import *
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
import time
class Streamer:
    def __init__(self, dst_ip, dst_port,
                 src_ip=INADDR_ANY, src_port=0):
        """Default values listen on all network interfaces, chooses a random source port,
           and does not introduce any simulated packet loss."""
        self.socket = LossyUDP()
        self.socket.bind((src_ip, src_port))
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.src_ip = src_ip
        self.src_port = src_port
        self.buffer = OrderedDict()
        self.sequence_num_sent = 0
        self.curr_packet_recv = 0
        self.closed = False
        self.ack = 0
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(self.listener)
    def send(self, data_bytes: bytes) -> None:
        """Note that data_bytes can be larger than one packet."""
        # Your code goes here!  The code below should be changed!

        # for now I'm just sending the raw application-level data in one UDP payload
        num_packets = len(data_bytes) / 1439
        for i in range(int(num_packets)):
            packet = pack('ii1439s', self.ack, self.sequence_num_sent, data_bytes[i*1439:(i+1)*1439])
            self.sequence_num_sent += 1
            self.socket.sendto(packet, (self.dst_ip, self.dst_port))
            while self.ack != 1:
                time.sleep(0.01)
            self.ack = 0
        if len(data_bytes) % 1439 != 0:
            packet = pack(f'ii1439s', self.ack, self.sequence_num_sent, data_bytes[int(num_packets)*1439::])
            self.sequence_num_sent += 1
            self.socket.sendto(packet, (self.dst_ip, self.dst_port))
            while self.ack != 1:
                time.sleep(0.01)
            self.ack = 0
                
    #Acks seem to send and self.ack notes this appropriately but then the above while loop doesnt care        

    def listener(self):
        while not self.closed: # a later hint will explain self.closed
            try:
                data, addr = self.socket.recvfrom()
                is_ack, header, data = unpack('ii1439s', data)
                if is_ack == 0:
                    self.buffer[str(header)] = data.split(b'\x00')[0]
                    packet = pack(f'ii1439s', 1, self.sequence_num_sent, data)
                    self.socket.sendto(packet, (self.dst_ip, self.dst_port))
                else:
                    self.ack = 1
                    print(f"ack?: {self.ack}")
            except Exception as e:
                print("listener died!")
                print(e)

    def recv(self) -> bytes:
        """Blocks (waits) if no data is ready to be read from the connection."""
        while str(self.curr_packet_recv) not in self.buffer.keys():
            self.listener
        data = self.buffer[str(self.curr_packet_recv)]
        self.buffer.pop(str(self.curr_packet_recv))
        self.curr_packet_recv +=1
        return data


    def close(self) -> None:
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""
        # your code goes here, especially after you add ACKs and retransmissions.
        self.closed = True
        self.socket.stoprecv()
