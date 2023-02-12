# do not import anything else from loss_socket besides LossyUDP
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY
from struct import *
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
import time
import hashlib
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
        self.fin_ack = 0

    def send(self, data_bytes: bytes) -> None:
        """Note that data_bytes can be larger than one packet."""
        # Your code goes here!  The code below should be changed!
        # for now I'm just sending the raw application-level data in one UDP payload
        num_packets = len(data_bytes) / 1423
        for i in range(int(num_packets)):
            m = hashlib.md5()
            m.update(data_bytes[i*1423:(i+1)*1423])
            packet = pack('16sii1423s', m.digest(), self.ack, self.sequence_num_sent, data_bytes[i*1423:(i+1)*1423])
            self.sequence_num_sent += 1
            self.socket.sendto(packet, (self.dst_ip, self.dst_port))
            count = 0
            while self.ack != 1:
                time.sleep(0.01)
                count += 0.01
                if count >= 0.25:
                    self.socket.sendto(packet, (self.dst_ip, self.dst_port))
                    count = 0
            self.ack = 0
        if len(data_bytes) % 1423 != 0:
            m = hashlib.md5()
            m.update(data_bytes[int(num_packets)*1423::])
            print(f"bro:   {len(data_bytes[int(num_packets)*1423::])}")
            packet = pack(f'16sii1423s', m.digest(), self.ack, self.sequence_num_sent, data_bytes[int(num_packets)*1423::])
            self.sequence_num_sent += 1
            self.socket.sendto(packet, (self.dst_ip, self.dst_port))
            count = 0
            while self.ack != 1:
                time.sleep(0.01)
                count += 0.01
                if count >= 0.25:
                    self.socket.sendto(packet, (self.dst_ip, self.dst_port))
                    count = 0
            self.ack = 0
                
    #Acks seem to send and self.ack notes this appropriately but then the above while loop doesnt care        

    def listener(self):
        while not self.closed: # a later hint will explain self.closed
            try:
                data, addr = self.socket.recvfrom()
                checksum, packet_type, header, data = unpack('16sii1423s', data)
                m = hashlib.md5()
                m.update(data.split(b'\x00')[0])
                hashed_recv_data = m.digest()

                if checksum == hashed_recv_data:
                    
                    if packet_type == 0: #if data packet
                        self.buffer[str(header)] = data.split(b'\x00')[0]
                        packet = pack(f'16sii1423s', checksum, 1, self.sequence_num_sent, data)
                        self.socket.sendto(packet, (self.dst_ip, self.dst_port))
                    elif packet_type == 2: #if fin packet
                        packet = pack(f'16sii1423s', checksum, 3, self.sequence_num_sent, data)
                        self.socket.sendto(packet, (self.dst_ip, self.dst_port))
                    elif packet_type == 3: #if fin_ack packet
                        self.fin_ack = 1
                    else:                  # if ack packet
                        self.ack = 1
                    
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
        m = hashlib.md5()
        m.update("a".encode())     
        packet = pack(f'16sii1423s', m.digest(), 2, self.sequence_num_sent, "a".encode()) #send fin packet
        self.socket.sendto(packet, (self.dst_ip, self.dst_port))
        count = 0
        while self.fin_ack != 1:
            time.sleep(0.01)
            count += 0.01
            if count >= 0.25:
                self.socket.sendto(packet, (self.dst_ip, self.dst_port))
                count = 0
        time.sleep(2.0)
        self.closed = True
        self.socket.stoprecv()
        return
