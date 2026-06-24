# Topic 7.3 — Network Security

## Items File

**Item 1 [F]**
Question: What is a firewall and what type of traffic does it typically block?
Answer: A firewall is a network security system that monitors and controls incoming and outgoing network traffic based on predefined security rules. It typically blocks unauthorised access attempts, traffic from suspicious sources, and connections to known malicious IP addresses.
Difficulty: F
Topic: 7.3
Explanation: Firewalls act as a barrier between trusted internal networks and untrusted external networks like the internet. They can be hardware-based, software-based, or a combination of both.
Tags: firewall, network-security

**Item 2 [F]**
Question: What is the difference between symmetric and asymmetric encryption?
Answer: Symmetric encryption uses the same key to encrypt and decrypt data; asymmetric encryption uses a pair of keys (a public key to encrypt and a private key to decrypt).
Difficulty: F
Topic: 7.3
Explanation: Symmetric encryption is faster and suitable for large data volumes, but key distribution is challenging. Asymmetric encryption solves the key distribution problem but is computationally slower, so it is often used to exchange symmetric keys.
Tags: encryption, cryptography

**Item 3 [F]**
Question: State two authentication methods used to verify user identity.
Answer: Any two of: password authentication, biometric authentication (fingerprint, facial recognition, iris scan), two-factor authentication (2FA), security token, smart card.
Difficulty: F
Topic: 7.3
Explanation: Authentication methods typically fall into three categories: something you know (password), something you have (token), and something you are (biometric). Combining multiple methods provides stronger security.
Tags: authentication, security

**Item 4 [F]**
Question: What is a VPN and what is its primary purpose?
Answer: A Virtual Private Network (VPN) creates an encrypted, secure connection over a public network (typically the internet). Its primary purpose is to allow remote users to access a private network securely as if they were physically connected to it.
Difficulty: F
Topic: 7.3
Explanation: VPNs extend the private network across public infrastructure by encapsulating and encrypting data packets, ensuring that sensitive information cannot be intercepted by third parties on the same network.
Tags: vpn, encryption, network-security

**Item 5 [F]**
Question: Name three common network security threats.
Answer: Any three of: phishing, malware (including viruses, worms, trojans, ransomware), distributed denial of service (DDoS) attacks, man-in-the-middle attacks, SQL injection, brute force attacks.
Difficulty: F
Topic: 7.3
Explanation: Understanding common threats is essential for implementing appropriate security measures. Different threats require different defensive strategies.
Tags: threats, security, malware

**Item 6 [F]**
Question: What is meant by the term data interception in the context of network security?
Answer: Data interception is the unauthorized capture of data as it travels across a network. Attackers use techniques like packet sniffing to capture sensitive information such as passwords, credit card numbers, or personal data being transmitted between devices.
Difficulty: F
Topic: 7.3
Explanation: Data interception is particularly dangerous on unsecured networks such as public WiFi. Without encryption, anyone with network access can potentially capture and read transmitted data.
Tags: data-interception, network-security

**Item 7 [S]**
Question: Explain how a firewall uses packet filtering to protect a network.
Answer: Packet filtering firewalls examine each packet's header information including source and destination IP addresses, port numbers, and protocol type. Packets that do not match the configured security rules are dropped, while matching packets are allowed through.
Difficulty: S
Topic: 7.3
Explanation: Stateless packet filtering examines each packet independently, while stateful inspection tracks the state of active connections. This allows firewalls to distinguish legitimate traffic from malicious traffic based on context.
Tags: firewall, packet-filtering

**Item 8 [S]**
Question: Describe how asymmetric encryption is used in practice when a user sends a secure message.
Answer: The sender obtains the recipient's public key (which is openly available). They encrypt the message using this public key. Only the recipient's corresponding private key, which they keep secret, can decrypt the message. The sender's private key can also be used to create a digital signature that verifies the sender's identity.
Difficulty: S
Topic: 7.3
Explanation: This system solves the key distribution problem because the public key can be shared freely without compromising security. The private key never needs to be transmitted, making it impossible for attackers to intercept.
Tags: asymmetric-encryption, public-key

**Item 9 [S]**
Question: What is phishing and describe one method used to identify a phishing attempt.
Answer: Phishing is a social engineering attack where attackers send fraudulent messages designed to trick recipients into revealing sensitive information or installing malware. A common identification method is checking the sender's email address carefully for subtle misspellings or mismatched domains.
Difficulty: S
Topic: 7.3
Explanation: Phishing attacks often create convincing replicas of legitimate websites or emails. Other red flags include urgent language demanding immediate action, suspicious links (hover to reveal true destination), and requests for personal information.
Tags: phishing, social-engineering

**Item 10 [S]**
Question: Explain how two-factor authentication (2FA) improves security compared to password-only authentication.
Answer: 2FA requires two different types of authentication factors, such as something you know (password) and something you have (mobile phone receiving an SMS code or authenticator app). Even if an attacker obtains the password, they cannot access the account without also having the second factor.
Difficulty: S
Topic: 7.3
Explanation: 2FA addresses the weakness that passwords can be guessed, stolen, or leaked in data breaches. The second factor is independent of the password and cannot be obtained through the same attack vectors.
Tags: 2fa, authentication, security

**Item 11 [S]**
Question: Describe how a man-in-the-middle (MITM) attack works and how HTTPS helps prevent it.
Answer: In a MITM attack, the attacker secretly intercepts and potentially alters communication between two parties who believe they are communicating directly with each other. HTTPS prevents MITM attacks by using TLS encryption with server certificates that verify the server's identity, making it impossible for an attacker to decrypt or modify the traffic without detection.
Difficulty: S
Topic: 7.3
Explanation: Without encryption and certificate validation, attackers on the same network can redirect traffic through their own systems. HTTPS with proper certificate validation ensures that even if traffic is intercepted, it cannot be read or modified.
Tags: mitm, https, encryption

**Item 12 [S]**
Question: What is the difference between a DDoS attack and a regular DoS attack?
Answer: A DoS attack originates from a single source attempting to overwhelm a target system. A DDoS attack uses multiple distributed sources (often a botnet of compromised computers) to flood the target simultaneously, making it much harder to defend against.
Difficulty: S
Topic: 7.3
Explanation: DDoS attacks are particularly difficult to mitigate because the traffic comes from many different IP addresses and locations, making it hard to distinguish legitimate traffic from attack traffic. Botnets can generate millions of requests per second.
Tags: ddos, dos, network-attacks

**Item 13 [C]**
Question: Evaluate the effectiveness of firewalls as a sole security measure, explaining why a defence-in-depth strategy is necessary.
Answer: Firewalls are effective at controlling network traffic based on rules but cannot inspect encrypted traffic content, cannot protect against insider threats or social engineering, and can be bypassed by attacks that appear legitimate. A defence-in-depth strategy uses multiple overlapping security layers including firewalls, intrusion detection systems, antivirus software, user education, and encryption. If one layer fails, others provide protection.
Difficulty: C
Topic: 7.3
Explanation: No single security measure is foolproof. Firewalls cannot see inside encrypted tunnels, so malware delivered via HTTPS will pass through undetected. Similarly, attacks that trick users into revealing credentials bypass technical controls entirely.
Tags: firewall, defence-in-depth, security

**Item 14 [C]**
Question: Compare RSA and AES encryption algorithms in terms of their purpose, speed, and typical use cases.
Answer: RSA is an asymmetric algorithm used primarily for key exchange and digital signatures. It is slow due to complex mathematical operations with large prime numbers. AES is a symmetric algorithm used for bulk data encryption. It is significantly faster and suitable for encrypting large files and data streams. In practice, RSA is used to securely exchange AES keys, then AES encrypts the actual data.
Difficulty: C
Topic: 7.3
Explanation: This hybrid approach combines the strengths of both algorithms. RSA's key exchange capability solves the fundamental problem of how to share symmetric keys securely, while AES provides efficient bulk encryption for day-to-day data protection.
Tags: rsa, aes, encryption, cryptography

**Item 15 [C]**
Question: Analyse the ethical and legal considerations when implementing biometric authentication systems.
Answer: Biometric systems raise privacy concerns because biometric data, unlike passwords, cannot be changed if stolen. There are risks of data breaches exposing immutable personal characteristics. Legal frameworks like GDPR treat biometric data as special category data requiring explicit consent and stringent protection. Organisations must weigh security benefits against the irreversible nature of biometric compromise and potential for surveillance misuse.
Difficulty: C
Topic: 7.3
Explanation: Once fingerprints or facial recognition data is compromised, individuals cannot change their biometrics the way they can change a password. This permanence creates lifelong security risks if databases are breached.
Tags: biometrics, privacy, ethics, gdpr

**Item 16 [C]**
Question: Evaluate the security implications of using public WiFi networks and explain how VPN technology mitigates these risks.
Answer: Public WiFi networks are inherently insecure because traffic is transmitted over radio waves that can be intercepted by anyone within range. Without encryption, attackers can capture passwords, emails, and personal data using packet sniffing tools. VPNs mitigate these risks by creating an encrypted tunnel between the user's device and a VPN server, ensuring that all traffic is encrypted and authenticated, preventing eavesdropping even on hostile networks.
Difficulty: C
Topic: 7.3
Explanation: The encryption provided by VPN protocols like OpenVPN, WireGuard, and IPSec makes intercepted packets unreadable without the decryption key. However, users must trust the VPN provider since all traffic passes through their servers.
Tags: vpn, wifi-security, encryption

**Item 17 [C]**
Question: Discuss the role of digital certificates and certificate authorities in establishing trust in online communications.
Answer: Digital certificates bind a public key to an entity's identity, verified by a trusted Certificate Authority (CA). When a browser connects to a website over HTTPS, the server presents its certificate. The browser verifies the certificate against trusted root CAs embedded in the browser. This chain of trust ensures that users are communicating with the genuine website and not an impersonator attempting a man-in-the-middle attack.
Difficulty: C
Topic: 7.3
Explanation: The CA ecosystem has vulnerabilities, as demonstrated by incidents where compromised CAs issued fraudulent certificates. Certificate transparency logs and initiatives like Certificate Authority Authorization (CAA) records help detect and prevent certificate misuse.
Tags: certificates, ca, https, trust

**Item 18 [C]**
Question: Evaluate the effectiveness of different authentication methods against various attack vectors, recommending an appropriate authentication strategy for a banking application.
Answer: Passwords alone are vulnerable to phishing, brute force, and credential stuffing attacks. SMS-based 2FA is vulnerable to SIM swapping. Authenticator apps and hardware tokens provide stronger protection. For a banking application, I recommend multi-layered authentication: strong password policy combined with authenticator app-based 2FA, transaction signing for high-value operations, device fingerprinting, and behavioural analytics to detect anomalous access patterns. This addresses the range of attack vectors while balancing usability for legitimate customers.
Difficulty: C
Topic: 7.3
Explanation: Banking applications face sophisticated threats including targeted phishing, insider fraud, and account takeover attempts. The cost of security breaches (financial loss, regulatory penalties, reputational damage) justifies implementing stronger authentication measures than typical consumer applications.
Tags: authentication, banking, security, 2fa
