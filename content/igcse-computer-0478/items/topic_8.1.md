# Topic 8.1 — Cyber Security Threats

## Items File

**Item 1 [F]**
Question: What is malware and name two examples of malware types.
Answer: Malware (malicious software) is software designed to damage, disrupt, or gain unauthorised access to computer systems. Two examples are viruses and worms.
Difficulty: F
Topic: 8.1
Explanation: Malware encompasses a wide range of hostile software including viruses, worms, trojans, ransomware, spyware, and adware, each with different propagation methods and objectives.
Tags: malware, viruses, worms

**Item 2 [F]**
Question: What is a computer virus?
Answer: A computer virus is a type of malware that attaches itself to legitimate programs or files and spreads when the infected program is run or the file is opened. It requires user action to spread and typically carries a malicious payload.
Difficulty: F
Topic: 8.1
Explanation: Viruses distinguish themselves from worms by requiring a host program and typically some form of human interaction (opening a file, running a program) to propagate.
Tags: virus, malware

**Item 3 [F]**
Question: What is a trojan horse program?
Answer: A trojan (trojan horse) is malware that disguises itself as legitimate or desirable software to trick users into installing it. Unlike viruses, trojans do not self-replicate and rely entirely on social engineering to spread.
Difficulty: F
Topic: 8.1
Explanation: The name derives from the Greek legend of the Trojan Horse. Trojans create backdoors, steal data, or provide remote control to attackers, but they cannot spread on their own without user installation.
Tags: trojan, malware, social-engineering

**Item 4 [F]**
Question: What is ransomware?
Answer: Ransomware is a type of malware that encrypts the victim's files or locks the computer, demanding a payment (ransom) in exchange for restoring access. Payment is typically demanded in cryptocurrency.
Difficulty: F
Topic: 8.1
Explanation: Ransomware attacks have become increasingly sophisticated, with operators using double extortion (threatening to publish stolen data if ransom is not paid) to pressure victims into paying.
Tags: ransomware, malware

**Item 5 [F]**
Question: What is social engineering in the context of cyber security?
Answer: Social engineering is a psychological manipulation technique used to trick people into divulging confidential information or performing actions that compromise security, such as revealing passwords or opening malicious attachments.
Difficulty: F
Topic: 8.1
Explanation: Social engineering exploits human psychology rather than technical vulnerabilities, making it difficult to defend against with purely technical security measures.
Tags: social-engineering, human-factors

**Item 6 [F]**
Question: Name two methods that can help protect against cyber security threats.
Answer: Any two of: using antivirus software, keeping software updated, using strong unique passwords with 2FA, being cautious of suspicious emails and links, regularly backing up data, using a firewall.
Difficulty: F
Topic: 8.1
Explanation: A layered approach (defence-in-depth) combining multiple protective measures is the most effective strategy against the diverse range of cyber threats.
Tags: protection, security-measures

**Item 7 [S]**
Question: Explain the key differences between a virus and a worm.
Answer: A virus requires a host program to attach to and typically needs user action (such as opening a file) to spread. A worm is self-contained and can self-replicate and spread across networks without any user action or host program, making worms significantly faster and more widespread in their propagation.
Difficulty: S
Topic: 8.1
Explanation: Worms exploit vulnerabilities in operating systems or services to spread automatically, which is why patches and updates are critical for preventing worm infections that can spread exponentially within hours.
Tags: virus, worm, malware

**Item 8 [S]**
Question: Describe how a brute force attack works and name one measure that helps defend against it.
Answer: A brute force attack systematically tries every possible combination of characters until the correct password is found. Automated tools can test thousands of combinations per second. defences include using complex passwords, account lockout after failed attempts, CAPTCHA challenges, and rate limiting login attempts.
Difficulty: S
Topic: 8.1
Explanation: The effectiveness of brute force attacks depends on password length and complexity. A 12-character mixed-case alphanumeric password has exponentially more combinations than an 8-character one, making it computationally infeasible to crack within a reasonable timeframe.
Tags: brute-force, password-security

**Item 9 [S]**
Question: What is a denial of service (DoS) attack and how does it affect targeted systems?
Answer: A DoS attack floods a target system (such as a web server) with traffic or requests, overwhelming its resources and making it unable to respond to legitimate users. This results in service outages, lost revenue, and reputational damage.
Difficulty: S
Topic: 8.1
Explanation: DoS attacks exploit the fact that servers have limited capacity. When this capacity is exhausted by attack traffic, genuine users cannot establish connections.
Tags: dos, network-attacks

**Item 10 [S]**
Question: What is a zero-day vulnerability and why is it particularly dangerous?
Answer: A zero-day vulnerability is a previously unknown software flaw that has not yet been patched by the developer. It is particularly dangerous because no fix exists at the time of discovery, giving developers zero days to address it before attacks can occur.
Difficulty: S
Topic: 8.1
Explanation: Zero-day exploits are sold on the black market for high prices and used in targeted attacks because they are virtually undetectable by signature-based security software. They may be used by nation-states, criminal organisations, or discovered by security researchers who responsibly disclose them.
Tags: zero-day, vulnerabilities

**Item 11 [S]**
Question: Explain what SQL injection is and describe a simple method to prevent it.
Answer: SQL injection exploits vulnerabilities in web applications by inserting malicious SQL code into input fields. If unsanitised, this code is executed by the database, potentially allowing attackers to view, modify, or delete data. Prevention involves using parameterised queries (prepared statements) that treat user input as data rather than executable code, and input validation.
Difficulty: S
Topic: 8.1
Explanation: SQL injection was one of the most common web vulnerabilities for over a decade. Successful attacks can expose entire databases including user credentials and personal information.
Tags: sql-injection, web-security

**Item 12 [S]**
Question: Describe what a phishing attack involves and state one way to identify a phishing email.
Answer: Phishing involves sending fraudulent communications, typically emails, that appear to come from a legitimate source to trick recipients into revealing sensitive information or installing malware. One identification method is hovering over links to check if the actual URL matches the displayed text, revealing suspicious or misspelled domains.
Difficulty: S
Topic: 8.1
Explanation: Phishing is a form of social engineering that exploits trust. Spear phishing targets specific individuals while whaling targets high-profile executives.
Tags: phishing, social-engineering

**Item 13 [C]**
Question: Evaluate the effectiveness of antivirus software against modern malware threats and discuss its limitations.
Answer: Traditional signature-based antivirus software is effective against known malware but struggles against zero-day threats and polymorphic malware that changes its code to evade detection. Modern antivirus uses behavioural analysis, heuristic detection, machine learning, and sandboxing to detect unknown threats. Limitations include: inability to protect against social engineering attacks; potential for attackers to test malware against major antivirus engines before deployment; performance overhead; and the arms race dynamic where malware creators continuously develop new evasion techniques.
Difficulty: C
Topic: 8.1
Explanation: The shift toward advanced persistent threats (APTs) used by nation-states and sophisticated criminal organisations means that no single security solution is sufficient, reinforcing the need for defence-in-depth strategies.
Tags: antivirus, security-limitations

**Item 14 [C]**
Question: Analyse how ransomware attacks have evolved and assess the most effective strategies for organisations to protect themselves.
Answer: Ransomware has evolved from simple encrypting malware to sophisticated operations using double and triple extortion (encrypting data, threatening publication, and attacking customers). Effective protection strategies include: maintaining offline backups following the 3-2-1 rule (three copies, two media types, one offsite); regular backup testing and restoration drills; keeping systems patched; network segmentation to limit lateral movement; employee security awareness training; endpoint detection and response (EDR) solutions; and having a tested incident response plan. Paying ransoms should be avoided as it funds future attacks and does not guarantee data recovery.
Difficulty: C
Topic: 8.1
Explanation: The ransomware-as-a-service (RaaS) model has lowered the technical barrier to entry, allowing less sophisticated attackers to launch major campaigns using pre-built ransomware toolkits.
Tags: ransomware, incident-response, backup

**Item 15 [C]**
Question: Compare three types of cyber security threats in terms of their propagation method, potential impact, and primary motivation behind them.
Answer: Phishing propagates through social engineering via email or messages, primarily motivated by credential theft and financial gain. Worms self-replicate across networks automatically, motivated by disruption or creating botnets for hire. SQL injection exploits web application vulnerabilities, motivated by data theft or financial gain. Phishing has high impact because it exploits human psychology and bypasses technical controls; worms cause rapid widespread disruption; SQL injection enables targeted data exfiltration with minimal footprint.
Difficulty: C
Topic: 8.1
Explanation: Understanding attacker motivations (financial, political hacktivism, espionage, destruction) helps organisations prioritise their defences based on which threat actors are most relevant to their sector and assets.
Tags: threats-comparison, attack-methods

**Item 16 [C]**
Question: Critically evaluate the human element in cyber security and explain why social engineering remains effective despite technical security measures.
Answer: The human element is often described as the weakest link in security because technical measures can be circumvented by manipulating people. Social engineering is effective because humans are naturally trusting, curious, helpful, and susceptible to authority. Attackers exploit cognitive biases including authority bias (complying with requests from perceived authority figures) and urgency bias (acting quickly without careful evaluation). Despite security awareness training, phishing success rates remain high because training cannot eliminate human nature and attackers continuously adapt their techniques. Effective mitigation requires combining technical controls (email filtering, URL checking), organisational processes (verification procedures), and ongoing awareness programmes, but organisations must accept that some attacks will succeed.
Difficulty: C
Topic: 8.1
Explanation: Statistics consistently show that over 80% of successful breaches involve some form of human error, making security culture and awareness as important as technical controls.
Tags: social-engineering, human-element, security-culture

**Item 17 [C]**
Question: Discuss the legal and ethical considerations surrounding vulnerability disclosure and zero-day exploits.
Answer: Vulnerability disclosure involves tension between competing interests. Responsible disclosure gives vendors time to develop and deploy patches before public disclosure, protecting users but potentially leaving researchers open to legal action. Full disclosure advocates argue that users have a right to know about risks. Zero-day exploits are particularly controversial because their existence puts all users at risk until patches are available, yet they are valuable to security researchers, law enforcement, and intelligence agencies for offensive operations. Selling zero-days to governments or exploit brokers raises ethical concerns about whether they will be used to surveil citizens or by authoritarian regimes. An ethical framework suggests reporting vulnerabilities to vendors first and only publicly disclosing after patches are available.
Difficulty: C
Topic: 8.1
Explanation: Bug bounty programmes offered by major software vendors provide ethical researchers with legal channels to report vulnerabilities in exchange for recognition and compensation.
Tags: zero-day, responsible-disclosure, ethics

**Item 18 [C]**
Question: Evaluate the effectiveness of multi-factor authentication in preventing common account compromise attacks and analyse its limitations.
Answer: MFA significantly reduces account compromise risk because attackers need both something you know (password) and something you have (phone/token) or something you are (biometric). It effectively blocks credential stuffing (using leaked passwords), brute force (too many factors to guess), and most phishing attacks. However, MFA has limitations: SMS-based MFA is vulnerable to SIM swapping; MFA fatigue attacks can overwhelm users with push notifications until they approve; some MFA implementations use insecure channels; users may disable MFA for convenience; and sophisticated attacks can intercept or redirect authentication codes. Hardware tokens (FIDO2/WebAuthn) provide the strongest protection against these limitations by using public key cryptography that cannot be intercepted.
Difficulty: C
Topic: 8.1
Explanation: The prevalence of MFA bypass techniques in real-world attacks demonstrates that MFA is a critical layer of defence but not a silver bullet. Combining MFA with other measures (device recognition, behavioural analytics, session monitoring) provides more robust protection.
Tags: mfa, authentication, account-security
