# Topic 7.1 — Network Types and Protocols
## Items File

**Item 1 [F]**
Question: What is a LAN (Local Area Network)?
Answer: A LAN is a network confined to a small geographic area, such as a single building, school, or home. It is owned and managed by one organisation.
Difficulty: F
Topic: 7.1
Explanation: LANs are characterised by high speed and low latency. Devices are connected using cables (Ethernet) or Wi-Fi.
Tags: LAN, local area network, network types

**Item 2 [F]**
Question: What is a WAN (Wide Area Network)?
Answer: A WAN is a network that spans a large geographic area, such as a country or the entire globe. The Internet is the largest WAN.
Difficulty: F
Topic: 7.1
Explanation: WANs connect multiple LANs together. They typically use public telecommunications infrastructure and have lower speeds than LANs.
Tags: WAN, wide area network, Internet, network types

**Item 3 [F]**
Question: State two differences between a LAN and a WAN.
Answer: (1) Geographic area: LAN is small; WAN is large. (2) Speed: LAN is faster; WAN is slower. (3) Ownership: LAN is privately owned; WAN uses public infrastructure.
Difficulty: F
Topic: 7.1
Explanation: LANs are typically owned by a single organisation; WANs span multiple organisations and geographic boundaries.
Tags: LAN, WAN, comparison, network differences

**Item 4 [F]**
Question: What is a client-server network?
Answer: A client-server network has a central server that provides services (files, printing, web pages) to client computers that request them.
Difficulty: F
Topic: 7.1
Explanation: Clients (user computers) request services from the server. The server authenticates users, stores data, and manages network resources.
Tags: client-server, server, client, network model

**Item 5 [S]**
Question: What is a peer-to-peer (P2P) network?
Answer: In a P2P network, all computers are equal peers — each can act as both a client and a server, sharing resources directly with other peers without a central server.
Difficulty: S
Topic: 7.1
Explanation: Examples: BitTorrent, Skype. P2P is decentralised. No central server means no single point of failure, but security management is harder.
Tags: peer-to-peer, P2P, decentralised, network model

**Item 6 [S]**
Question: What is the role of a router in a network?
Answer: A router connects different networks and directs data packets between them, choosing the best path for data to travel from source to destination.
Difficulty: S
Topic: 7.1
Explanation: A home router connects the home LAN to the Internet (WAN). It uses IP addresses to route packets.
Tags: router, routing, network device, IP address

**Item 7 [S]**
Question: What is the purpose of a switch in a computer network?
Answer: A switch connects devices within a single network (LAN). It uses MAC addresses to forward data only to the device that is the intended recipient.
Difficulty: S
Topic: 7.1
Explanation: Unlike a hub (which broadcasts to all devices), a switch learns which MAC addresses are on each port and forwards frames selectively.
Tags: switch, MAC address, LAN, network device

**Item 8 [S]**
Question: What is the difference between a hub and a switch?
Answer: A hub broadcasts incoming data to all connected devices. A switch forwards data only to the specific device that is the intended recipient, based on MAC addresses.
Difficulty: S
Topic: 7.1
Explanation: Hubs are simpler but inefficient. Switches are faster and more secure because data goes only to the intended recipient.
Tags: hub, switch, comparison, LAN device

**Item 9 [S]**
Question: What does HTTP stand for and what is its purpose?
Answer: HyperText Transfer Protocol. HTTP defines how web browsers and servers communicate to transfer web pages and other resources.
Difficulty: S
Topic: 7.1
Explanation: When a browser requests a webpage, it sends an HTTP request. The server responds with the requested resource.
Tags: HTTP, web protocol, hypertext, request-response

**Item 10 [S]**
Question: What is the difference between HTTP and HTTPS?
Answer: HTTPS is HTTP with encryption (SSL/TLS). HTTPS secures data in transit, preventing eavesdropping and tampering. HTTP transmits data in plain text.
Difficulty: S
Topic: 7.1
Explanation: HTTPS is required for sensitive data (banking, passwords). The browser shows a padlock icon for HTTPS sites.
Tags: HTTP, HTTPS, encryption, SSL, security

**Item 11 [S]**
Question: What is TCP/IP?
Answer: TCP/IP (Transmission Control Protocol / Internet Protocol) is the fundamental protocol suite of the Internet. IP handles addressing and routing; TCP ensures reliable, ordered delivery.
Difficulty: S
Topic: 7.1
Explanation: IP: sends packets from source to destination (unreliable, no guarantee of delivery). TCP: on top of IP, ensures all packets arrive in order and without errors.
Tags: TCP/IP, protocol suite, Internet, reliability

**Item 12 [S]**
Question: What is a MAC address?
Answer: A MAC (Media Access Control) address is a unique hardware identifier assigned to a network interface card (NIC). It is 48 bits long, written as six pairs of hex digits.
Difficulty: S
Topic: 7.1
Explanation: Example: 00:1A:2B:3C:4D:5E. MAC addresses identify devices at the data link layer (Layer 2). They are permanent and assigned by the manufacturer.
Tags: MAC address, hardware address, network layer, NIC

**Item 13 [S]**
Question: What is the purpose of DHCP?
Answer: DHCP (Dynamic Host Configuration Protocol) automatically assigns IP addresses to devices on a network, so administrators do not need to configure them manually.
Difficulty: S
Topic: 7.1
Explanation: When a device connects to a network, DHCP assigns it an IP address from a pool. The address is "leased" and may change when the lease expires.
Tags: DHCP, IP address, automatic configuration, network protocol

**Item 14 [C]**
Question: Explain what DNS (Domain Name System) does.
Answer: DNS translates human-readable domain names (like www.google.com) into IP addresses that computers use to identify each other on the Internet.
Difficulty: C
Topic: 7.1
Explanation: Without DNS, users would need to remember IP addresses (e.g., 142.250.80.46) for every website. DNS works like a distributed phonebook.
Tags: DNS, domain name, IP address, name resolution

**Item 15 [C]**
Question: What is FTP used for?
Answer: FTP (File Transfer Protocol) is used to transfer files between a client and a server over a network.
Difficulty: C
Topic: 7.1
Explanation: FTP allows uploading (uploading files from local computer to server) and downloading (retrieving files from server). FTP transmits credentials in plain text (unless FTPS/SFTP is used).
Tags: FTP, file transfer, upload, download

**Item 16 [C]**
Question: A user browses to https://www.example.com. Describe the steps involved at a high level.
Answer: (1) Browser uses DNS to resolve www.example.com to an IP address. (2) Browser opens a TCP connection to the server on port 443 (HTTPS). (3) TLS handshake establishes encryption. (4) Browser sends an HTTPS GET request. (5) Server responds with the webpage content.
Difficulty: C
Topic: 7.1
Explanation: Each step uses specific protocols: DNS (UDP), TCP, TLS, HTTP. The process is layered — each layer handles one concern.
Tags: HTTPS, DNS, TCP, TLS, protocol stack

**Item 17 [C]**
Question: What is a subnet mask and what is its purpose?
Answer: A subnet mask determines which part of an IP address identifies the network and which part identifies the host. It is used to divide a network into sub-networks (subnets).
Difficulty: C
Topic: 7.1
Explanation: For example, in 192.168.1.0/24, the /24 (255.255.255.0) mask means the first 24 bits are the network portion. This allows routing to know whether a destination is local or remote.
Tags: subnet mask, IP address, network, subnet

**Item 18 [C]**
Question: Compare star topology and bus topology in terms of advantages and disadvantages.
Answer: Star: advantage — if one node fails, others continue; disadvantage — if the central hub fails, all nodes lose connectivity. Bus: advantage — uses less cable; disadvantage — a break in the main cable brings down the entire network.
Difficulty: C
Topic: 7.1
Explanation: Star topology is the most common in modern LANs. Bus topology is largely obsolete.
Tags: star topology, bus topology, network topology, comparison
