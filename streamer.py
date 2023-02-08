# do not import anything else from loss_socket besides LossyUDP
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY
from struct import *
from collections import OrderedDict
class Streamer:
    def __init__(self, dst_ip, dst_port,
                 src_ip=INADDR_ANY, src_port=0):
        """Default values listen on all network interfaces, chooses a random source port,
           and does not introduce any simulated packet loss."""
        self.socket = LossyUDP()
        self.socket.bind((src_ip, src_port))
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.buffer = OrderedDict()
    def send(self, data_bytes: bytes) -> None:
        """Note that data_bytes can be larger than one packet."""
        # Your code goes here!  The code below should be changed!

        # for now I'm just sending the raw application-level data in one UDP payload

        num_packets = len(data_bytes) / 1440
        for i in range(int(num_packets)):
        #    packet = pack('i1440s', i, data_bytes[i*1440:(i+1)*1440])
        #    self.socket.sendto(packet, (self.dst_ip, self.dst_port))
            self.socket.sendto(data_bytes[i*1440:(i+1)*1440], (self.dst_ip, self.dst_port))
        if len(data_bytes) % 1440 != 0:
        #    packet = pack(f'i1440s', int(num_packets), data_bytes[int(num_packets)*1440::])
        #    self.socket.sendto(packet, (self.dst_ip, self.dst_port))
            self.socket.sendto(data_bytes[int(num_packets)*1440::], (self.dst_ip, self.dst_port))
        
    def recv(self) -> bytes:
        """Blocks (waits) if no data is ready to be read from the connection."""
        # your code goes here!  The code below should be changed!
        
        # this sample code just calls the recvfrom method on the LossySocket
        data, addr = self.socket.recvfrom()
       # header, data = unpack('i1440s', data) 
       # last_sequence_num = self.buffer.keys()[-1]
       # self.buffer[header] = data
        # For now, I'll just pass the full UDP payload to the app
        return data.split(b'\x00')[0]

    def close(self) -> None:
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""
        # your code goes here, especially after you add ACKs and retransmissions.
        pass
