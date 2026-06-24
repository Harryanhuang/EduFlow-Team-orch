# Topic 7.4 — Cloud Computing

## Items File

**Item 1 [F]**
Question: What do the acronyms IaaS, PaaS, and SaaS stand for?
Answer: IaaS = Infrastructure as a Service; PaaS = Platform as a Service; SaaS = Software as a Service.
Difficulty: F
Topic: 7.4
Explanation: These are the three main service models of cloud computing, representing different levels of abstraction and management responsibility transferred to the cloud provider.
Tags: iaas, paas, saas, cloud-models

**Item 2 [F]**
Question: Give one example of an SaaS application commonly used in education.
Answer: Google Workspace (Gmail, Docs, Drive), Microsoft 365 (Office Online, OneDrive), or learning platforms such as Google Classroom or Moodle.
Difficulty: F
Topic: 7.4
Explanation: SaaS applications are accessed via a web browser and do not require installation. The provider manages everything including infrastructure, platforms, and software updates.
Tags: saas, education

**Item 3 [F]**
Question: What is the difference between a public cloud and a private cloud?
Answer: A public cloud is owned and operated by a third-party provider and shared across multiple organisations; a private cloud is dedicated to a single organisation, either hosted on-premises or by a dedicated provider, offering greater control and customisation.
Difficulty: F
Topic: 7.4
Explanation: Public clouds offer cost efficiency through resource sharing but less control. Private clouds provide enhanced security, customisation, and guaranteed performance but require significant capital investment and IT expertise.
Tags: public-cloud, private-cloud

**Item 4 [F]**
Question: What is meant by cloud storage?
Answer: Cloud storage is a service where data is stored on remote servers accessible via the internet, managed by a cloud storage provider who handles maintenance, backups, and physical security of the servers.
Difficulty: F
Topic: 7.4
Explanation: Users can access their stored data from any device with an internet connection, making it ideal for file sharing and backup purposes.
Tags: cloud-storage

**Item 5 [F]**
Question: State one advantage and one disadvantage of cloud computing for a small business.
Answer: Advantage: reduced capital expenditure (no need to buy and maintain physical servers); Disadvantage: dependency on internet connectivity and potential data security concerns when storing data on third-party servers.
Difficulty: F
Topic: 7.4
Explanation: Cloud computing allows small businesses to access enterprise-grade infrastructure without large upfront investments, but they must accept the trade-offs of reduced control and internet dependency.
Tags: cloud-computing, advantages, disadvantages

**Item 6 [F]**
Question: What is a hybrid cloud environment?
Answer: A hybrid cloud combines public and private cloud infrastructure, allowing data and applications to be shared between them. Organisations can keep sensitive data in a private cloud while using public cloud resources for scalable workloads.
Difficulty: F
Topic: 7.4
Explanation: Hybrid cloud provides flexibility by allowing workloads to move between private and public clouds based on changing needs for compute and storage.
Tags: hybrid-cloud

**Item 7 [S]**
Question: Describe what IaaS provides and give an example of when it would be suitable for an organisation.
Answer: IaaS provides virtualised computing resources including virtual machines, storage, and networking. An organisation would use IaaS when it needs full control over the operating system and applications but wants to avoid the cost and complexity of managing physical hardware, such as when migrating from on-premises servers to the cloud.
Difficulty: S
Topic: 7.4
Explanation: IaaS is the most flexible cloud service model, giving organisations the ability to scale resources up or down based on demand while maintaining control over the software stack.
Tags: iaas, cloud-services

**Item 8 [S]**
Question: Explain the concept of data sovereignty and why it is a concern in cloud computing.
Answer: Data sovereignty refers to the legal jurisdiction under which data is stored and processed, governed by the laws of the country where the data centre is located. In cloud computing, data may be stored in any country where the provider has data centres, potentially subjecting it to foreign laws that conflict with local regulations regarding privacy, surveillance, or data access.
Difficulty: S
Topic: 7.4
Explanation: Some countries require certain types of data (especially government or healthcare data) to remain within national borders. Organisations must verify where their data is stored to ensure compliance with data protection regulations.
Tags: data-sovereignty, privacy, regulations

**Item 9 [S]**
Question: What privacy issues arise when organisations store personal data in the cloud?
Answer: Privacy issues include: data being stored in jurisdictions with different privacy laws; risk of data breaches exposing personal information; lack of direct control over who can access the data; potential for data to be shared with third parties without clear consent; and uncertainty about data handling practices of the cloud provider.
Difficulty: S
Topic: 7.4
Explanation: Under regulations like GDPR, organisations remain responsible for the personal data they store in the cloud, including ensuring the cloud provider meets required security and privacy standards.
Tags: privacy, gdpr, cloud-storage

**Item 10 [S]**
Question: Explain why cloud computing can improve reliability compared to on-premises solutions.
Answer: Cloud providers operate multiple geographically distributed data centres with redundant systems, automatic failover, and 24/7 monitoring. If one data centre fails, services automatically switch to another with minimal downtime. They also provide regular automated backups and disaster recovery capabilities that would be expensive for individual organisations to implement.
Difficulty: S
Topic: 7.4
Explanation: Major cloud providers guarantee high availability (typically 99.9% or higher) through Service Level Agreements (SLAs), offering financial compensation if targets are not met.
Tags: reliability, uptime, disaster-recovery

**Item 11 [S]**
Question: What is meant by internet connectivity in the context of cloud computing limitations?
Answer: Cloud services require a stable internet connection to access applications, data, and computing resources. Without connectivity, users cannot reach their data or use cloud-hosted applications, effectively making local resources unavailable.
Difficulty: S
Topic: 7.4
Explanation: This creates a dependency that can be problematic in areas with unreliable internet, during internet outages, or for applications requiring extremely low latency where local processing would be preferable.
Tags: internet-connectivity, limitations

**Item 12 [S]**
Question: Describe Platform as a Service (PaaS) and identify a situation where it would be preferred over IaaS.
Answer: PaaS provides a platform for developing, running, and managing applications without the complexity of building and maintaining the underlying infrastructure. PaaS would be preferred over IaaS when a development team wants to focus purely on application code without managing servers, operating systems, or middleware, such as when deploying a web application or API service.
Difficulty: S
Topic: 7.4
Explanation: PaaS automatically handles scaling, load balancing, and runtime environments, allowing developers to push code directly without configuring servers, making it ideal for agile development teams.
Tags: paas, iaas, cloud-services

**Item 13 [C]**
Question: Evaluate the economic advantages and disadvantages of cloud computing versus maintaining on-premises IT infrastructure.
Answer: Cloud computing eliminates capital expenditure on hardware (CapEx) by converting to operational expenditure (OpEx), reducing upfront costs and allowing pay-as-you-go pricing. However, long-term cloud usage can become more expensive than ownership due to subscription costs, data transfer fees, and vendor lock-in. On-premises infrastructure requires large upfront investment but has predictable long-term costs and no dependency on ongoing subscriptions. Hidden costs of cloud include data egress charges, API costs, and the need for staff training.
Difficulty: C
Topic: 7.4
Explanation: Total cost of ownership analysis must consider not just hardware costs but also power, cooling, staffing, maintenance, and the opportunity cost of capital tied up in infrastructure.
Tags: cloud-costs, economics, capex, opex

**Item 14 [C]**
Question: Analyse the security risks associated with multi-tenancy in public cloud environments and explain how cloud providers address these risks.
Answer: Multi-tenancy means multiple customers share computing resources (servers, storage, networks), raising risks of data leakage between tenants, side-channel attacks, and resource contention. Cloud providers address these risks through virtualisation-based isolation, encrypted storage, separate virtual networks per customer, regular security audits, compliance certifications, and intrusion detection systems. However, customers must also implement their own security measures including access controls, encryption, and proper configuration.
Difficulty: C
Topic: 7.4
Explanation: The shared responsibility model defines which security aspects are handled by the provider versus the customer. Infrastructure-as-a-Service providers secure the physical infrastructure while customers secure their own virtual machines and data.
Tags: multi-tenancy, security, shared-responsibility

**Item 15 [C]**
Question: Discuss how organisations can address the challenges of data sovereignty when selecting a cloud provider for sensitive data.
Answer: Organisations should audit potential providers for data centre locations and ensure compliance with relevant regulations. They can implement data classification to determine which data can be stored in public clouds and which requires private or on-premises solutions. Using providers that offer explicit data residency guarantees, encryption with customer-managed keys, and comprehensive data processing agreements helps ensure legal compliance. Regular compliance audits and understanding the provider's incident response procedures provide additional assurance.
Difficulty: C
Topic: 7.4
Explanation: The European GDPR framework requires organisations to ensure adequate data protection regardless of where data is processed, making contractual and technical controls essential.
Tags: data-sovereignty, compliance, gdpr

**Item 16 [C]**
Question: Evaluate the impact of cloud computing on business continuity and disaster recovery strategies.
Answer: Cloud computing significantly improves business continuity by providing geographic redundancy, automatic failover, and rapid scalability that would be prohibitively expensive on-premises. Disaster recovery as a Service (DRaaS) enables organisations to replicate their environments to the cloud and fail over in minutes rather than days. However, cloud-based DR still depends on internet connectivity, creating a single point of failure for recovery. Organisations must also understand their provider's RTO (Recovery Time Objective) and RPO (Recovery Point Objective) guarantees and test recovery procedures regularly.
Difficulty: C
Topic: 7.4
Explanation: Traditional DR required maintaining a secondary data centre, often in a different geographic region, representing significant capital investment. Cloud-based DR is typically 60-80% cheaper than equivalent on-premises solutions.
Tags: business-continuity, disaster-recovery, draas

**Item 17 [C]**
Question: Compare the use cases for public cloud, private cloud, and hybrid cloud, justifying when each approach is most appropriate for different types of organisations.
Answer: Public cloud suits startups and SMEs needing rapid scalability without capital investment, organisations with variable workloads, and applications with no specific data residency requirements. Private cloud is appropriate for government agencies, healthcare organisations, and financial institutions handling sensitive data with strict compliance requirements that mandate complete control over infrastructure. Hybrid cloud serves large organisations transitioning to cloud gradually, those with mixed sensitive and non-sensitive workloads, or those requiring on-premises high-performance computing with cloud burst capacity. The choice depends on factors including budget, security requirements, regulatory constraints, and technical expertise.
Difficulty: C
Topic: 7.4
Explanation: Many organisations adopt a "lift-and-shift" approach to migrate to public cloud initially, then optimise workloads over time. The trend is toward multi-cloud strategies using services from multiple providers to avoid vendor lock-in.
Tags: public-cloud, private-cloud, hybrid-cloud, use-cases

**Item 18 [C]**
Question: Critically evaluate cloud computing's environmental impact, considering both positive and negative effects on sustainability.
Answer: Cloud computing offers positive environmental impacts through resource sharing and optimisation. Large cloud providers achieve utilisation rates of 50-65% compared to 5-15% for enterprise data centres, significantly reducing energy consumption per computation. They also invest heavily in renewable energy and advanced cooling technologies. However, the concentration of data centres increases energy demand, contributes to carbon emissions, and raises concerns about water consumption for cooling. Electronic waste from regular hardware refresh cycles and the energy consumed by data transmission networks add to the environmental burden. Responsible cloud strategies should include workload optimisation, selecting providers with strong sustainability commitments, and implementing data retention policies to minimise unnecessary storage.
Difficulty: C
Topic: 7.4
Explanation: Major cloud providers have committed to carbon neutrality and 100% renewable energy usage, but their actual progress varies and the overall growth in cloud computing may offset efficiency gains.
Tags: sustainability, environmental-impact, cloud-computing
