# Service Level Agreement

**Agreement Number:** HP-SLA-2024-0189  
**Effective Date:** January 1, 2024  
**Parties:**  
- **Service Provider:** HostPro Managed Services LLC, 4400 Data Center Way, Ashburn, VA 20147  
- **Customer:** RetailMax Corporation, 7700 Commerce Street, Dallas, TX 75201  

**This SLA is an Exhibit to the Managed Services Agreement dated November 15, 2023 (Agreement No. HP-MSA-2023-1142).**

---

## 1. Service Description

1.1 This SLA covers the following managed services provided by HostPro to Customer (collectively, the "Services"): (a) dedicated server hosting and management; (b) database administration (MySQL, PostgreSQL); (c) network infrastructure management; (d) backup and disaster recovery; and (e) 24/7 monitoring and incident response.

1.2 The Services are provided for Customer's e-commerce platform and associated internal applications as described in the Service Schedule.

---

## 2. Availability Commitments

2.1 **Production Environment Availability.** HostPro shall maintain a monthly uptime percentage of at least 99.95% for Customer's production environment, measured as: ((Total Minutes in Month - Downtime Minutes) / Total Minutes in Month) × 100.

2.2 **Staging Environment Availability.** HostPro shall maintain a monthly uptime percentage of at least 99.5% for Customer's staging environment.

2.3 **Network Availability.** HostPro shall maintain network availability of at least 99.99% as measured at the edge of HostPro's network.

2.4 **Excluded Downtime.** The following shall not count as Downtime for purposes of uptime calculations: (a) scheduled maintenance as defined in Section 3; (b) downtime caused by Customer's applications, configurations, or actions; (c) force majeure events; (d) downtime caused by third-party services outside HostPro's control; and (e) DNS propagation delays.

---

## 3. Maintenance Windows

3.1 **Scheduled Maintenance.** HostPro shall perform routine maintenance during the following windows: Tuesdays and Thursdays, 2:00 AM to 6:00 AM Central Time. Customer shall be notified at least seventy-two (72) hours in advance of any scheduled maintenance.

3.2 **Emergency Maintenance.** HostPro may perform emergency maintenance outside scheduled windows when necessary to address critical security vulnerabilities or system stability issues. HostPro shall notify Customer as far in advance as practicable and shall minimize the duration and impact of emergency maintenance.

3.3 Scheduled maintenance shall not exceed eight (8) hours per month in aggregate. Any maintenance exceeding this threshold shall count against uptime commitments.

---

## 4. Incident Response and Resolution

4.1 HostPro shall classify and respond to incidents according to the following severity levels:

| Severity | Definition | Response Time | Resolution Target |
|----------|-----------|---------------|-------------------|
| P1 - Critical | Production system completely unavailable; significant revenue impact | 15 minutes | 2 hours |
| P2 - High | Major functionality degraded; workaround not available | 30 minutes | 4 hours |
| P3 - Medium | Partial functionality impaired; workaround available | 2 hours | 8 business hours |
| P4 - Low | Minor issue; no significant business impact | 4 business hours | 5 business days |

4.2 **Response Time** means the elapsed time between HostPro's receipt of the incident report and the initial acknowledgment and assignment to a qualified engineer.

4.3 **Resolution Target** means the target elapsed time between incident report and either resolution or implementation of a suitable workaround. Resolution Targets are best-effort goals, not guarantees.

4.4 HostPro shall provide real-time incident status updates to Customer through the HostPro Status Portal and via email notifications to designated Customer contacts.

---

## 5. Service Credits

5.1 If HostPro fails to meet the availability commitments in Section 2, Customer shall be entitled to service credits as follows:

| Monthly Uptime Percentage | Service Credit (% of Monthly Fee) |
|---------------------------|-----------------------------------|
| 99.00% - 99.94% | 10% |
| 95.00% - 98.99% | 25% |
| 90.00% - 94.99% | 50% |
| Below 90.00% | 100% |

5.2 Service credits shall be applied to the next monthly invoice. Service credits are Customer's sole and exclusive remedy for HostPro's failure to meet availability commitments.

5.3 Customer must request service credits in writing within thirty (30) days of the end of the month in which the availability failure occurred. HostPro shall validate the request within ten (10) business days.

5.4 Total service credits in any calendar month shall not exceed one hundred percent (100%) of the monthly service fee for the affected Services.

---

## 6. Monitoring and Reporting

6.1 HostPro shall provide 24/7/365 monitoring of Customer's infrastructure, including: (a) server health (CPU, memory, disk, network); (b) application availability via HTTP/HTTPS health checks; (c) database performance and replication status; (d) security event monitoring; and (e) backup job status.

6.2 HostPro shall provide Customer with a monthly service report within ten (10) business days of the end of each month, including: (a) uptime and availability statistics; (b) incident summary and resolution details; (c) capacity utilization trends; (d) security event summary; and (e) recommendations for optimization.

6.3 Customer shall have access to a real-time monitoring dashboard showing current system status and performance metrics.

---

## 7. Backup and Disaster Recovery

7.1 HostPro shall perform daily incremental backups and weekly full backups of Customer's data and system configurations. Backups shall be retained for thirty (30) days.

7.2 Backups shall be stored in a geographically separate data center facility at least one hundred (100) miles from the primary data center.

7.3 HostPro shall test backup restoration procedures quarterly and provide Customer with test results.

7.4 In the event of a disaster, HostPro shall initiate failover to the disaster recovery environment within the following targets: (a) Recovery Time Objective (RTO): four (4) hours; (b) Recovery Point Objective (RPO): one (1) hour.

---

## 8. Security

8.1 HostPro shall implement and maintain the following security measures: (a) network firewalls and intrusion detection/prevention systems; (b) DDoS mitigation; (c) encryption of data in transit (TLS 1.2 or higher) and at rest (AES-256); (d) multi-factor authentication for administrative access; (e) regular vulnerability scanning and patching; and (f) SOC 2 Type II compliance.

8.2 HostPro shall notify Customer of any security incident affecting Customer's data or systems within two (2) hours of detection.

8.3 HostPro shall apply critical security patches within twenty-four (24) hours of release. Non-critical patches shall be applied within the next scheduled maintenance window.

---

## 9. Escalation Procedures

9.1 If an incident is not resolved within the Resolution Target, Customer may escalate through the following chain:

| Escalation Level | Contact | Trigger |
|-----------------|---------|---------|
| Level 1 | On-call Engineer | Initial report |
| Level 2 | Team Lead | Resolution Target exceeded |
| Level 3 | Service Delivery Manager | 2× Resolution Target |
| Level 4 | VP of Operations | 4× Resolution Target |

9.2 HostPro shall provide Customer with current escalation contact information and update it within two (2) business days of any personnel change.

---

## 10. SLA Review

10.1 The parties shall review this SLA annually and may propose modifications. Any changes to SLA terms shall be mutually agreed in writing.

10.2 HostPro shall conduct a quarterly business review with Customer to discuss service performance, capacity planning, and upcoming changes.

---

**IN WITNESS WHEREOF**, the parties have executed this SLA as of the Effective Date.

**HostPro Managed Services LLC**  
By: ________________________________  
Name: Thomas Wright  
Title: Director of Service Delivery  

**RetailMax Corporation**  
By: ________________________________  
Name: Angela Kim  
Title: VP of Technology  
