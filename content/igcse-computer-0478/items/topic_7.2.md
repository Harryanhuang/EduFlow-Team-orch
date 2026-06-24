# Topic 7.2 — Network Protocols

## Items File

**Item 1 [F]**
Question: Name the four layers of the TCP/IP model in order from top to bottom.
Answer: Application layer, Transport layer, Internet layer, Network Access layer.
Difficulty: F
Topic: 7.2
Explanation: The TCP/IP model is a four-layer model used for network communication. The Application layer handles user interfaces and data formatting, Transport manages end-to-end communication, Internet handles logical addressing and routing, and Network Access deals with physical data transmission.
Tags: tcp-ip, networking, models

**Item 2 [F]**
Question: State the port number used by HTTP and the port number used by HTTPS.
Answer: HTTP uses port 80; HTTPS uses port 443.
Difficulty: F
Topic: 7.2
Explanation: Port numbers identify specific services on a computer. Port 80 is the well-known port for unencrypted HTTP web traffic, while port 443 is used for HTTPS which encrypts data using TLS/SSL.
Tags: http, https, ports

**Item 3 [F]**
Question: What type of data does DNS convert?
Answer: Domain names (human-readable names like www.example.com) into IP addresses (numerical addresses like 192.0.2.1).
Difficulty: F
Topic: 7.2
Explanation: The Domain Name System acts as a phone book for the internet. Without DNS, users would need to memorise IP addresses for every website they want to visit.
Tags: dns, ip-address

**Item 4 [F]**
Question: Which protocol is used to send emails and which port does it commonly use?
Answer: SMTP (Simple Mail Transfer Protocol), commonly using port 25 or 587.
Difficulty: F
Topic: 7.2
Explanation: SMTP is specifically designed for sending and relaying email between mail servers. Port 25 is traditionally used for server-to-server transfer, while port 587 is preferred for client-to-server submission with STARTTLS encryption.
Tags: smtp, email, ports

**Item 5 [F]**
Question: State two differences between TCP and UDP.
Answer: TCP is connection-oriented (establishes a connection before sending data) and reliable (guarantees delivery with error checking); UDP is connectionless (no handshake) and unreliable (does not guarantee delivery or order).
Difficulty: F
Topic: 7.2
Explanation: TCP and UDP are transport layer protocols with different characteristics. TCP provides reliability through acknowledgements and retransmission, making it suitable for web pages and email. UDP sacrifices reliability for speed, making it suitable for video streaming and online gaming.
Tags: tcp, udp, transport-layer

**Item 6 [F]**
Question: What does DHCP stand for and what is its primary function?
Answer: Dynamic Host Configuration Protocol. It automatically assigns IP addresses and other network configuration parameters (such as subnet mask and gateway) to devices on a network.
Difficulty: F
Topic: 7.2
Explanation: DHCP removes the need for manual IP address configuration. When a device joins a network, it requests an IP address from the DHCP server, which leases an address from a pool for a defined period.
Tags: dhcp, ip-address, network-config

**Item 7 [S]**
Question: Explain why HTTPS is preferred over HTTP for online banking transactions.
Answer: HTTPS uses TLS/SSL encryption to protect data in transit, preventing eavesdropping and man-in-the-middle attacks. HTTP sends data in plain text, meaning any intercepted packets would reveal sensitive information like passwords and account numbers.
Difficulty: S
Topic: 7.2
Explanation: HTTPS provides confidentiality and integrity. The encryption ensures that even if data is intercepted, it cannot be read. Certificate authentication also verifies the identity of the website, protecting against spoofing.
Tags: https, encryption, security

**Item 8 [S]**
Question: Describe the role of FTP in file transfers and identify one well-known port number used by FTP.
Answer: FTP (File Transfer Protocol) is used to transfer files between a client and a server over a network. It uses port 21 for control commands and port 20 for active data transfer.
Difficulty: S
Topic: 7.2
Explanation: FTP operates using a client-server model with separate channels for commands and data. Users authenticate with a username and password (or anonymously) and can upload, download, rename, and delete files on the remote server.
Tags: ftp, file-transfer, ports

**Item 9 [S]**
Question: In the context of packet switching, explain what happens when a packet takes a different route to its destination.
Answer: Each packet is sent independently and may travel through different network nodes (routers) along different physical paths. All packets must still arrive at the destination where they are reassembled into the original message.
Difficulty: S
Topic: 7.2
Explanation: Packet switching differs from circuit switching used in telephone networks. Because packets find their own path through the network, if one route becomes congested or fails, packets can be rerouted without disrupting the overall communication.
Tags: packet-switching, networks

**Item 10 [S]**
Question: A user types www.school.edu into a browser. Describe the DNS lookup process that occurs.
Answer: The browser first checks its local cache; if not found, it queries a recursive resolver (usually provided by the ISP). The resolver queries root servers, then TLD servers (.edu), then authoritative servers for school.edu to obtain the IP address, which is returned to the browser.
Difficulty: S
Topic: 7.2
Explanation: DNS uses a distributed hierarchical database. This distributed approach allows the system to scale globally while maintaining fast lookups through caching at multiple levels, reducing the load on authoritative servers.
Tags: dns, web, networking

**Item 11 [S]**
Question: Why is UDP often used for video streaming applications despite not guaranteeing delivery?
Answer: UDP is faster because it does not wait for acknowledgements or retransmit lost packets. For video streaming, occasional packet loss causes minor visual artefacts, which is preferable to the delays caused by TCP retransmission that would make playback stutter.
Difficulty: S
Topic: 7.2
Explanation: The trade-off between reliability and speed makes UDP suitable for real-time applications. Many streaming services use UDP-based protocols like RTMP or WebRTC where speed is more critical than perfect accuracy.
Tags: udp, streaming, real-time

**Item 12 [S]**
Question: Explain how DHCP allocates IP addresses when a device connects to a network.
Answer: The device broadcasts a DHCPDISCOVER message. The DHCP server responds with a DHCPOFFER containing an available IP address from its pool. The device broadcasts a DHCPREQUEST to accept, and the server sends a DHCPACK to confirm the lease.
Difficulty: S
Topic: 7.2
Explanation: This four-step process (DISCOVER, OFFER, REQUEST, ACK) ensures that IP addresses are dynamically allocated rather than permanently assigned. The lease has a time limit, allowing addresses to be reclaimed and reused when devices disconnect.
Tags: dhcp, ip-address, networking

**Item 13 [C]**
Question: Evaluate the impact of packet switching on network reliability compared to circuit switching, using a specific example.
Answer: Packet switching provides superior reliability because if a router fails, packets are automatically rerouted through alternative paths without interrupting communication. In circuit switching, a single broken connection point would terminate the entire session. For example, during internet backbone failures, packet-switched networks continue operating while phone calls on circuit-switched lines may be disconnected.
Difficulty: C
Topic: 7.2
Explanation: The distributed nature of packet switching means there is no single point of failure. However, this flexibility comes with challenges: packets may arrive out of order and require reassembly, and congestion at certain routers can cause variable delays.
Tags: packet-switching, circuit-switching, reliability

**Item 14 [C]**
Question: Discuss why DNS is vulnerable to cache poisoning attacks and how DNSSEC mitigates this threat.
Answer: DNS cache poisoning exploits the fact that DNS responses are not authenticated. An attacker can inject false records into a DNS resolver's cache, redirecting users to malicious websites. DNSSEC (DNS Security Extensions) adds cryptographic signatures to DNS records, allowing resolvers to verify that responses originated from the authoritative server and were not tampered with in transit.
Difficulty: C
Topic: 7.2
Explanation: Without DNSSEC, resolvers must trust the source of DNS data without verification. The chain of trust from root zone to TLD to individual domain must be validated at each level using public key cryptography, making spoofed responses detectable.
Tags: dns, dnssec, security

**Item 15 [C]**
Question: Compare the TCP three-way handshake process with UDP communication in terms of overhead and suitability for different applications.
Answer: TCP requires a three-way handshake (SYN, SYN-ACK, ACK) before data transfer begins, adding latency but ensuring the connection is established. UDP has no handshake, reducing overhead and latency. This makes TCP suitable for applications requiring reliability such as web browsing and email, while UDP is better for real-time applications like VoIP and online gaming where latency is more important than occasional packet loss.
Difficulty: C
Topic: 7.2
Explanation: The handshake overhead of TCP is approximately 1.5 round-trip times before data transfer begins. For short transactions, this can be significant. UDP's zero-overhead approach prioritises responsiveness, which is why it dominates real-time communication despite offering no delivery guarantees.
Tags: tcp, udp, handshake, networking

**Item 16 [C]**
Question: Evaluate the trade-offs between using well-known ports (below 1024) versus higher-numbered ports for network services.
Answer: Well-known ports are reserved and standardised, ensuring all clients know which port to connect to without configuration. They require administrator privileges to bind, reducing the risk of malicious services impersonating well-known ones. However, they are limited in number and inflexible. Higher ports allow multiple instances of the same service, easier testing without privileges, and avoid conflicts but lack standardisation, requiring clients to know specific port numbers.
Difficulty: C
Topic: 7.2
Explanation: Port number allocation is managed by IANA. Using non-standard ports is common in enterprise environments where multiple versions of services run simultaneously or where security through obscurity is layered with other measures.
Tags: ports, networking, security

**Item 17 [C]**
Question: Analyse how email protocols (SMTP, POP3, IMAP) work together to provide a complete email service.
Answer: SMTP handles sending and relaying email from the sender's client to the recipient's mail server and between servers. When the recipient retrieves email, POP3 downloads messages from the server to the client (typically deleting server copies), while IMAP synchronises messages across multiple devices without deleting server copies. SMTP operates on ports 25/587, POP3 on port 110, and IMAP on port 143.
Difficulty: C
Topic: 7.2
Explanation: The separation of concerns between these protocols enables flexible email access. A user might send via their workplace SMTP server while reading from home using IMAP, with the message having traversed multiple SMTP servers in transit.
Tags: smtp, pop3, imap, email

**Item 18 [C]**
Question: Discuss the security implications of using FTP versus SFTP and explain why SFTP is now preferred in enterprise environments.
Answer: FTP transmits credentials and data in plain text, making it vulnerable to packet sniffing and man-in-the-middle attacks. SFTP (SSH File Transfer Protocol) runs over an encrypted SSH connection, protecting both authentication credentials and file contents. In enterprise environments, regulatory compliance requirements for data protection, the prevalence of remote work exposing traffic to untrusted networks, and the need to protect intellectual property make SFTP the mandatory choice.
Difficulty: C
Topic: 7.2
Explanation: SFTP is not technically an FTP protocol but rather a protocol that runs over SSH. This distinction is important because it means SFTP inherits all of SSH's security features including strong authentication and encryption, while using a single port (22) that is typically allowed through firewalls.
Tags: ftp, sftp, security, encryption
